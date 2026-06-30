from __future__ import annotations

import httpx

from .models import Channel, Guild, Message
from .rate_limiter import RateLimiter

BASE_URL = "https://discord.com/api/v10"
MAX_PER_PAGE = 100


class DiscordClient:
    """Discord API v10 client with rate limiting."""

    def __init__(self, token: str, rate_limiter: RateLimiter | None = None) -> None:
        self._token = token
        self._rate_limiter = rate_limiter or RateLimiter()
        self._http: httpx.Client | None = None

    @property
    def rate_limiter(self) -> RateLimiter:
        return self._rate_limiter

    def __enter__(self) -> DiscordClient:
        self._http = httpx.Client(
            base_url=BASE_URL,
            headers={"Authorization": self._token},
            timeout=30.0,
        )
        return self

    def __exit__(self, *exc: object) -> None:
        if self._http:
            self._http.close()
            self._http = None

    def _request(self, method: str, url: str, **kwargs: object) -> httpx.Response:
        assert self._http is not None, "Use DiscordClient as a context manager"
        return self._rate_limiter.execute(
            lambda: self._http.request(method, url, **kwargs)  # type: ignore[union-attr]
        )

    def get_channel(self, channel_id: str) -> Channel:
        resp = self._request("GET", f"/channels/{channel_id}")
        if resp.status_code != 200:
            return Channel(id=channel_id, name=channel_id, guild_id="unknown")
        return Channel.from_api(resp.json())

    def get_guild(self, guild_id: str) -> Guild:
        resp = self._request("GET", f"/guilds/{guild_id}")
        if resp.status_code != 200:
            return Guild.unknown(guild_id)
        return Guild.from_api(resp.json())

    def get_messages(
        self,
        channel_id: str,
        *,
        before: str | None = None,
        after: str | None = None,
        limit: int = MAX_PER_PAGE,
    ) -> list[dict]:
        """Fetch a single page of messages. Returns raw dicts."""
        params: dict[str, str | int] = {"limit": limit}
        if before:
            params["before"] = before
        if after:
            params["after"] = after

        resp = self._request("GET", f"/channels/{channel_id}/messages", params=params)

        if resp.status_code == 401:
            raise AuthenticationError("Invalid or expired token.")
        if resp.status_code == 403:
            raise AccessDeniedError(f"No access to channel {channel_id}.")
        if resp.status_code != 200:
            raise APIError(f"HTTP {resp.status_code}: {resp.text}")

        return resp.json()


class APIError(Exception):
    pass


class AuthenticationError(APIError):
    pass


class AccessDeniedError(APIError):
    pass
