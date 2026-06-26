from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey
from datetime import datetime

class Base(DeclarativeBase):
    pass


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[str] = mapped_column(String, unique=True, index=True)

    danger_score: Mapped[float] = mapped_column(Float, default=0.0)

    total_messages: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


    messages = relationship(
        "DangerMessage",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class DangerMessage(Base):
    __tablename__ = "danger_messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id")
    )

    message_id: Mapped[str] = mapped_column(String, unique=True)
    content: Mapped[str] = mapped_column(String)

    danger_score: Mapped[float] = mapped_column(Float)

    sexual_score: Mapped[float] = mapped_column(Float)
    hate_score: Mapped[float] = mapped_column(Float)
    concern_score: Mapped[float] = mapped_column(Float)

    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    user = relationship(
        "UserProfile",
        back_populates="messages"
    )