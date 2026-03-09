from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_session
from app.db.base import Base

class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = 'users'

async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)