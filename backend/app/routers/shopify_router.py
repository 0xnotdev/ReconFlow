from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.services import shopify_service
import csv
import io
from datetime import datetime
from app.models.shopify_order import ShopifyOrder

router = APIRouter(prefix='/shopify', tags=['shopify'])

@router.post('/upload-csv')
async def upload_shopify_csv(
    file: UploadFile = File(...),
    client_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, 'Only CSV files accepted')
    content = await file.read()
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    
    # Implementing parsing shopify csv as it's missing in service file
    reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
    imported = 0
    for row in reader:
        order_id = row.get('Name', '')
        if not order_id: continue
        existing = db.query(ShopifyOrder).filter(
            ShopifyOrder.shopify_id == order_id
        ).first()
        if existing: continue
        try:
            total = float(row.get('Total', '0').replace(',', '').replace('$', ''))
            created_str = row.get('Created at', '')
            created = datetime.strptime(created_str, '%Y-%m-%d %H:%M:%S %z') if created_str else datetime.utcnow()
        except (ValueError, KeyError):
            continue
        order = ShopifyOrder(
            org_id=org.id,
            client_id=client_id,
            shopify_id=order_id,
            order_number=order_id,
            total_price=total,
            financial_status=row.get('Financial Status', ''),
            customer_email=row.get('Email', ''),
            gateway=row.get('Payment Method', ''),
            created_at=created,
            imported_at=datetime.utcnow()
        )
        db.add(order)
        imported += 1
    db.commit()
    
    return {'imported': imported}
