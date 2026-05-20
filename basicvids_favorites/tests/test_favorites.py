from sqlmodel import Session, delete
import httpx
import pytest

from basicvids_favorites.auth import CurrentUser, get_current_user
from basicvids_favorites.schemas.favorites import FavoritePlaylist, FavoriteVideo
from basicvids_favorites.tests import app, engine


pytestmark = pytest.mark.anyio


async def request(method: str, url: str, **kwargs):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, url, **kwargs)


def user(user_id: int = 1, is_admin: bool = False) -> CurrentUser:
    return CurrentUser(
        id=user_id,
        username=f"user-{user_id}",
        first_name="Test",
        last_name="Viewer",
        email=f"user-{user_id}@example.com",
        is_admin=is_admin,
        email_confirmed=True,
    )


def set_current_user(current_user: CurrentUser) -> None:
    async def override_get_current_user():
        return current_user

    app.dependency_overrides[get_current_user] = override_get_current_user


class BaseTestFavorites:
    def setup_method(self):
        set_current_user(user())
        with Session(engine) as session:
            session.exec(delete(FavoriteVideo))
            session.exec(delete(FavoritePlaylist))
            session.commit()


class TestFavoriteVideos(BaseTestFavorites):
    method_url = "/api/v1/favorites/videos"

    async def add_video(self, video_id: str = "video-1"):
        response = await request("PUT", f"{self.method_url}/{video_id}")
        return response.json()

    async def test_add_favorite_video_creates_entry(self):
        response = await request("PUT", f"{self.method_url}/video-1")

        assert response.status_code == 201
        body = response.json()
        assert body["video_id"] == "video-1"
        assert body["user_id"] == 1
        assert body["created_at"]

    async def test_add_favorite_video_is_idempotent(self):
        first = await request("PUT", f"{self.method_url}/video-1")
        second = await request("PUT", f"{self.method_url}/video-1")

        assert second.status_code == 201
        assert second.json()["id"] == first.json()["id"]

    async def test_list_favorite_videos(self):
        await self.add_video("video-1")
        await self.add_video("video-2")

        response = await request("GET", f"{self.method_url}/")

        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 2
        assert {item["video_id"] for item in body["items"]} == {"video-1", "video-2"}

    async def test_get_favorite_video_status(self):
        await self.add_video("video-1")

        response = await request("GET", f"{self.method_url}/video-1")
        missing_response = await request("GET", f"{self.method_url}/video-2")

        assert response.status_code == 200
        assert response.json() == {"is_favorite": True}
        assert missing_response.status_code == 200
        assert missing_response.json() == {"is_favorite": False}

    async def test_get_favorite_video_statuses(self):
        await self.add_video("video-1")

        response = await request("POST", f"{self.method_url}/statuses", json={"video_ids": ["video-1", "video-2"]})

        assert response.status_code == 200
        assert response.json() == {"favorites": {"video-1": True, "video-2": False}}

    async def test_delete_favorite_video(self):
        await self.add_video("video-1")

        response = await request("DELETE", f"{self.method_url}/video-1")

        assert response.status_code == 200
        assert response.json() == {"message": "Favorite video deleted successfully"}

    async def test_clear_favorite_videos(self):
        await self.add_video("video-1")
        await self.add_video("video-2")

        response = await request("DELETE", f"{self.method_url}/")

        assert response.status_code == 200
        assert response.json() == {"message": "Favorite videos cleared successfully"}

        response = await request("GET", f"{self.method_url}/")
        assert response.status_code == 200
        assert response.json()["count"] == 0

    async def test_favorite_videos_are_user_scoped(self):
        await self.add_video("video-1")
        set_current_user(user(user_id=2))

        response = await request("GET", f"{self.method_url}/")

        assert response.status_code == 200
        assert response.json()["count"] == 0

    async def test_favorite_video_requires_authentication(self):
        app.dependency_overrides.pop(get_current_user, None)

        response = await request("PUT", f"{self.method_url}/video-1")

        assert response.status_code == 401


class TestFavoritePlaylists(BaseTestFavorites):
    method_url = "/api/v1/favorites/playlists"

    async def add_playlist(self, playlist_id: str = "playlist-1", channel_id: str = "channel-1"):
        response = await request("PUT", f"{self.method_url}/{playlist_id}", json={"channel_id": channel_id})
        return response.json()

    async def test_add_favorite_playlist_creates_entry(self):
        response = await request("PUT", f"{self.method_url}/playlist-1", json={"channel_id": "channel-1"})

        assert response.status_code == 201
        body = response.json()
        assert body["playlist_id"] == "playlist-1"
        assert body["channel_id"] == "channel-1"
        assert body["user_id"] == 1

    async def test_add_favorite_playlist_updates_channel_id(self):
        first = await request("PUT", f"{self.method_url}/playlist-1", json={"channel_id": "channel-1"})
        second = await request("PUT", f"{self.method_url}/playlist-1", json={"channel_id": "channel-2"})

        assert second.status_code == 201
        assert second.json()["id"] == first.json()["id"]
        assert second.json()["channel_id"] == "channel-2"

    async def test_list_favorite_playlists(self):
        await self.add_playlist("playlist-1", "channel-1")
        await self.add_playlist("playlist-2", "channel-2")

        response = await request("GET", f"{self.method_url}/")

        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 2
        assert {item["playlist_id"] for item in body["items"]} == {"playlist-1", "playlist-2"}

    async def test_get_favorite_playlist_statuses(self):
        await self.add_playlist("playlist-1", "channel-1")

        response = await request(
            "POST",
            f"{self.method_url}/statuses",
            json={"playlist_ids": ["playlist-1", "playlist-2"]},
        )

        assert response.status_code == 200
        assert response.json() == {"favorites": {"playlist-1": True, "playlist-2": False}}

    async def test_delete_favorite_playlist(self):
        await self.add_playlist("playlist-1", "channel-1")

        response = await request("DELETE", f"{self.method_url}/playlist-1")

        assert response.status_code == 200
        assert response.json() == {"message": "Favorite playlist deleted successfully"}
