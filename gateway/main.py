"""
gateway/main.py – API Gateway (PORT 3000)
"""

from __future__ import annotations
import os
import asyncio
from typing import Any, Annotated

import httpx
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from fastapi import Body
from dotenv import load_dotenv

from .auth import TokenPayload                         
from .models.schemas import (
    CampaignUpdate,
    LoginRequest,
    RegisterRequest,
    CampaignCreate,
    DonationCreate,
    CommentCreate,
    ReportCreate,
)

# ---------------------------------------------------------------------------
# ENV
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DONATION_USER_URL   = os.getenv("DONATION_USER_SERVICE")
CAMPAIGN_COMMENT_URL = os.getenv("CAMPAIGN_COMMENT_SERVICE")
SAGA_URL             = os.getenv("SAGA_SERVICE")

if not all([DONATION_USER_URL, CAMPAIGN_COMMENT_URL, SAGA_URL]):
    raise RuntimeError("Missing environment variables in .env")

# ---------------------------------------------------------------------------
# APP
# ---------------------------------------------------------------------------
app = FastAPI(title="API Gateway", version="1.0.0")


# ---------------------------------------------------------------------------
# PROXY HELPER
# ---------------------------------------------------------------------------
async def _proxy(
    method: str,
    url: str,
    request: Request,
    body: Any = None,
    *,
    extra_headers: dict[str, str] | None = None,
) -> JSONResponse:
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }
    headers = {k: v for k, v in headers.items() if not k.lower().startswith("x-user-")}

    if extra_headers:
        headers.update(extra_headers)

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.request(method, url, headers=headers, json=body)
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Upstream error: {exc}",
            )

    try:
        data = resp.json()
    except Exception:
        data = resp.text

    return JSONResponse(content=data, status_code=resp.status_code)


def _user_headers(token: dict) -> dict[str, str]:
    return {
        "X-User-Id":    str(token.get("sub", "")),
        "X-User-Email": str(token.get("email", "")),
        "X-User-Role":  str(token.get("role", "")),
    }


# ---------------------------------------------------------------------------
# WEBSOCKET
# ---------------------------------------------------------------------------
class _WSManager:
    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self._connections.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self._connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections.remove(ws)


_ws_mgr = _WSManager()


@app.websocket("/ws/campaign/{campaign_id}")
async def campaign_ws(ws: WebSocket, campaign_id: str):
    await _ws_mgr.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        _ws_mgr.disconnect(ws)


# ---------------------------------------------------------------------------
# AUTH (public)
# ---------------------------------------------------------------------------
@app.post("/login")
async def login(body: LoginRequest, request: Request):
    return await _proxy("POST", f"{DONATION_USER_URL}/login", request, body.dict())


@app.post("/register")
async def register(body: RegisterRequest, request: Request):
    return await _proxy("POST", f"{SAGA_URL}/register", request, body.dict())


@app.get("/user/{id}")
async def get_user(id: int, request: Request):
    return await _proxy("GET", f"{DONATION_USER_URL}/user/{id}", request)


# ---------------------------------------------------------------------------
# DONATION — protected
# ---------------------------------------------------------------------------
@app.post("/donate")
async def donate(
    body: DonationCreate,
    request: Request,
    token: TokenPayload,                           # ← enforces auth
):
    # UserID comes from the verified token, not the request body
    payload = body.dict()
    payload["userID"] = int(token["sub"])          # overwrite / set from token

    response = await _proxy(
        "POST",
        f"{SAGA_URL}/donate",
        request,
        payload,
        extra_headers=_user_headers(token),
    )

    if response.status_code == 200:
        asyncio.create_task(
            _ws_mgr.broadcast({
                "event": "counter_refresh",
                "campaignId": body.campaignID,
            })
        )

    return response

@app.get("/donate/{campaign_id}/running-total")
async def get_running_total(campaign_id: str, request: Request):
    return await _proxy("GET", f"{DONATION_USER_URL}/donate/{campaign_id}/running-total", request)

@app.get("/donate/{campaign_id}")
async def get_donations(campaign_id: str, request: Request):
    return await _proxy("GET", f"{DONATION_USER_URL}/donate/{campaign_id}", request)


