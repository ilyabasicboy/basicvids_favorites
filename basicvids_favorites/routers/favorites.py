from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session, col, delete, select

from basicvids_favorites.auth import CurrentUser, get_current_user
from basicvids_favorites.db import get_session
from basicvids_favorites.models.favorites import (
    FavoriteDeleteResponse,
    FavoritePlaylistCreate,
    FavoritePlaylistList,
    FavoritePlaylistPublic,
    FavoritePlaylistsStatusRequest,
    FavoritePlaylistsStatusResponse,
    FavoriteStatus,
    FavoriteVideoList,
    FavoriteVideoPublic,
    FavoriteVideosStatusRequest,
    FavoriteVideosStatusResponse,
)
from basicvids_favorites.rate_limit import client_identifier, enforce_rate_limit
from basicvids_favorites.schemas.favorites import FavoritePlaylist, FavoriteVideo


router = APIRouter(tags=["Favorites"], prefix="/favorites")


def get_favorite_video(session: Session, video_id: str, user_id: int) -> FavoriteVideo | None:
    return session.exec(
        select(FavoriteVideo).where(
            FavoriteVideo.video_id == video_id,
            FavoriteVideo.user_id == user_id,
        )
    ).first()


def get_favorite_playlist(session: Session, playlist_id: str, user_id: int) -> FavoritePlaylist | None:
    return session.exec(
        select(FavoritePlaylist).where(
            FavoritePlaylist.playlist_id == playlist_id,
            FavoritePlaylist.user_id == user_id,
        )
    ).first()


