from fastapi import FastAPI

from .api import api_router
from .core.database import engine
from .models import Base

app = FastAPI(title="BuildWise API")
app.include_router(api_router)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def read_root():
    return {"message": "Hello World"}
