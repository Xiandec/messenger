import json
from typing import Dict, List, Any
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.services.message_service import MessageService
from app.services.chat_service import ChatService
from app.schemas.message import MessageCreate

router = APIRouter()

# Хранение активных соединений WebSocket
class ConnectionManager:
    def __init__(self):
        # Словарь для хранения соединений: {user_id: {chat_id: websocket}}
        self.active_connections: Dict[UUID, Dict[UUID, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: UUID, chat_id: UUID):
        # await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        self.active_connections[user_id][chat_id] = websocket

    def disconnect(self, user_id: UUID, chat_id: UUID):
        if user_id in self.active_connections and chat_id in self.active_connections[user_id]:
            del self.active_connections[user_id][chat_id]
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: Dict[str, Any], user_id: UUID, chat_id: UUID):
        if user_id in self.active_connections and chat_id in self.active_connections[user_id]:
            await self.active_connections[user_id][chat_id].send_json(message)

    async def broadcast_to_chat(self, message: Dict[str, Any], chat_id: UUID, skip_user_id: UUID = None):
        for user_id, chats in self.active_connections.items():
            if skip_user_id and user_id == skip_user_id:
                continue
            if chat_id in chats:
                await chats[chat_id].send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: UUID,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    await websocket.accept()
    
    # Аутентификация пользователя по токену
    from app.core.security import get_user_from_token
    
    try:
        user = await get_user_from_token(token=token, db=db)
        if not user:
            await websocket.send_json({"error": "Недействительный токен"})
            await websocket.close(code=1008)
            return
            
        # Проверка доступа к чату
        chat_service = ChatService(db)
        chat_result = await chat_service.get_chat_by_id(chat_id=chat_id, user_id=user.id)
        
        if not chat_result or "error" in chat_result:
            await websocket.send_json({"error": "Чат не найден или доступ запрещен"})
            await websocket.close(code=1008)
            return

        # Отправляем подтверждение успешного подключения
        await websocket.send_json({"status": "connected", "user_id": str(user.id), "chat_id": str(chat_id)})
        
        # Регистрируем соединение в менеджере
        await manager.connect(websocket, user.id, chat_id)
        
        try:
            while True:
                # Получение сообщения от клиента
                data = await websocket.receive_text()
                message_data_text = json.loads(data)
                
                # Создание сообщения в базе данных
                message_service = MessageService(db)
                result = await message_service.create_message(
                    sender_id=user.id,
                    message_data=MessageCreate(
                        chat_id = chat_id,
                        text = message_data_text.get("text", "")
                    )
                )
                
                if "error" in result:
                    await manager.send_personal_message(
                        {"error": result["error"]},
                        user.id,
                        chat_id
                    )
                    continue
                
                # Отправка сообщения всем участникам чата
                await manager.broadcast_to_chat(
                    {
                        "type": "message",
                        "data": {
                            "id": str(result["id"]),
                            "sender_id": str(result["sender_id"]),
                            "sender_name": user.name,
                            "text": result["text"],
                            "timestamp": str(result["timestamp"]),
                            "is_read": result["is_read"]
                        }
                    },
                    chat_id
                )
        except WebSocketDisconnect:
            manager.disconnect(user.id, chat_id)
        except Exception as e:
            print(f"WebSocket error: {str(e)}")
            await websocket.send_json({"error": str(e)})
            manager.disconnect(user.id, chat_id)
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        await websocket.send_json({"error": "Ошибка аутентификации"})
        await websocket.close(code=1008) 