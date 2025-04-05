from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.services.message_service import MessageService
from app.schemas.message import ChatHistoryParams, MessageCreate, MessageResponse, ChatHistoryResponse
from app.core.security import get_current_user

router = APIRouter()

@router.get("/{chat_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    chat_id: UUID,
    params: ChatHistoryParams = Depends(),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение истории сообщений в чате"""
    service = MessageService(db)
    result = await service.get_chat_history(
        chat_id=chat_id,
        user_id=current_user.id,
        limit=params.limit,
        offset=params.offset
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.post("/messages", response_model=MessageResponse)
async def create_message(
    message: MessageCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отправка нового сообщения"""
    service = MessageService(db)
    result = await service.create_message(
        sender_id=current_user.id,
        message_data=message
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.post("/messages/{message_id}/read")
async def mark_message_as_read(
    message_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Пометить сообщение как прочитанное"""
    service = MessageService(db)
    result = await service.mark_message_as_read(
        message_id=message_id,
        user_id=current_user.id
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result 