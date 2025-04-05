from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import MessageRepository, ChatRepository
from app.schemas.message import MessageCreate

class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = MessageRepository(db)
        self.chat_repository = ChatRepository(db)
    
    async def create_message(self, sender_id: UUID, message_data: MessageCreate) -> Dict[str, Any]:
        # Проверяем, существует ли чат
        chat = await self.chat_repository.get_chat_by_id(message_data.chat_id)
        if not chat:
            return {"error": "Чат не найден"}
        
        # Проверяем, является ли отправитель участником чата
        if sender_id not in [member.id for member in chat.members]:
            return {"error": "Вы не являетесь участником этого чата"}
        
        # Создаем сообщение
        message = await self.repository.create(
            chat_id=message_data.chat_id,
            sender_id=sender_id,
            text=message_data.text
        )
        
        # Получаем данные отправителя
        sender = None
        for member in chat.members:
            if member.id == sender_id:
                sender = member
                break
        
        return {
            "id": message.id,
            "chat_id": message.chat_id,
            "sender_id": message.sender_id,
            "sender": {
                "id": sender.id,
                "name": sender.name,
                "email": sender.email
            },
            "text": message.text,
            "timestamp": message.timestamp,
            "is_read": message.is_read
        }
    
    async def get_chat_history(self, chat_id: UUID, user_id: UUID, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        # Проверяем, существует ли чат
        chat = await self.chat_repository.get_chat_by_id(chat_id)
        if not chat:
            return {"error": "Чат не найден"}
        
        # Проверяем, является ли пользователь участником чата
        if user_id not in [member.id for member in chat.members]:
            return {"error": "Вы не являетесь участником этого чата"}
        
        # Получаем историю сообщений
        messages = await self.repository.get_chat_history(chat_id, limit, offset)
        
        # Помечаем сообщения как прочитанные
        for message in messages:
            if message.sender_id != user_id and not message.is_read:
                await self.repository.mark_as_read(message.id, user_id)
        
        return {
            "messages": [
                {
                    "id": message.id,
                    "chat_id": message.chat_id,
                    "sender_id": message.sender_id,
                    "sender": {
                        "id": message.sender.id,
                        "name": message.sender.name,
                        "email": message.sender.email
                    },
                    "text": message.text,
                    "timestamp": message.timestamp,
                    "is_read": message.is_read
                }
                for message in messages
            ],
            "total": len(messages)
        }
    
    async def mark_message_as_read(self, message_id: UUID, user_id: UUID) -> Dict[str, Any]:
        # Проверяем, существует ли сообщение
        message = await self.repository.get_by_id(message_id)
        if not message:
            return {"error": "Сообщение не найдено"}
        
        # Проверяем, является ли пользователь участником чата
        chat = await self.chat_repository.get_chat_by_id(message.chat_id)
        if not chat:
            return {"error": "Чат не найден"}
        
        if user_id not in [member.id for member in chat.members]:
            return {"error": "Вы не являетесь участником этого чата"}
        
        # Если пользователь - отправитель сообщения, то оно уже считается прочитанным
        if message.sender_id == user_id:
            return {"message": "Это ваше сообщение, оно уже считается прочитанным"}
        
        # Помечаем сообщение как прочитанное
        message_read = await self.repository.mark_as_read(message_id, user_id)
        
        return {
            "message_id": message_read.message_id,
            "user_id": message_read.user_id,
            "read_at": message_read.read_at
        } 