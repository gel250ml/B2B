from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from src.database.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

# origins = [
#     "http://localhost",
# ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Потом заменить на origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)