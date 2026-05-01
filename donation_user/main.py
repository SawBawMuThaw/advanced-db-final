from fastapi import FastAPI
 
from routes.auth_routes import router as auth_router
from routes.donation_routes import router as donation_router
from routes.user_routes import router as user_router
 
app = FastAPI(title="Donation & User Service", version="1.0.0")
 
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(donation_router)
 
 
@app.get("/health")
def health():
    return {"status": "ok"}