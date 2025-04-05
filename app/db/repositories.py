from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, update, and_, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import User, Chat, Message, Group, MessageRead, ChatType, chat_members, group_members

class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

class UserRepository(BaseRepository):
    async def create(self, name: str, email: str, password: str) -> User:
        user = User(name=name, email=email, password=password)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalars().first()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().first()

class ChatRepository(BaseRepository):
    async def create_personal_chat(self, user_ids: List[UUID], name: Optional[str] = None) -> Chat:
        # Создание чата
        chat = Chat(name=name, type=ChatType.PERSONAL)
        self.db.add(chat)
        await self.db.flush()
        
        # Добавление связей между чатом и пользователями напрямую в промежуточную таблицу
        for user_id in user_ids:
            await self.db.execute(
                chat_members.insert().values(
                    chat_id=chat.id,
                    user_id=user_id
                )
            )
        
        await self.db.commit()
        
        # Загружаем чат с участниками
        result = await self.db.execute(
            select(Chat)
            .options(selectinload(Chat.members))
            .where(Chat.id == chat.id)
        )
        return result.scalars().first()
    
    async def create_group_chat(self, name: str, creator_id: UUID, member_ids: List[UUID]) -> Chat:
        # Создание чата
        chat = Chat(name=name, type=ChatType.GROUP)
        self.db.add(chat)
        await self.db.flush()
        
        # Создание группы
        group = Group(name=name, chat_id=chat.id, creator_id=creator_id)
        self.db.add(group)
        await self.db.flush()
        
        # Добавление связей между чатом и пользователями напрямую в промежуточную таблицу
        all_user_ids = set([creator_id] + member_ids)
        for user_id in all_user_ids:
            # Добавляем пользователя в чат
            await self.db.execute(
                chat_members.insert().values(
                    chat_id=chat.id,
                    user_id=user_id
                )
            )
            
            # Добавляем пользователя в группу
            await self.db.execute(
                group_members.insert().values(
                    group_id=group.id,
                    user_id=user_id
                )
            )
        
        await self.db.commit()
        
        # Загружаем чат с участниками
        result = await self.db.execute(
            select(Chat)
            .options(selectinload(Chat.members))
            .options(selectinload(Chat.group))
            .where(Chat.id == chat.id)
        )
        return result.scalars().first()
    
    async def get_chat_by_id(self, chat_id: UUID) -> Optional[Chat]:
        result = await self.db.execute(
            select(Chat)
            .options(selectinload(Chat.members))
            .where(Chat.id == chat_id)
        )
        return result.scalars().first()
    
    async def get_user_chats(self, user_id: UUID) -> List[Chat]:
        result = await self.db.execute(
            select(Chat)
            .join(Chat.members)
            .where(User.id == user_id)
            .options(selectinload(Chat.members))
        )
        return result.scalars().all()

class MessageRepository(BaseRepository):
    async def create(self, chat_id: UUID, sender_id: UUID, text: str) -> Message:
        message = Message(chat_id=chat_id, sender_id=sender_id, text=text)
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message
    
    async def get_by_id(self, message_id: UUID) -> Optional[Message]:
        result = await self.db.execute(
            select(Message).where(Message.id == message_id)
        )
        return result.scalars().first()
    
    async def get_chat_history(self, chat_id: UUID, limit: int = 100, offset: int = 0) -> List[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.timestamp)
            .options(selectinload(Message.sender))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    async def mark_as_read(self, message_id: UUID, user_id: UUID) -> MessageRead:
        message_read = MessageRead(message_id=message_id, user_id=user_id)
        self.db.add(message_read)
        
        # Проверка, прочитали ли все участники чата сообщение
        message = await self.get_by_id(message_id)
        
        if message:
            chat = await self.db.execute(
                select(Chat)
                .options(selectinload(Chat.members))
                .where(Chat.id == message.chat_id)
            )
            chat = chat.scalars().first()
            
            if chat:
                # Получаем всех, кто прочитал сообщение
                read_by_result = await self.db.execute(
                    select(MessageRead.user_id)
                    .where(MessageRead.message_id == message_id)
                )
                read_by_user_ids = [r for r in read_by_result.scalars().all()]
                
                # Проверяем, все ли участники чата прочитали сообщение
                all_read = all(user.id in read_by_user_ids for user in chat.members if user.id != message.sender_id)
                
                if all_read:
                    await self.db.execute(
                        update(Message)
                        .where(Message.id == message_id)
                        .values(is_read=True)
                    )
        
        await self.db.commit()
        await self.db.refresh(message_read)
        return message_read 