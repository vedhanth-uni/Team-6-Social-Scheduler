#refer to the fastapi documentation, especially for databases stuff 

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

from app.config import settings

from app.database import engine,init_db

from app import models  # noqa: F401  -- registers all tables before init_db() runs create_all

from app.routers import health # this is how u call an endpoint file from the routers folder, so we're calling health.py in this case
from app.routers import calendars
from app.routers import events
from app.routers import calendar_import
from app.routers import friends
from app.routers import me

@asynccontextmanager
async def lifespan(app:FastAPI):
    if not settings.SUPABASE_URL:
        # refuse to start rather than run with auth silently broken
        raise RuntimeError("SUPABASE_URL is not set. Copy backend/.env.example to backend/.env and fill it in.")
    init_db()
    try:
        yield
    finally:
        engine.dispose()

app = FastAPI(
    title="Social Scheduler API",
    version="0.0.0",
    lifespan=lifespan,
)

# lets the react app (a different origin) call this api from the browser. Auth is a bearer
# token in a header, not a cookie, so credentials stay off.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.get("/")
def default():
    return {"message:" : "Head over to the health page!" }

app.include_router(health.router)
app.include_router(calendars.router)
app.include_router(events.router)
app.include_router(calendar_import.router)
app.include_router(friends.router)
app.include_router(me.router)
