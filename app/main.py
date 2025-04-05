from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from uuid import UUID
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.db.base import get_db, init_db
from app.services.user_service import UserService
from app.services.chat_service import ChatService
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse
from app.schemas.chat import ChatCreate, GroupChatCreate, ChatResponse
from app.core.security import get_current_user
from app.api import history, websockets

app = FastAPI(title=settings.PROJECT_NAME)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене здесь должны быть указаны конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API роутер
api_router = APIRouter(prefix=settings.API_V1_STR)

# Событие инициализации приложения
@app.on_event("startup")
async def startup_db_client():
    await init_db()

# Auth endpoints
@api_router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Регистрация нового пользователя"""
    service = UserService(db)
    result = await service.create_user(user_data)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@api_router.post("/auth/token", response_model=Token)
async def login_for_access_token(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Получение токена доступа"""
    service = UserService(db)
    
    result = await service.authenticate_user(login_data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return result

# Chat endpoints
@api_router.post("/chats/personal", response_model=ChatResponse)
async def create_personal_chat(
    chat_data: ChatCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание личного чата"""
    service = ChatService(db)
    result = await service.create_personal_chat(
        user_id=current_user.id,
        chat_data=chat_data
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@api_router.post("/chats/group", response_model=ChatResponse)
async def create_group_chat(
    chat_data: GroupChatCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание группового чата"""
    service = ChatService(db)
    result = await service.create_group_chat(
        creator_id=current_user.id,
        chat_data=chat_data
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@api_router.get("/chats", response_model=List[ChatResponse])
async def get_user_chats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка чатов пользователя"""
    service = ChatService(db)
    result = await service.get_user_chats(user_id=current_user.id)
    return result

@api_router.get("/chats/{chat_id}", response_model=ChatResponse)
async def get_chat_by_id(
    chat_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение информации о чате по ID"""
    service = ChatService(db)
    result = await service.get_chat_by_id(chat_id=chat_id, user_id=current_user.id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Чат не найден"
        )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result["error"]
        )
    
    return result

# Подключение API роутеров
api_router.include_router(history.router, prefix="/chats", tags=["messages"])
# WebSocket роутер подключаем напрямую к приложению без префикса api/v1
app.include_router(websockets.router, tags=["websockets"])

# Подключение главного роутера к приложению
app.include_router(api_router)

# Проверочный эндпоинт для WebSocket
@app.get("/ws-info")
def websocket_info():
    """Информация о WebSocket эндпоинтах"""
    return {
        "endpoints": [
            {
                "path": "/ws/{chat_id}",
                "params": ["token"],
                "description": "WebSocket соединение для чата. Токен нужно передавать как query-параметр."
            }
        ]
    } 