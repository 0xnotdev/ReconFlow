from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.services import stripe_service
from app.config import settings
from pydantic import BaseModel

router = APIRouter(prefix='/stripe', tags=['stripe'])

class StripeOAuthRequest(BaseModel):
    code: str

@router.get('/connect-url')
def get_stripe_connect_url(current_user: User = Depends(get_current_user)):
    url = (
        f'https://connect.stripe.com/oauth/authorize'
        f'?response_type=code'
        f'&client_id={settings.STRIPE_CLIENT_ID}'
        f'&scope=read_only'
    )
    return {'url': url}

@router.post('/callback')
async def stripe_callback(
    body: StripeOAuthRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = await stripe_service.exchange_stripe_code(body.code)
    if 'error' in result:
        raise HTTPException(400, result['error_description'])
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    org.stripe_access_token = result['access_token']
    org.stripe_account_id = result['stripe_user_id']
    db.commit()
    background_tasks.add_task(
        stripe_service.import_stripe_transactions,
        str(org.id), result['access_token'], db
    )
    return {'message': 'Stripe connected, importing transactions in background'}

@router.post('/upload-csv')
async def upload_stripe_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, 'Only CSV files accepted')
    content = await file.read()
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    count = stripe_service.parse_stripe_csv(content, str(org.id), db)
    return {'imported': count}
