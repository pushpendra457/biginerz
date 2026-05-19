import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import get_settings
from app.models.rep import Rep
from app.models.retailer import Retailer

# Initialize password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if the provided password matches the hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generate the JWT token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    # Sign the token using your secret key from config.py
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def authenticate_user(db: AsyncSession, username: str, password: str):
    """
    Check if the user is a Rep or a Retailer, verify their password, 
    and return their account and role if successful.
    """
    # 1. Try to find the user in the Reps table
    rep_result = await db.execute(select(Rep).where(Rep.rep_id == username))
    rep = rep_result.scalars().first()
    
    if rep and verify_password(password, rep.hashed_password):
        return {"user": rep, "role": "rep", "id": rep.rep_id}

    # 2. If not a Rep, try to find the user in the Retailers table
    retailer_result = await db.execute(select(Retailer).where(Retailer.retailer_id == username))
    retailer = retailer_result.scalars().first()
    
    if retailer and verify_password(password, retailer.hashed_password):
        return {"user": retailer, "role": "retailer", "id": retailer.retailer_id}

    # 3. If neither matched or password was wrong, return None
    return None