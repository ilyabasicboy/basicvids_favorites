from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FavoriteVideo(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("video_id", "user_id", name="uq_favorite_video_user"),)

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    video_id: str = Field(index=True, max_length=100)
    user_id: int = Field(index=True)
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=utc_now,
        nullable=False,
    )


class FavoritePlaylist(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("playlist_id", "user_id", name="uq_favorite_playlist_user"),)

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    playlist_id: str = Field(index=True, max_length=100)
    channel_id: str = Field(index=True, max_length=100)
    user_id: int = Field(index=True)
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=utc_now,
        nullable=False,
    )
