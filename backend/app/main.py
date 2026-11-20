from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # (registers every table before create_all runs)
from app.config import settings
from app.database import create_db_and_tables
from app.routers import calendar_import, calendars, events, friends, health, me, profile, friend_events


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Social Scheduler", lifespan=lifespan)

# lets the frontend (a different origin) call the api from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(me.router)
app.include_router(profile.router)
app.include_router(friends.router)
app.include_router(calendars.router)
app.include_router(events.router)
app.include_router(calendar_import.router)
app.include_router(friend_events.router)