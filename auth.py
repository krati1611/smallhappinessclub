from supabase import create_client, Client
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import config

# Initialize Supabase client
supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SUPABASE_JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Get token from cookie
        token = request.cookies.get("access_token")
        if not token:
            raise credentials_exception
            
        # Remove 'Bearer ' prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
            
        # Verify the token with Supabase
        user = supabase.auth.get_user(token)
        if not user:
            raise credentials_exception
            
        # Get profile data
        profile = supabase.table('profiles').select('*').eq('id', user.user.id).single().execute()
        
        return {
            "id": user.user.id,
            "email": user.user.email,
            "first_name": profile.data.get('first_name'),
            "last_name": profile.data.get('last_name'),
            "created_at": profile.data.get('created_at')
        }
    except Exception as e:
        raise credentials_exception

class AuthHandler:
    async def register_user(self, email: str, password: str, first_name: str, last_name: str):
        try:
            # Sign up user using Supabase Auth
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "email_redirect_to": f"{config.SUPABASE_URL}/auth/callback",
                    "data": {
                        "first_name": first_name,
                        "last_name": last_name
                    }
                }
            })
            
            if auth_response.user:
                return {"message": "User registered successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Registration failed"
                )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def login_user(self, email: str, password: str):
        try:
            # Sign in user using Supabase Auth
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )
            
            # Get profile data
            profile = supabase.table('profiles').select('*').eq('id', auth_response.user.id).single().execute()
            
            return {
                "access_token": auth_response.session.access_token,
                "token_type": "bearer",
                "user": {
                    "id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "first_name": profile.data.get('first_name'),
                    "last_name": profile.data.get('last_name'),
                    "created_at": profile.data.get('created_at')
                }
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            ) 