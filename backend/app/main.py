from fastapi import FastAPI
from app.routers import produto

app = FastAPI()

app.include_router(produto.product)