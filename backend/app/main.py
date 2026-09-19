# FastAPI application entry point for Study Companion.

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import check_db_connection, init_db
from app.routes import auth, chat, content, documents, roadmap, workspaces, graph

import os
from fastapi.staticfiles import StaticFiles

# Defines server startup lifespan handler to create uploads directory and initialize DB
@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("uploads", exist_ok=True)
    init_db()
    yield

# Initializes FastAPI app instance with metadata and lifespan handler
app = FastAPI(
    title="Study Companion API",
    description="Backend API for the Study Companion academic workspace",
    version="0.2.0",
    lifespan=lifespan,
)

# Mounts static uploads directory for serving uploaded study document files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Configures CORS middleware for cross-origin frontend requests
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env and allowed_origins_env.strip() != "*":
    origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Registers API route handlers for authentication, workspaces, documents, graphs, content, and chat
app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(documents.router)
app.include_router(content.router)
app.include_router(chat.router)
app.include_router(roadmap.router)
app.include_router(graph.router)

# Basic API server operational health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Database connectivity health check endpoint
@app.get("/health/db")
def health_db_check():
    connected = check_db_connection()
    return {
        "status": "ok" if connected else "error",
        "database": "connected" if connected else "disconnected",
    }

