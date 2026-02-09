"""Main FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path

from app.config import settings
from app.database import init_db, SessionLocal, engine
from app.models.user import User
from app.utils.auth import get_password_hash
from app.api import auth, devices


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    init_db()

    # Create default admin user if not exists
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=get_password_hash("admin"),
            )
            db.add(admin)
            db.commit()
            print("✅ Created default admin user (username: admin, password: admin)")
    finally:
        db.close()

    yield
    # Shutdown (if needed)


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="局域网设备管理 - SmsForwarder Web Manager",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/auth")
app.include_router(devices.router, prefix="/api/devices")


# ============== Special Routes (must be before {device_id} routes) ==============

@app.post("/api/devices/scan")
async def scan_network(local_ip: str = None):
    """Scan local network for devices."""
    from app.utils.network import discover_devices
    return await discover_devices(local_ip)


@app.post("/api/devices/test")
async def test_device_by_ip():
    """Test device connection by IP (handled by devices router)."""
    # This route is handled by devices.router, kept here for documentation
    pass


# ============== Health Check (before SPA routes) ==============

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}


# ============== Avatar Static Files ==============

# Mount avatars directory (same directory used by auth.py)
from app.config import settings
AVATAR_DIR = Path(settings.database_file).parent / "avatars"
AVATAR_DIR.mkdir(exist_ok=True)
app.mount("/avatars", StaticFiles(directory=str(AVATAR_DIR)), name="avatars")


# ============== Frontend Static Files ==============

# Path to frontend build output
FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "dist"


@app.get("/")
async def root():
    """Serve index.html for SPA routing."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse({
        "message": "SmsManager API",
        "docs": "/docs",
        "frontend": "Frontend not built yet. Run: cd frontend && npm install && npm run build"
    })


@app.get("/{path:path}")
async def serve_frontend(path: str):
    """Serve frontend assets and handle SPA routing."""
    # API paths should be handled by routers, return 404
    if path.startswith("api/"):
        return JSONResponse(
            status_code=404,
            content={"detail": f"Path /{path} not found"}
        )

    # Check if it's a static asset
    file_path = FRONTEND_DIR / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))

    # Otherwise serve index.html for SPA routing
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))

    return JSONResponse({
        "error": "Frontend not built",
        "hint": "Run: cd frontend && npm install && npm run build"
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
