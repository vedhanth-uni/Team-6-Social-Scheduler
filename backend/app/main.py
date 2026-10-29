#refer to the fastapi documentation, especially for databases stuff 

from fastapi import FastAPI

from contextlib import asynccontextmanager

from app import models

from app.database import create_db_and_tables

from app.routers import health,profile # this is how u call an endpoint file from the routers folder, so we're calling health.py in this case

@asynccontextmanager
async def lifespan(app:FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Social Scheduler" , lifespan = lifespan)

app.include_router(health.router)
app.include_router(profile.router)