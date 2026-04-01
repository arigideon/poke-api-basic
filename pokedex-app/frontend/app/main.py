from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings

app = FastAPI(title="Pokédex Frontend", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

_AUTH_COOKIE = "pokedex_token"


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

async def _verify_session(request: Request) -> dict | None:
    """Return the verified user dict or None if the session is invalid/missing."""
    token = request.cookies.get(_AUTH_COOKIE)
    if not token:
        return None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.auth_service_url}/auth/verify",
                json={"token": token},
                timeout=5.0,
            )
        if resp.status_code == 200:
            return resp.json()  # {"username": "...", "valid": true}
    except httpx.RequestError:
        pass
    return None


def _redirect_login(next_url: str = "/") -> RedirectResponse:
    return RedirectResponse(f"/login?next={next_url}", status_code=302)


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = await _verify_session(request)
    if not user:
        return _redirect_login("/")
    return templates.TemplateResponse("pokedex.html", {"request": request, "user": user})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = await _verify_session(request)
    if user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    user = await _verify_session(request)
    if user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie(_AUTH_COOKIE)
    return response


# ---------------------------------------------------------------------------
# Auth proxy routes (browser → frontend → auth-service)
# ---------------------------------------------------------------------------

@app.post("/auth/login")
async def proxy_login(request: Request):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.auth_service_url}/auth/login",
            json=body,
            timeout=5.0,
        )
    if resp.status_code != 200:
        return JSONResponse(resp.json(), status_code=resp.status_code)

    token = resp.json()["access_token"]
    response = JSONResponse({"success": True})
    response.set_cookie(
        key=_AUTH_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=3600,
        secure=False,  # Set to True when using HTTPS in production
    )
    return response


@app.post("/auth/register")
async def proxy_register(request: Request):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.auth_service_url}/auth/register",
            json=body,
            timeout=5.0,
        )
    return JSONResponse(resp.json(), status_code=resp.status_code)


# ---------------------------------------------------------------------------
# API proxy routes (browser → frontend → backend)
# All routes validate the session before forwarding.
# ---------------------------------------------------------------------------

async def _proxy_api(request: Request, path: str) -> JSONResponse:
    user = await _verify_session(request)
    if not user:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)

    params = dict(request.query_params)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.backend_url}/api/{path}",
                params=params,
                timeout=30.0,
            )
        return JSONResponse(resp.json(), status_code=resp.status_code)
    except httpx.RequestError:
        return JSONResponse({"detail": "Backend unavailable"}, status_code=503)


@app.get("/api/pokemon")
async def api_list_pokemon(request: Request):
    return await _proxy_api(request, "pokemon")


@app.get("/api/pokemon/{name_or_id}")
async def api_get_pokemon(request: Request, name_or_id: str):
    return await _proxy_api(request, f"pokemon/{name_or_id}")


@app.get("/api/types")
async def api_types(request: Request):
    return await _proxy_api(request, "types")


@app.get("/api/search")
async def api_search(request: Request):
    return await _proxy_api(request, "search")


@app.get("/health")
def health():
    return {"status": "ok", "service": "frontend"}
