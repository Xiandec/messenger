import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Boolean, Table, DateTime, TEXT, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

Base = declarative_base()

# Промежуточная таблица для связи many-to-many между пользователями и групповыми чатами
group_members = Table(
    'group_members',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id')),
    Column('group_id', UUID(as_uuid=True), ForeignKey('groups.id'))
)

# Промежуточная таблица для связи many-to-many между пользователями и личными чатами
chat_members = Table(
    'chat_members',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id')),
    Column('chat_id', UUID(as_uuid=True), ForeignKey('chats.id'))
)

class ChatType(PyEnum):
    PERSONAL = "personal"
    GROUP = "group"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    
    # Связи
    messages = relationship("Message", back_populates="sender")
    created_groups = relationship("Group", back_populates="creator")
    group_memberships = relationship("Group", secondary=group_members, back_populates="members")
    chats = relationship(
        "Chat", 
        secondary=chat_members, 
        back_populates="members",
        lazy="selectin"  
    )

class Chat(Base):
    __tablename__ = 'chats'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=True)  # Может быть NULL для личных чатов
    type = Column(Enum(ChatType), nullable=False)
    
    # Связи
    messages = relationship("Message", back_populates="chat")
    members = relationship(
        "User", 
        secondary=chat_members, 
        back_populates="chats",
        lazy="selectin"
    )
    group = relationship("Group", back_populates="chat", uselist=False)

class Group(Base):
    __tablename__ = 'groups'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    chat_id = Column(UUID(as_uuid=True), ForeignKey('chats.id'), unique=True)
    creator_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
    # Связи
    creator = relationship("User", back_populates="created_groups")
    members = relationship(
        "User", 
        secondary=group_members, 
        back_populates="group_memberships",
        lazy="selectin"
    )
    chat = relationship("Chat", back_populates="group")

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey('chats.id'), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    text = Column(TEXT, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    
    # Связи
    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="messages")
    read_by = relationship("MessageRead", back_populates="message")

class MessageRead(Base):
    __tablename__ = 'message_reads'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey('messages.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    read_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Связи
    message = relationship("Message", back_populates="read_by")
    user = relationship("User") 