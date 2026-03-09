from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, ForeignKey
from datetime import datetime, timezone
from typing import Optional
from app.db.base import Base
from uuid import UUID

class Link(Base):
    __tablename__ = 'links'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    short_code: Mapped[str] = mapped_column(String, unique=True, index=True)
    short_url: Mapped[str] = mapped_column(String, nullable=False)
    original_url: Mapped[str] = mapped_column(String, nullable=False)

    clicks: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
        )
    
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True
        )
    
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
        )
    
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
        )
    
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey('users.id'), nullable=True)

    user = relationship('User')