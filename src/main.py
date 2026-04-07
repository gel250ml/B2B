from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from src.database.init_db import init_db
from src.routes.invoice_routes import router as invoice_routes
from src.routes.product_routes import router as product_routes
from src.routes.sku_routes import router as sku_routes

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

app.include_router(invoice_routes, prefix="/api/v1")
app.include_router(product_routes, prefix="/api/v1")
app.include_router(sku_routes, prefix="/api/v1")