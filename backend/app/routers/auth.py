from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.config import settings
from pydantic import BaseModel
import uuid

router = APIRouter(prefix='/auth', tags=['auth'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    org_name: str

class Token(BaseModel):
    access_token: str
    token_type: str

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get('sub')
        if user_id is None: raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None: raise credentials_exception
    return user

@router.post('/register', response_model=Token)
def register(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail='Email already registered')
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name
    )
    db.add(user)
    db.flush()
    org = Organization(name=data.org_name, owner_id=user.id)
    db.add(org)
    db.commit()

    # Auto-seed sample financial data so the user sees a working dashboard immediately
    try:
        _seed_sample_data(org.id, db)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f'Auto-seed failed for org {org.id}: {e}')

    token = create_access_token({'sub': str(user.id)})
    return {'access_token': token, 'token_type': 'bearer'}


def _seed_sample_data(org_id, db: Session):
    """Seed sample transactions and run reconciliation for a new org."""
    from app.models.stripe_transaction import StripeTransaction
    from app.models.shopify_order import ShopifyOrder
    from app.models.quickbooks_entry import QuickBooksEntry
    from datetime import timedelta

    now = datetime.utcnow()

    def fee(amt):
        return round(amt * 0.029 + 0.30, 2)

    # Reconciled (clean) transactions
    clean = [
        ("Alice Vance", 150.00, 12), ("Bob Miller", 450.00, 10),
        ("Charlie King", 890.00, 8), ("Diana Ross", 1250.00, 6),
        ("Ethan Hunt", 3200.00, 4),
    ]
    for i, (name, amt, days) in enumerate(clean):
        dt = now - timedelta(days=days)
        db.add(StripeTransaction(org_id=org_id, stripe_id=f"ch_rec_{i}", amount=amt, status="succeeded",
            customer_name=name, stripe_fee=fee(amt), net_amount=amt - fee(amt), created_at=dt, imported_at=now))
        db.add(ShopifyOrder(org_id=org_id, shopify_id=f"sh_rec_{i}", order_number=f"100{i}",
            total_price=amt, financial_status="paid", customer_name=name, gateway="stripe", created_at=dt, imported_at=now))
        db.add(QuickBooksEntry(org_id=org_id, qb_id=f"qb_rec_{i}", transaction_type="SalesReceipt",
            amount=amt, customer_name=name, txn_date=dt, imported_at=now))

    # Missing in QB
    db.add(StripeTransaction(org_id=org_id, stripe_id="ch_miss_001", amount=2400.00, status="succeeded",
        customer_name="Sarah Mitchell", stripe_fee=fee(2400), net_amount=2400 - fee(2400),
        created_at=now - timedelta(days=5), imported_at=now))
    db.add(ShopifyOrder(org_id=org_id, shopify_id="sh_miss_001", order_number="10098",
        total_price=2400.00, financial_status="paid", customer_name="Sarah Mitchell",
        gateway="stripe", created_at=now - timedelta(days=5), imported_at=now))

    # Duplicate in QB
    db.add(StripeTransaction(org_id=org_id, stripe_id="ch_dup_001", amount=1850.00, status="succeeded",
        customer_name="James Whitfield", stripe_fee=fee(1850), net_amount=1850 - fee(1850),
        created_at=now - timedelta(days=15), imported_at=now))
    db.add(QuickBooksEntry(org_id=org_id, qb_id="qb_dup_001a", transaction_type="Payment",
        amount=1850.00, customer_name="James Whitfield", txn_date=now - timedelta(days=15), imported_at=now))
    db.add(QuickBooksEntry(org_id=org_id, qb_id="qb_dup_001b", transaction_type="Payment",
        amount=1850.00, customer_name="James Whitfield", txn_date=now - timedelta(days=15), imported_at=now))

    # Refund mismatch
    db.add(StripeTransaction(org_id=org_id, stripe_id="ch_ref_001", amount=3200.00, status="refunded",
        customer_name="Elena Rodriguez", refunded=True, refund_amount=3200.00,
        created_at=now - timedelta(days=20), imported_at=now))
    db.add(QuickBooksEntry(org_id=org_id, qb_id="qb_ref_orig", transaction_type="SalesReceipt",
        amount=3200.00, customer_name="Elena Rodriguez", txn_date=now - timedelta(days=20), imported_at=now))

    # Revenue leak
    db.add(ShopifyOrder(org_id=org_id, shopify_id="sh_leak_001", order_number="10105",
        total_price=1200.00, financial_status="paid", customer_name="David Park",
        gateway="stripe", created_at=now - timedelta(days=3), imported_at=now))

    # Chargeback dispute
    db.add(StripeTransaction(org_id=org_id, stripe_id="ch_dis_001", amount=890.00, status="succeeded",
        disputed=True, customer_name="Monica Chen", created_at=now - timedelta(days=2), imported_at=now))
    db.add(QuickBooksEntry(org_id=org_id, qb_id="qb_dis_orig", transaction_type="SalesReceipt",
        amount=890.00, customer_name="Monica Chen", txn_date=now - timedelta(days=2), imported_at=now))

    # Fee variance
    db.add(StripeTransaction(org_id=org_id, stripe_id="ch_fee_001", amount=5000.00, status="succeeded",
        customer_name="Peak Performance Gear", stripe_fee=250.00, net_amount=4750.00,
        created_at=now - timedelta(days=1), imported_at=now))
    db.add(QuickBooksEntry(org_id=org_id, qb_id="qb_fee_orig", transaction_type="SalesReceipt",
        amount=4750.00, customer_name="Peak Performance Gear", txn_date=now - timedelta(days=1), imported_at=now))

    db.commit()

    from app.services.reconciliation_engine import ReconciliationEngine
    engine = ReconciliationEngine(str(org_id), db)
    engine.run()

@router.post('/token', response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail='Incorrect email or password')
    token = create_access_token({'sub': str(user.id)})
    return {'access_token': token, 'token_type': 'bearer'}

@router.get('/me')
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    return {
        'id': str(current_user.id),
        'email': current_user.email,
        'full_name': current_user.full_name,
        'org_name': org.name if org else 'No Organization'
    }
