"""Raw fetch capability exposed to the model as a tool.

The plugin decides *when*; the model decides *what* to fetch and how to report
it. This module only turns one URL into compact, model-friendly text.
"""

from __future__ import annotations

from .models import SourceConfig
from .sources.auto import build_auto_items
from .sources.base import BaseSource
from .sources.http import FetchError, HttpClient, decode_bytes

MAX_ITEMS = 5


async def fetch_content(
    http: HttpClient,
    url: str,
    *,
    cookie: str = "",
    max_items: int = MAX_ITEMS,
    timeout: float = 15.0,
) -> dict:
    """Fetch ``url`` and return ``{kind, title, items, text}`` for the model."""

    headers = {"Cookie": cookie} if cookie else None
    _, raw, response_headers = await http.request(
        url, headers=headers, timeout=timeout
    )
    text = decode_bytes(raw, response_headers)

    cfg = SourceConfig(
        id="fetch",
        type="auto",
        label="",
        url=url,
        max_items=max(1, min(int(max_items or MAX_ITEMS), 10)),
    )
    try:
        items = build_auto_items(text, cfg)
    except FetchError as exc:
        # Not a feed/JSON/HTML we understand: hand back a trimmed snippet.
        snippet = " ".join(text.split())[:1200]
        if not snippet:
            raise
        return {"ok": True, "kind": "text", "url": url, "text": snippet,
                "note": exc.code}

    payload: dict = {"ok": True, "url": url, "kind": "items", "items": []}
    for item in items:
        payload["items"].append(
            {
                "title": item.title,
                "summary": item.summary,
                "url": item.url,
            }
        )
    return payload


def require_url(url: str) -> str:
    """Small guard so the model cannot ask us to read local files."""

    value = (url or "").strip()
    if not value.lower().startswith(("http://", "https://")):
        raise FetchError("CONFIG_INVALID", "url must be http(s)")
    return value


__all__ = ["fetch_content", "require_url", "BaseSource"]
