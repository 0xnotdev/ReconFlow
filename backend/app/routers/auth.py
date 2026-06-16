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
    token = create_access_token({'sub': str(user.id)})
    return {'access_token': token, 'token_type': 'bearer'}

@router.post('/token', response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail='Incorrect email or password')
    token = create_access_token({'sub': str(user.id)})
    return {'access_token': token, 'token_type': 'bearer'}
