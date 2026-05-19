from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import auth_services

router = APIRouter(prefix="/auth", tags=["Authentication"])

# --- Pydantic Schemas ---
class LoginRequest(BaseModel):
    username: str  # e.g., REP_001 or RTL_005
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str

# --- Endpoints ---
@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login_for_access_token(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Unified login endpoint for both Field Reps and Retailers.
    Returns a JWT access token upon successful authentication.
    """
    # Attempt to authenticate the user
    auth_data = await auth_services.authenticate_user(db, payload.username, payload.password)
    
    if not auth_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Generate the JWT Token containing their ID and Role
    access_token = auth_services.create_access_token(
        data={"sub": auth_data["id"], "role": auth_data["role"]}
    )
    
    # Return the payload that Vue 3 will save in localStorage
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": auth_data["role"],
        "user_id": auth_data["id"]
    }