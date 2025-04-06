# Messenger

Мессенджер с функционалом обмена сообщениями и создания групповых чатов на базе FastAPI, WebSocket, SQLAlchemy и PostgreSQL.

## Функциональность

- Регистрация и аутентификация пользователей
- Создание личных и групповых чатов
- Отправка и получение сообщений в реальном времени
- Просмотр истории сообщений
- Отметка сообщений как прочитанных
- Уведомления о новых сообщениях через WebSocket

## Технологии

- FastAPI - асинхронный web-фреймворк
- SQLAlchemy - ORM для работы с базой данных
- PostgreSQL - реляционная СУБД
- WebSocket - протокол для обмена сообщениями в реальном времени
- JWT - авторизация пользователей
- Docker - контейнеризация приложения

## Запуск проекта

### С использованием Docker Compose

1. Клонировать репозиторий:
```
git clone https://github.com/Xiandec/messenger.git
cd messenger
```

2. Запустить с помощью Docker Compose:
```
docker-compose up --build
```

3. API будет доступен по адресу http://localhost:8000

## API Endpoints

### Аутентификация

- `POST /api/v1/auth/register` - Регистрация нового пользователя
- `POST /api/v1/auth/token` - Получение JWT токена

### Чаты

- `GET /api/v1/chats` - Получение списка чатов пользователя
- `GET /api/v1/chats/with-last-message` - Получение списка чатов с последними сообщениями
- `GET /api/v1/chats/{chat_id}` - Получение информации о чате
- `POST /api/v1/chats/personal` - Создание личного чата
- `POST /api/v1/chats/group` - Создание группового чата

### Сообщения

- `GET /api/v1/chats/{chat_id}/history` - Получение истории сообщений
- `POST /api/v1/chats/messages` - Отправка нового сообщения
- `POST /api/v1/chats/messages/{message_id}/read` - Пометить сообщение как прочитанное

### WebSockets

- `WebSocket /ws/{chat_id}?token={token}` - Подключение к WebSocket для обмена сообщениями в конкретном чате
- `WebSocket /ws/user?token={token}` - Глобальное подключение для получения уведомлений о новых сообщениях во всех чатах

## Подробная документация API

Полная документация по API доступна в файле [API_DOCUMENTATION.md](./API_DOCUMENTATION.md).

## Структура проекта

```
/messenger
  /app
    /api
      __init__.py
      history.py
      websockets.py
    /core
      __init__.py
      config.py
      security.py
    /db
      __init__.py
      base.py
      models.py
      repositories.py
    /services
      __init__.py
      chat_service.py
      message_service.py
      user_service.py
    /schemas
      __init__.py
      chat.py
      message.py
      user.py
    __init__.py
    main.py
  /tests
    __init__.py
    test_chat.py
    test_history.py
  docker-compose.yml
  Dockerfile
  requirements.txt
  README.md
  API_DOCUMENTATION.md
```

## Особенности авторизации

Система использует JWT токены для авторизации. Срок действия токена - 30 минут. Для доступа к защищенным эндпоинтам необходимо добавить заголовок:

```
Authorization: Bearer {полученный_токен}
```

