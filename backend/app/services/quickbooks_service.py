import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.quickbooks_entry import QuickBooksEntry
from app.config import settings
import base64

QB_BASE_URL = 'https://quickbooks.api.intuit.com/v3/company'
QB_SANDBOX_URL = 'https://sandbox-quickbooks.api.intuit.com/v3/company'

def get_auth_header() -> str:
    credentials = f'{settings.QUICKBOOKS_CLIENT_ID}:{settings.QUICKBOOKS_CLIENT_SECRET}'
    return base64.b64encode(credentials.encode()).decode()

async def exchange_qb_code(code: str, realm_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer',
            headers={
                'Authorization': f'Basic {get_auth_header()}',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': settings.QUICKBOOKS_REDIRECT_URI,
            }
        )
    return resp.json()

async def refresh_qb_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer',
            headers={
                'Authorization': f'Basic {get_auth_header()}',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            data={'grant_type': 'refresh_token', 'refresh_token': refresh_token}
        )
    return resp.json()

async def import_qb_transactions(
    org_id: str, access_token: str, realm_id: str, db: Session,
    start_date: str = '2024-01-01', end_date: str = '2024-12-31'
) -> int:
    '''Query using QBO Query API for Payments and Invoices'''
    base = QB_BASE_URL  # change to QB_SANDBOX_URL for testing
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    imported = 0
    # Fetch Payments
    query = f"SELECT * FROM Payment WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}' MAXRESULTS 1000"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f'{base}/{realm_id}/query?query={query}',
            headers=headers
        )
    data = resp.json()
    payments = data.get('QueryResponse', {}).get('Payment', [])
    for p in payments:
        existing = db.query(QuickBooksEntry).filter(
            QuickBooksEntry.qb_id == p['Id']
        ).first()
        if existing: continue
        entry = QuickBooksEntry(
            org_id=org_id,
            qb_id=p['Id'],
            transaction_type='Payment',
            doc_number=p.get('PaymentRefNum', ''),
            amount=float(p.get('TotalAmt', 0)),
            customer_name=p.get('CustomerRef', {}).get('name', ''),
            memo=p.get('PrivateNote', ''),
            payment_ref=p.get('PaymentRefNum', ''),
            txn_date=datetime.strptime(p['TxnDate'], '%Y-%m-%d'),
            imported_at=datetime.utcnow()
        )
        db.add(entry)
        imported += 1
    db.commit()
    return imported

def parse_qb_csv(file_content: bytes, org_id: str, client_id: str, db: Session) -> int:
    '''QuickBooks Transaction List report CSV'''
    import csv, io
    reader = csv.DictReader(io.StringIO(file_content.decode('utf-8')))
    imported = 0
    for row in reader:
        txn_id = row.get('Num', row.get('Transaction ID', ''))
        if not txn_id or not txn_id.strip(): continue
        existing = db.query(QuickBooksEntry).filter(
            QuickBooksEntry.qb_id == txn_id.strip()
        ).first()
        if existing: continue
        try:
            amount_str = row.get('Amount', '0').replace(',', '').replace('$', '')
            amount = float(amount_str) if amount_str else 0
            date_str = row.get('Date', '')
            txn_date = datetime.strptime(date_str, '%m/%d/%Y') if date_str else datetime.utcnow()
        except (ValueError, KeyError):
            continue
        entry = QuickBooksEntry(
            org_id=org_id,
            client_id=client_id,
            qb_id=txn_id.strip(),
            transaction_type=row.get('Transaction Type', 'Payment'),
            doc_number=row.get('Num', ''),
            amount=amount,
            customer_name=row.get('Name', ''),
            memo=row.get('Memo/Description', ''),
            txn_date=txn_date,
            imported_at=datetime.utcnow()
        )
        db.add(entry)
        imported += 1
    db.commit()
    return imported
