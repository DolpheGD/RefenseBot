from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, ForeignKey, UniqueConstraint, Boolean
from datetime import datetime, timezone

class Base(DeclarativeBase):
    pass


class Guild(Base):
    __tablename__ = "guilds"

    id: Mapped[int] = mapped_column(primary_key=True)

    discord_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)

    allow_votes: Mapped[bool] = mapped_column(Boolean, default=False)

    users = relationship(
        "UserProfile",
        back_populates="guild",
        cascade="all, delete-orphan"
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    __table_args__ = (
        UniqueConstraint(
            "guild_id",
            "discord_id",
            name="uq_guild_user"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[int] = mapped_column(ForeignKey("guilds.id"))
    discord_id: Mapped[str] = mapped_column(String)

    username: Mapped[str] = mapped_column(String, default="")
    display_name: Mapped[str] = mapped_column(String, default="")
    avatar_url: Mapped[str] = mapped_column(String, default="")

    danger_score: Mapped[float] = mapped_column(Float, default=0.0)

    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    votes: Mapped[int] = mapped_column(default=0)

    votes_used: Mapped[int] = mapped_column(default=0)

    last_voted: Mapped[datetime] = mapped_column()

    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))

    guild = relationship(
        "Guild",
        back_populates="users"
    )

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
    scam_score: Mapped[float] = mapped_column(Float)

    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    user = relationship(
        "UserProfile",
        back_populates="messages"
    )