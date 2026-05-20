from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field as PydanticField


class FavoritePlaylistCreate(BaseModel):
    channel_id: str = PydanticField(min_length=1, max_length=100)


class FavoriteVideoPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    video_id: str
    user_id: int
    created_at: datetime


class FavoritePlaylistPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    playlist_id: str
    channel_id: str
    user_id: int
    created_at: datetime


class FavoriteVideoList(BaseModel):
    items: list[FavoriteVideoPublic]
    count: int


class FavoritePlaylistList(BaseModel):
    items: list[FavoritePlaylistPublic]
    count: int


class FavoriteStatus(BaseModel):
    is_favorite: bool


class FavoriteVideosStatusRequest(BaseModel):
    video_ids: list[str] = PydanticField(default_factory=list, max_length=200)


class FavoriteVideosStatusResponse(BaseModel):
    favorites: dict[str, bool]


class FavoritePlaylistsStatusRequest(BaseModel):
    playlist_ids: list[str] = PydanticField(default_factory=list, max_length=200)


class FavoritePlaylistsStatusResponse(BaseModel):
    favorites: dict[str, bool]


class FavoriteDeleteResponse(BaseModel):
    message: str
