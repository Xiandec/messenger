from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import get_db
from app.db.repositories import UserRepository
from app.schemas.user import TokenData
from app.core.logging import log_error, log_warning, log_info

# Настройка контекста шифрования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка OAuth2 с проверкой по паролю
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка соответствия пароля хэшу"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Получение хэша пароля"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT токена доступа"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Получение текущего пользователя по токену"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Невозможно проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception
    return user

async def get_user_from_token(
    token: str,
    db: AsyncSession
) -> dict:
    """Получение пользователя по токену для WebSocket соединений"""
    try:
        # Проверяем и декодируем токен
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"verify_signature": True, "verify_exp": True}
        )
        user_id: str = payload.get("sub")
        
        if user_id is None:
            log_warning("Token payload does not contain 'sub' field")
            return None
            
        token_data = TokenData(user_id=user_id)
        
        # Получаем пользователя из базы данных
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(token_data.user_id)
        
        if user is None:
            log_warning(f"User with ID {token_data.user_id} not found in database")
            return None
            
        log_info(f"Successfully authenticated user {user.id} via WebSocket token")
        return user
        
    except JWTError as e:
        log_error(f"JWT token error: {str(e)}")
        return None
    except Exception as e:
        log_error(f"Unexpected error during WebSocket token verification: {str(e)}")
        return None 