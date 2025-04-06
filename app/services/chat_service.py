from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import ChatRepository, UserRepository, MessageRepository
from app.schemas.chat import ChatCreate, GroupChatCreate

class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ChatRepository(db)
        self.user_repository = UserRepository(db)
        self.message_repository = MessageRepository(db)
    
    async def create_personal_chat(self, user_id: UUID, chat_data: ChatCreate) -> Dict[str, Any]:
        # Проверяем, что все пользователи существуют
        member_ids = list(set([user_id] + chat_data.member_ids))
        for member_id in member_ids:
            user = await self.user_repository.get_by_id(member_id)
            if not user:
                return {"error": f"Пользователь с ID {member_id} не найден"}
        
        # Создаем личный чат
        chat = await self.repository.create_personal_chat(member_ids, chat_data.name)
        
        return {
            "id": chat.id,
            "name": chat.name,
            "type": chat.type.value,
            "members": [{"id": member.id, "name": member.name, "email": member.email} for member in chat.members]
        }
    
    async def create_group_chat(self, creator_id: UUID, chat_data: GroupChatCreate) -> Dict[str, Any]:
        # Проверяем, что создатель существует
        creator = await self.user_repository.get_by_id(creator_id)
        if not creator:
            return {"error": "Пользователь-создатель не найден"}
        
        # Проверяем, что все участники существуют
        for member_id in chat_data.member_ids:
            user = await self.user_repository.get_by_id(member_id)
            if not user:
                return {"error": f"Пользователь с ID {member_id} не найден"}
        
        # Создаем групповой чат
        chat = await self.repository.create_group_chat(
            name=chat_data.name,
            creator_id=creator_id,
            member_ids=chat_data.member_ids
        )
        
        return {
            "id": chat.id,
            "name": chat.name,
            "type": chat.type.value,
            "members": [{"id": member.id, "name": member.name, "email": member.email} for member in chat.members]
        }
    
    async def get_user_chats(self, user_id: UUID) -> List[Dict[str, Any]]:
        # Получаем все чаты пользователя
        chats = await self.repository.get_user_chats(user_id)
        
        return [{
            "id": chat.id,
            "name": chat.name,
            "type": chat.type.value,
            "members": [{"id": member.id, "name": member.name, "email": member.email} for member in chat.members]
        } for chat in chats]
    
    async def get_user_chats_with_last_message(self, user_id: UUID) -> List[Dict[str, Any]]:
        # Получаем все чаты пользователя
        chats = await self.repository.get_user_chats(user_id)
        result = []
        
        for chat in chats:
            # Получаем последнее сообщение в чате
            last_message = await self.message_repository.get_last_message(chat.id)
            # Получаем количество непрочитанных сообщений
            unread_count = await self.message_repository.get_unread_count(chat.id, user_id)
            
            chat_data = {
                "id": chat.id,
                "name": chat.name,
                "type": chat.type.value,
                "members": [{"id": member.id, "name": member.name, "email": member.email} for member in chat.members],
                "unread_count": unread_count
            }
            
            if last_message:
                chat_data["last_message"] = {
                    "id": last_message.id,
                    "sender_id": last_message.sender_id,
                    "sender_name": last_message.sender.name,
                    "text": last_message.text,
                    "timestamp": last_message.timestamp,
                    "is_read": last_message.is_read
                }
            
            result.append(chat_data)
            
        return result
    
    async def get_chat_by_id(self, chat_id: UUID, user_id: UUID) -> Optional[Dict[str, Any]]:
        # Получаем чат по ID
        chat = await self.repository.get_chat_by_id(chat_id)
        
        if not chat:
            return None
        
        # Проверяем, что пользователь является участником чата
        if user_id not in [member.id for member in chat.members]:
            return {"error": "У вас нет доступа к этому чату"}
        
        return {
            "id": chat.id,
            "name": chat.name,
            "type": chat.type.value,
            "members": [{"id": member.id, "name": member.name, "email": member.email} for member in chat.members]
        } 