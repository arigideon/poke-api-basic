import asyncio
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.cache import pokemon_cache
from app.config import settings

router = APIRouter()
POKEAPI = settings.pokeapi_base_url


def _normalize_pokemon(raw: dict) -> dict:
    """Extract only the fields the frontend needs from a raw PokéAPI payload."""
    sprites = raw.get("sprites", {})
    other = sprites.get("other", {})
    official = other.get("official-artwork", {})

    return {
        "id": raw["id"],
        "name": raw["name"],
        "height": raw["height"],
        "weight": raw["weight"],
        "base_experience": raw.get("base_experience"),
        "sprites": {
            "front_default": sprites.get("front_default"),
            "front_shiny": sprites.get("front_shiny"),
            "official_artwork": official.get("front_default"),
            "official_artwork_shiny": official.get("front_shiny"),
        },
        "types": [t["type"]["name"] for t in raw["types"]],
        "abilities": [
            {"name": a["ability"]["name"], "is_hidden": a["is_hidden"]}
            for a in raw["abilities"]
        ],
        "stats": [
            {"name": s["stat"]["name"], "base_stat": s["base_stat"]}
            for s in raw["stats"]
        ],
        "moves_count": len(raw.get("moves", [])),
    }


async def _fetch_one(client: httpx.AsyncClient, url_or_name: str) -> dict | None:
    cache_key = f"pokemon:{url_or_name}"
    cached = await pokemon_cache.get(cache_key)
    if cached is not None:
        return cached

    url = (
        url_or_name
        if url_or_name.startswith("http")
        else f"{POKEAPI}/pokemon/{url_or_name}"
    )
    resp = await client.get(url, timeout=10.0)
    if resp.status_code != 200:
        return None

    result = _normalize_pokemon(resp.json())
    await pokemon_cache.set(cache_key, result)
    return result


@router.get("/pokemon")
async def list_pokemon(
    offset: int = Query(0, ge=0),
    limit: int = Query(24, ge=1, le=100),
    type_filter: str | None = Query(None, alias="type", description="Filter by Pokémon type"),
) -> dict[str, Any]:
    cache_key = f"list:{offset}:{limit}:{type_filter}"
    cached = await pokemon_cache.get(cache_key)
    if cached is not None:
        return cached

    async with httpx.AsyncClient() as client:
        if type_filter:
            resp = await client.get(f"{POKEAPI}/type/{type_filter}", timeout=10.0)
            if resp.status_code == 404:
                raise HTTPException(404, detail=f"Type '{type_filter}' not found")
            if resp.status_code != 200:
                raise HTTPException(502, detail="Failed to reach PokéAPI")

            all_entries = resp.json()["pokemon"]
            total = len(all_entries)
            page_entries = all_entries[offset : offset + limit]
            urls = [e["pokemon"]["url"] for e in page_entries]

        else:
            resp = await client.get(
                f"{POKEAPI}/pokemon", params={"offset": offset, "limit": limit}, timeout=10.0
            )
            if resp.status_code != 200:
                raise HTTPException(502, detail="Failed to reach PokéAPI")
            data = resp.json()
            total = data["count"]
            urls = [p["url"] for p in data["results"]]

        details = await asyncio.gather(*[_fetch_one(client, url) for url in urls])

    result = {
        "results": [d for d in details if d is not None],
        "total": total,
        "offset": offset,
        "limit": limit,
    }
    await pokemon_cache.set(cache_key, result)
    return result


@router.get("/pokemon/{name_or_id}")
async def get_pokemon(name_or_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        pokemon = await _fetch_one(client, name_or_id.lower().strip())
    if pokemon is None:
        raise HTTPException(404, detail=f"Pokémon '{name_or_id}' not found")
    return pokemon


@router.get("/types")
async def get_types() -> list[str]:
    cached = await pokemon_cache.get("types")
    if cached is not None:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{POKEAPI}/type", params={"limit": 100}, timeout=10.0)
    data = resp.json()
    types = [t["name"] for t in data["results"] if t["name"] not in ("unknown", "shadow")]
    await pokemon_cache.set("types", types)
    return types


@router.get("/search")
async def search_pokemon(q: str = Query(..., min_length=1)) -> dict[str, Any]:
    """Exact-name or ID lookup. Returns a single-item list for API consistency."""
    async with httpx.AsyncClient() as client:
        pokemon = await _fetch_one(client, q.lower().strip())

    if pokemon:
        return {"results": [pokemon], "total": 1}
    return {"results": [], "total": 0}
