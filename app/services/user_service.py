from typing import Optional, Dict, Any
from uuid import UUID
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import UserRepository
from app.core.security import get_password_hash, verify_password, create_access_token
from app.schemas.user import UserCreate, UserLogin, Token

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = UserRepository(db)
    
    async def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        # Проверяем, существует ли пользователь с таким email
        db_user = await self.repository.get_by_email(user_data.email)
        if db_user:
            return {"error": "Пользователь с таким email уже существует"}
        
        # Хешируем пароль
        hashed_password = get_password_hash(user_data.password)
        
        # Создаем пользователя
        user = await self.repository.create(
            name=user_data.name,
            email=user_data.email,
            password=hashed_password
        )
        
        return {"id": user.id, "email": user.email, "name": user.name}
    
    async def authenticate_user(self, login_data: UserLogin) -> Optional[Dict[str, Any]]:
        user = await self.repository.get_by_email(login_data.email)
        
        if not user or not verify_password(login_data.password, user.password):
            return None
        
        # Создаем токен доступа
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(minutes=30)
        )
        
        return {"access_token": access_token, "token_type": "bearer", "user_id": user.id} 