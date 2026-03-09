import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, models
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy

from fastapi_users.db import SQLAlchemyUserDatabase
from app.auth.db import User, get_user_db

SECRET = 'SECRET'

# менеджер пользователей, который помогает обрабатывать регистрацию, восстановление пароля и верификацию
class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    # принтим после фактических событий, но можно отправлять пуши и тд
    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f'Пользователь {user.id} зарегистрирован')

    async def on_after_forgot_password(self, user: User, token: str, request: Optional[Request] = None):
        print(f'Пользователь {user.id} отправил запрос на восстановление пароля. Токен: {token}')

    async def on_after_request_verify(self, user: User, token: str, request: Optional[Request] = None):
        print(f'Пользователь {user.id} отправил запрос на верификацию. Токен: {token}')

async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)

bearer_transport = BearerTransport(tokenUrl='/auth/login')

# для проверки токена, который придет в запросе
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name='jwt',
    transport=bearer_transport,
    get_strategy=get_jwt_strategy
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
current_user = fastapi_users.current_user()