from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import aiohttp_socks
import fastapi
from aiohttp_client_cache.backends.sqlite import SQLiteBackend
from aiohttp_client_cache.session import CachedSession

from embedez.utils import fetch_html, search_embedez

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger("uvicorn")


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI) -> AsyncGenerator[None, fastapi.FastAPI]:
    proxy_url = os.getenv("PROXY_URL")
    if proxy_url:
        logger.info("Using proxy")
    connector = aiohttp_socks.ProxyConnector.from_url(proxy_url) if proxy_url else None

    cache = SQLiteBackend("cache.db", expire_after=3600)
    app.state.session = CachedSession(
        cache=None if os.getenv("DISABLE_CACHE") else cache,
        connector=connector,
        headers={"User-Agent": "Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)"},
    )
    yield
    await app.state.session.close()


app = fastapi.FastAPI(lifespan=lifespan)


@app.get("/")
def root() -> fastapi.Response:
    return fastapi.responses.RedirectResponse("https://github.com/seriaati/embedez")


@app.get("/embed")
async def embed(request: fastapi.Request) -> fastapi.Response:
    url = request.query_params.get("url")
    if not url:
        return fastapi.responses.JSONResponse(
            content={"error": "URL parameter is required"}, status_code=400
        )

    if "Discordbot" not in request.headers.get("User-Agent", ""):
        return fastapi.responses.RedirectResponse(url)

    result = await search_embedez(request.app.state.session, url)
    logger.info("Found embedez result for %s: %s", url, result)

    embedez_url = f"https://embedez.com/embed/{result.key}"
    html = await fetch_html(request.app.state.session, embedez_url)

    html = html.replace(embedez_url, url)
    html = html.replace("EmbedEZ", result.site.title())
    html = html.replace("@embedez.com", f"@{request.url.netloc}")

    return fastapi.responses.HTMLResponse(html)
