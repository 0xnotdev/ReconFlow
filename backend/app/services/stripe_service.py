import stripe
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.stripe_transaction import StripeTransaction
from app.config import settings
import httpx

stripe.api_key = settings.STRIPE_SECRET_KEY

async def exchange_stripe_code(code: str) -> dict:
    '''Exchange OAuth code for access token'''
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            'https://connect.stripe.com/oauth/token',
            data={
                'client_secret': settings.STRIPE_SECRET_KEY,
                'code': code,
                'grant_type': 'authorization_code',
            }
        )
    return resp.json()

async def import_stripe_transactions(
    org_id: str, access_token: str, db: Session,
    start_date: datetime = None, end_date: datetime = None
) -> int:
    '''Pull all charges from Stripe and store in DB. Returns count.'''
    stripe.api_key = access_token  # use connected account token
    imported = 0
    params = {'limit': 100, 'expand': ['data.balance_transaction']}
    if start_date:
        params['created'] = {'gte': int(start_date.timestamp())}
    if end_date:
        params['created'] = {**params.get('created', {}), 'lte': int(end_date.timestamp())}

    charges = stripe.Charge.list(**params)

    for charge in charges.auto_paging_iter():
        existing = db.query(StripeTransaction).filter(
            StripeTransaction.stripe_id == charge.id
        ).first()
        if existing:
            continue

        bt = charge.balance_transaction
        fee = bt.fee / 100 if bt and hasattr(bt, 'fee') else 0
        net = bt.net / 100 if bt and hasattr(bt, 'net') else 0

        txn = StripeTransaction(
            org_id=org_id,
            stripe_id=charge.id,
            amount=charge.amount / 100,
            currency=charge.currency,
            status=charge.status,
            customer_email=charge.billing_details.email if charge.billing_details else None,
            customer_name=charge.billing_details.name if charge.billing_details else None,
            description=charge.description,
            stripe_fee=fee,
            net_amount=net,
            payment_intent_id=charge.payment_intent,
            charge_id=charge.id,
            refunded=charge.refunded,
            refund_amount=charge.amount_refunded / 100,
            disputed=charge.disputed,
            created_at=datetime.fromtimestamp(charge.created),
            imported_at=datetime.utcnow()
        )
        db.add(txn)
        imported += 1

    db.commit()
    return imported

def parse_stripe_csv(file_content: bytes, org_id: str, client_id: str, db: Session) -> int:
    '''Parse Stripe CSV export. Headers vary by export type.'''
    import csv, io
    reader = csv.DictReader(io.StringIO(file_content.decode('utf-8')))
    imported = 0
    for row in reader:
        charge_id = row.get('id', row.get('charge_id', ''))
        if not charge_id: continue
        existing = db.query(StripeTransaction).filter(
            StripeTransaction.stripe_id == charge_id
        ).first()
        if existing: continue
        try:
            amount = float(row.get('Amount', '0').replace(',', '')) / 100
            fee = float(row.get('Fee', '0').replace(',', '')) / 100
            net = float(row.get('Net', '0').replace(',', '')) / 100
            created = datetime.strptime(row.get('Created (UTC)', ''), '%Y-%m-%d %H:%M:%S')
        except (ValueError, KeyError):
            continue
        txn = StripeTransaction(
            org_id=org_id,
            client_id=client_id,
            stripe_id=charge_id,
            amount=amount,
            currency=row.get('Currency', 'usd'),
            status=row.get('Status', 'unknown'),
            customer_email=row.get('Customer Email', ''),
            stripe_fee=fee,
            net_amount=net,
            refunded=row.get('Refunded', '') == 'true',
            created_at=created,
            imported_at=datetime.utcnow()
        )
        db.add(txn)
        imported += 1
    db.commit()
    return imported
