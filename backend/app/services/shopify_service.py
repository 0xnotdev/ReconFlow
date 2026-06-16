import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.shopify_order import ShopifyOrder
from app.config import settings

async def get_shopify_auth_url(shop_domain: str) -> str:
    scopes = 'read_orders,read_customers,read_payments'
    redirect_uri = settings.SHOPIFY_REDIRECT_URI
    return (
        f'https://{shop_domain}/admin/oauth/authorize'
        f'?client_id={settings.SHOPIFY_API_KEY}'
        f'&scope={scopes}'
        f'&redirect_uri={redirect_uri}'
    )

async def exchange_shopify_code(shop_domain: str, code: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f'https://{shop_domain}/admin/oauth/access_token',
            json={
                'client_id': settings.SHOPIFY_API_KEY,
                'client_secret': settings.SHOPIFY_API_SECRET,
                'code': code,
            }
        )
    return resp.json().get('access_token')

async def import_shopify_orders(
    org_id: str, access_token: str, shop_domain: str,
    db: Session, status: str = 'any'
) -> int:
    headers = {'X-Shopify-Access-Token': access_token}
    imported = 0
    page_info = None
    async with httpx.AsyncClient() as client:
        while True:
            params = {'limit': 250, 'status': status}
            if page_info:
                params = {'limit': 250, 'page_info': page_info}
            resp = await client.get(
                f'https://{shop_domain}/admin/api/2024-01/orders.json',
                headers=headers, params=params
            )
            data = resp.json()
            orders = data.get('orders', [])
            if not orders: break
            for o in orders:
                existing = db.query(ShopifyOrder).filter(
                    ShopifyOrder.shopify_id == str(o['id'])
                ).first()
                if existing: continue
                order = ShopifyOrder(
                    org_id=org_id,
                    shopify_id=str(o['id']),
                    order_number=str(o.get('order_number', '')),
                    total_price=float(o.get('total_price', 0)),
                    subtotal_price=float(o.get('subtotal_price', 0)),
                    total_tax=float(o.get('total_tax', 0)),
                    total_discounts=float(o.get('total_discounts', 0)),
                    financial_status=o.get('financial_status', ''),
                    fulfillment_status=o.get('fulfillment_status', ''),
                    customer_email=o.get('email', ''),
                    customer_name=f"{o.get('customer', {}).get('first_name', '')} {o.get('customer', {}).get('last_name', '')}".strip(),
                    gateway=o.get('gateway', ''),
                    refunded_amount=sum(float(r.get('amount', 0)) for r in o.get('refunds', [])),
                    created_at=datetime.fromisoformat(o['created_at'].replace('Z', '+00:00')),
                    imported_at=datetime.utcnow()
                )
                db.add(order)
                imported += 1
            # Check for next page
            link_header = resp.headers.get('Link', '')
            if 'rel="next"' not in link_header: break
            import re
            match = re.search(r'page_info=([^&>]+).*rel="next"', link_header)
            page_info = match.group(1) if match else None
            if not page_info: break
    db.commit()
    return imported
