# """
# gateway/main.py

# Thin API Gateway built with FastAPI.
# Responsibilities:
#   1. Route HTTP requests to the correct downstream service.
#   2. Forward JWT (passed by the client) without validating it here –
#      each service validates with its own public key.
#   3. Expose a WebSocket endpoint so the UI can receive real-time
#      'counter refresh' notifications after a successful donation.

# Environment variables (set in .env or docker-compose):
#     DONATION_USER_URL    e.g. http://donation_user:8001
#     CAMPAIGN_COMMENT_URL e.g. http://campaign_comment:8002
#     SAGA_URL             e.g. http://saga_orchestrator:8003
# """
# from __future__ import annotations

# import asyncio
# import logging
# from typing import Any

# import httpx
# from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, status
# from fastapi.responses import JSONResponse
# from pydantic_settings import BaseSettings

# # ---------------------------------------------------------------------------
# # Settings
# # ---------------------------------------------------------------------------

# class Settings(BaseSettings):
#     DONATION_USER_URL: str = "http://localhost:8001"
#     CAMPAIGN_COMMENT_URL: str = "http://localhost:8002"
#     SAGA_URL: str = "http://localhost:8003"

#     class Config:
#         env_file = ".env"


# cfg = Settings()
# logger = logging.getLogger("gateway")

# # ---------------------------------------------------------------------------
# # App
# # ---------------------------------------------------------------------------

# app = FastAPI(title="API Gateway", version="1.0.0")

# # ---------------------------------------------------------------------------
# # WebSocket connection manager
# # ---------------------------------------------------------------------------

# class _WSManager:
#     def __init__(self):
#         self._connections: list[WebSocket] = []

#     async def connect(self, ws: WebSocket):
#         await ws.accept()
#         self._connections.append(ws)

#     def disconnect(self, ws: WebSocket):
#         self._connections.remove(ws)

#     async def broadcast(self, data: dict):
#         dead = []
#         for ws in self._connections:
#             try:
#                 await ws.send_json(data)
#             except Exception:
#                 dead.append(ws)
#         for ws in dead:
#             self._connections.remove(ws)


# _ws_mgr = _WSManager()


# @app.websocket("/ws/campaign/{campaign_id}")
# async def campaign_ws(ws: WebSocket, campaign_id: str):
#     """
#     Client connects here to receive live counter updates for a campaign.
#     Server pushes {"event": "counter_refresh", "campaignId": <id>} after
#     each successful donation saga.
#     """
#     await _ws_mgr.connect(ws)
#     try:
#         while True:
#             await ws.receive_text()   # keep-alive ping from client
#     except WebSocketDisconnect:
#         _ws_mgr.disconnect(ws)


# # ---------------------------------------------------------------------------
# # Proxy helper
# # ---------------------------------------------------------------------------

# async def _proxy(
#     method: str,
#     url: str,
#     request: Request,
#     body: Any = None,
# ) -> JSONResponse:
#     headers = {
#         k: v for k, v in request.headers.items()
#         if k.lower() not in ("host", "content-length")
#     }
#     async with httpx.AsyncClient(timeout=10.0) as client:
#         try:
#             resp = await client.request(
#                 method,
#                 url,
#                 headers=headers,
#                 json=body,
#             )
#         except httpx.RequestError as exc:
#             raise HTTPException(
#                 status_code=status.HTTP_502_BAD_GATEWAY,
#                 detail=f"Upstream error: {exc}",
#             )
#     return JSONResponse(content=resp.json(), status_code=resp.status_code)


# # ---------------------------------------------------------------------------
# # Auth routes  →  donation_user service
# # ---------------------------------------------------------------------------

# @app.post("/login")
# async def login(request: Request):
#     body = await request.json()
#     return await _proxy("POST", f"{cfg.DONATION_USER_URL}/login", request, body)


# @app.post("/register")
# async def register(request: Request):
#     body = await request.json()
#     return await _proxy("POST", f"{cfg.DONATION_USER_URL}/register", request, body)


# @app.get("/user/{id}")
# async def get_user(id: int, request: Request):
#     return await _proxy("GET", f"{cfg.DONATION_USER_URL}/user/{id}", request)


# # ---------------------------------------------------------------------------
# # Donation  →  Saga Orchestrator
# # ---------------------------------------------------------------------------

# @app.post("/donate")
# async def donate(request: Request):
#     """
#     Routes to the Saga Orchestrator which:
#       1. Saves donation via donation_user service.
#       2. Increments campaign counter via campaign_comment service.
#       3. On success, notifies WebSocket subscribers.
#     """
#     body = await request.json()
#     response = await _proxy("POST", f"{cfg.SAGA_URL}/donate", request, body)

#     if response.status_code == 200:
#         campaign_id = body.get("campaignID", "")
#         asyncio.create_task(
#             _ws_mgr.broadcast({"event": "counter_refresh", "campaignId": campaign_id})
#         )
#     return response


# @app.get("/donate/{campaign_id}")
# async def get_campaign_donations(campaign_id: str, request: Request):
#     return await _proxy(
#         "GET",
#         f"{cfg.DONATION_USER_URL}/donate/{campaign_id}",
#         request,
#     )


# # ---------------------------------------------------------------------------
# # Campaign  →  Saga Orchestrator
# # ---------------------------------------------------------------------------

# @app.post("/campaign")
# async def create_campaign(request: Request):
#     body = await request.json()
#     return await _proxy("POST", f"{cfg.SAGA_URL}/campaign", request, body)


# @app.get("/campaign/{id}")
# async def get_campaign(id: str, request: Request):
#     return await _proxy("GET", f"{cfg.CAMPAIGN_COMMENT_URL}/campaign/{id}", request)


# @app.get("/campaign")
# async def list_campaigns(request: Request):
#     page = request.query_params.get("page", "1")
#     return await _proxy(
#         "GET",
#         f"{cfg.CAMPAIGN_COMMENT_URL}/campaign?page={page}",
#         request,
#     )


# @app.put("/campaign/{id}")
# async def update_campaign(id: str, request: Request):
#     body = await request.json()
#     return await _proxy("PUT", f"{cfg.CAMPAIGN_COMMENT_URL}/campaign/{id}", request, body)


# # ---------------------------------------------------------------------------
# # Comments  →  Saga Orchestrator
# # ---------------------------------------------------------------------------

# @app.post("/comment")
# async def post_comment(request: Request):
#     body = await request.json()
#     return await _proxy("POST", f"{cfg.SAGA_URL}/comment", request, body)


# @app.put("/reply/{id}")
# async def reply_comment(id: str, request: Request):
#     body = await request.json()
#     return await _proxy("PUT", f"{cfg.SAGA_URL}/reply/{id}", request, body)


# # ---------------------------------------------------------------------------
# # Health
# # ---------------------------------------------------------------------------

# @app.get("/health")
# def health():
#     return {"status": "ok"}