# ---------------------------------------------------------------------------
# CAMPAIGN
# ---------------------------------------------------------------------------
@app.post("/campaign")
async def create_campaign(
    body: CampaignCreate,
    request: Request,
    token: TokenPayload,                           # ← protected
):
    payload = body.dict()
    payload["ownerId"] = int(token["sub"])         # set from token

    return await _proxy(
        "POST",
        f"{SAGA_URL}/campaign",
        request,
        payload,
        extra_headers=_user_headers(token),
    )


@app.get("/campaign")
async def list_campaigns(page: int = 1, request: Request = None):
    return await _proxy("GET", f"{CAMPAIGN_COMMENT_URL}/campaign?page={page}", request)


@app.get("/campaign/{id}")
async def get_campaign(id: str, request: Request):
    return await _proxy("GET", f"{CAMPAIGN_COMMENT_URL}/campaign/{id}", request)


@app.put("/campaign/{id}")
async def update_campaign(
    id: str,
    body: Annotated[CampaignUpdate, Body()],
    request: Request,
    token: TokenPayload,                           # ← protected
):
    return await _proxy(
        "PUT",
        f"{CAMPAIGN_COMMENT_URL}/campaign/{id}",
        request,
        body.dict(),
        extra_headers=_user_headers(token),
    )


# ---------------------------------------------------------------------------
# COMMENTS — protected
# ---------------------------------------------------------------------------
@app.post("/comment")
async def comment(
    body: CommentCreate,
    request: Request,
    token: TokenPayload,
):
    payload = body.dict()
    payload["userId"] = int(token["sub"])

    return await _proxy(
        "POST",
        f"{SAGA_URL}/comment",
        request,
        payload,
        extra_headers=_user_headers(token),
    )


@app.put("/reply/{id}")
async def reply(
    id: str,
    body: CommentCreate,
    request: Request,
    token: TokenPayload,
):
    payload = body.dict()
    payload["userId"] = int(token["sub"])

    return await _proxy(
        "PUT",
        f"{SAGA_URL}/reply/{id}",
        request,
        payload,
        extra_headers=_user_headers(token),
    )
    
@app.put("/active-commenters")
async def get_active_commenters(request: Request, top_n : int | None = 10):
    return await _proxy(
        "GET",
        f"{CAMPAIGN_COMMENT_URL}/active-commenters?top_n={top_n}",
        request
    )

# ---------------------------------------------------------------------------
# REPORT — protected
# ---------------------------------------------------------------------------
@app.post("/report")
async def report(
    body: ReportCreate,
    request: Request,
    token: TokenPayload,
):
    return await _proxy(
        "POST",
        f"{SAGA_URL}/report",
        request,
        body.dict(),
        extra_headers=_user_headers(token),
    )


# ---------------------------------------------------------------------------
# IMAGE UPLOAD — protected 
# ---------------------------------------------------------------------------
@app.post("/image/{report_id}/{campaign_id}")
async def upload_image(
    report_id: str,
    campaign_id: str,
    request: Request,
    token: TokenPayload,
):

    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host",)
        and not k.lower().startswith("x-user-")
    }
    headers.update(_user_headers(token))

    body_bytes = await request.body()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{SAGA_URL}/image/{report_id}/{campaign_id}",
                headers=headers,
                content=body_bytes,
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Upstream error: {exc}")

    try:
        data = resp.json()
    except Exception:
        data = resp.text

    return JSONResponse(content=data, status_code=resp.status_code)


# ---------------------------------------------------------------------------
# LIKE — protected
# ---------------------------------------------------------------------------
@app.put("/like/{campaign_id}/{user_id}")
async def like(
    campaign_id: str,
    user_id: int,
    request: Request,
    token: TokenPayload,
):
    # Prevent a user from liking as someone else
    token_user_id = int(token["sub"])
    if token_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user_id in path must match authenticated user",
        )

    return await _proxy(
        "PUT",
        f"{CAMPAIGN_COMMENT_URL}/like/{campaign_id}/{user_id}",
        request,
        extra_headers=_user_headers(token),
    )


# ---------------------------------------------------------------------------
# HEALTH (public)
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}