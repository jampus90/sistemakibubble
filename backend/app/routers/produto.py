from fastapi import APIRouter

product = APIRouter()


@product.get("/products")
async def get_products():
    return {"products": ["Product 1", "Product 2", "Product 3"]}