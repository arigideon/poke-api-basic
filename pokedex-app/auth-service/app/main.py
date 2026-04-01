from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app import models, router

# Create database tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Pokédex Auth Service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router.router, prefix="/auth", tags=["auth"])


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "auth"}