@router.put("/videos/{video_id}", response_model=FavoriteVideoPublic, status_code=201)
async def add_favorite_video(
    video_id: str,
    request: Request,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> FavoriteVideo:
    await enforce_rate_limit("add_favorite_video_ip", client_identifier(request), 120, 60)
    await enforce_rate_limit("add_favorite_video_user", f"user:{current_user.id}", 120, 60)

    favorite = get_favorite_video(session, video_id, current_user.id)
    if favorite:
        return favorite

    favorite = FavoriteVideo(video_id=video_id, user_id=current_user.id)
    session.add(favorite)
    session.commit()
    session.refresh(favorite)
    return favorite


@router.get("/videos/", response_model=FavoriteVideoList)
async def list_favorite_videos(
    offset: int = 0,
    limit: int = Query(default=20, le=100),
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> FavoriteVideoList:
    statement = (
        select(FavoriteVideo)
        .where(FavoriteVideo.user_id == current_user.id)
        .order_by(col(FavoriteVideo.created_at).desc())
        .offset(offset)
        .limit(limit)
    )
    items = session.exec(statement).all()
    return FavoriteVideoList(
        items=[FavoriteVideoPublic.model_validate(item) for item in items],
        count=len(items),
    )


@router.get("/videos/{video_id}", response_model=FavoriteStatus)
async def get_favorite_video_status(
    video_id: str,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> FavoriteStatus:
    return FavoriteStatus(is_favorite=get_favorite_video(session, video_id, current_user.id) is not None)


@router.post("/videos/statuses", response_model=FavoriteVideosStatusResponse)
async def get_favorite_video_statuses(
    data: FavoriteVideosStatusRequest,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> FavoriteVideosStatusResponse:
    video_ids = list(dict.fromkeys(data.video_ids))
    if not video_ids:
        return FavoriteVideosStatusResponse(favorites={})

    favorites = session.exec(
        select(FavoriteVideo.video_id).where(
            FavoriteVideo.user_id == current_user.id,
            col(FavoriteVideo.video_id).in_(video_ids),
        )
    ).all()
    favorite_set = set(favorites)
    return FavoriteVideosStatusResponse(favorites={video_id: video_id in favorite_set for video_id in video_ids})


@router.delete("/videos/{video_id}", response_model=FavoriteDeleteResponse)
async def delete_favorite_video(
    video_id: str,
    request: Request,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> FavoriteDeleteResponse:
    await enforce_rate_limit("delete_favorite_video_user", f"user:{current_user.id}", 120, 60)
    favorite = get_favorite_video(session, video_id, current_user.id)
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite video not found")

    session.delete(favorite)
    session.commit()
    return FavoriteDeleteResponse(message="Favorite video deleted successfully")


@router.delete("/videos/", response_model=FavoriteDeleteResponse)
async def clear_favorite_videos(
    request: Request,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> FavoriteDeleteResponse:
    await enforce_rate_limit("clear_favorite_videos_user", f"user:{current_user.id}", 10, 60)
    session.exec(delete(FavoriteVideo).where(FavoriteVideo.user_id == current_user.id))
    session.commit()
    return FavoriteDeleteResponse(message="Favorite videos cleared successfully")


@router.put("/playlists/{playlist_id}", response_model=FavoritePlaylistPublic, status_code=201)
async def add_favorite_playlist(
    playlist_id: str,
    data: FavoritePlaylistCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> FavoritePlaylist:
    await enforce_rate_limit("add_favorite_playlist_ip", client_identifier(request), 120, 60)
    await enforce_rate_limit("add_favorite_playlist_user", f"user:{current_user.id}", 120, 60)

    favorite = get_favorite_playlist(session, playlist_id, current_user.id)
    if favorite:
        favorite.channel_id = data.channel_id
        session.add(favorite)
        session.commit()
        session.refresh(favorite)
        return favorite

    favorite = FavoritePlaylist(playlist_id=playlist_id, channel_id=data.channel_id, user_id=current_user.id)
    session.add(favorite)
    session.commit()
    session.refresh(favorite)
    return favorite


@router.get("/playlists/", response_model=FavoritePlaylistList)
async def list_favorite_playlists(
    offset: int = 0,
    limit: int = Query(default=20, le=100),
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> FavoritePlaylistList:
    statement = (
        select(FavoritePlaylist)
        .where(FavoritePlaylist.user_id == current_user.id)
        .order_by(col(FavoritePlaylist.created_at).desc())
        .offset(offset)
        .limit(limit)
    )
    items = session.exec(statement).all()
    return FavoritePlaylistList(
        items=[FavoritePlaylistPublic.model_validate(item) for item in items],
        count=len(items),
    )


@router.get("/playlists/{playlist_id}", response_model=FavoriteStatus)
async def get_favorite_playlist_status(
    playlist_id: str,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> FavoriteStatus:
    return FavoriteStatus(is_favorite=get_favorite_playlist(session, playlist_id, current_user.id) is not None)


@router.post("/playlists/statuses", response_model=FavoritePlaylistsStatusResponse)
async def get_favorite_playlist_statuses(
    data: FavoritePlaylistsStatusRequest,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> FavoritePlaylistsStatusResponse:
    playlist_ids = list(dict.fromkeys(data.playlist_ids))
    if not playlist_ids:
        return FavoritePlaylistsStatusResponse(favorites={})

    favorites = session.exec(
        select(FavoritePlaylist.playlist_id).where(
            FavoritePlaylist.user_id == current_user.id,
            col(FavoritePlaylist.playlist_id).in_(playlist_ids),
        )
    ).all()
    favorite_set = set(favorites)
    return FavoritePlaylistsStatusResponse(
        favorites={playlist_id: playlist_id in favorite_set for playlist_id in playlist_ids},
    )


@router.delete("/playlists/{playlist_id}", response_model=FavoriteDeleteResponse)
async def delete_favorite_playlist(
    playlist_id: str,
    request: Request,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> FavoriteDeleteResponse:
    await enforce_rate_limit("delete_favorite_playlist_user", f"user:{current_user.id}", 120, 60)
    favorite = get_favorite_playlist(session, playlist_id, current_user.id)
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite playlist not found")

    session.delete(favorite)
    session.commit()
    return FavoriteDeleteResponse(message="Favorite playlist deleted successfully")


@router.delete("/playlists/", response_model=FavoriteDeleteResponse)
async def clear_favorite_playlists(
    request: Request,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> FavoriteDeleteResponse:
    await enforce_rate_limit("clear_favorite_playlists_user", f"user:{current_user.id}", 10, 60)
    session.exec(delete(FavoritePlaylist).where(FavoritePlaylist.user_id == current_user.id))
    session.commit()
    return FavoriteDeleteResponse(message="Favorite playlists cleared successfully")
