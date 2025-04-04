from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import orjson

if TYPE_CHECKING:
    import aiohttp

SEARCH_ENDPOINT = "https://embedez.com/api/v1/providers/search?url={url}"
OEMBED_ENDPOINT = "https://embedez.com/api/v1/og/alternate?id={id}&amp;mediaKey=media"

BASE_URL = "https://twelve-chicken-fetch.loca.lt"
EMBED_HTML = f"""
<head>
    <meta name="og:type" content="rich"/>
    <link rel="alternate" type="application/json+oembed"
    href="{BASE_URL}/oembed?url={{url}}&amp;mediaKey=media"/>
</head>
"""


@dataclass
class SearchResult:
    key: str
    site: str


async def fetch_html(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.text()


async def search_embedez(session: aiohttp.ClientSession, url: str) -> SearchResult:
    async with session.get(SEARCH_ENDPOINT.format(url=url)) as resp:
        resp.raise_for_status()
        data: dict[str, Any] = await resp.json()

    return SearchResult(key=data["data"]["key"], site=data["data"]["site"])


async def fetch_embedez_oembed(session: aiohttp.ClientSession, url: str) -> dict[str, Any]:
    async with session.get(SEARCH_ENDPOINT.format(url=url)) as resp:
        resp.raise_for_status()
        data: dict[str, Any] = await resp.json()

        key = data["data"]["key"]

    async with session.get(OEMBED_ENDPOINT.format(id=key)) as resp:
        resp.raise_for_status()
        text = await resp.text()

    return orjson.loads(text)


def modify_oembed(oembed: dict[str, Any], url: str) -> dict[str, Any]:
    oembed["author_url"] = url
    oembed["provider_url"] = url
    return oembed


def get_embed_html(url: str) -> str:
    return EMBED_HTML.format(url=url)
