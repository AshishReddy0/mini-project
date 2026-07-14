# FastAPI application entry point for Study Companion.

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import check_db_connection, init_db
from app.routes import auth, chat, content, documents, roadmap, workspaces, graph


import os
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Run once when the server starts.
    Creates database tables if they do not exist yet.
    """
    os.makedirs("uploads", exist_ok=True)
    init_db()
    yield


app = FastAPI(
    title="Study Companion API",
    description="Backend API for the Study Companion academic workspace",
    version="0.2.0",
    lifespan=lifespan,
)

# Mount the uploads directory to serve documents statically
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Allow the React dev server to call the API during local development / production
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all API route groups
app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(documents.router)
app.include_router(content.router)
app.include_router(chat.router)
app.include_router(roadmap.router)
app.include_router(graph.router)


@app.get("/health")
def health_check():
    """Basic health check — confirms the API server is running."""
    return {"status": "ok"}


@app.get("/health/db")
def health_db_check():
    """Database health check — confirms PostgreSQL is reachable."""
    connected = check_db_connection()
    return {
        "status": "ok" if connected else "error",
        "database": "connected" if connected else "disconnected",
    }
