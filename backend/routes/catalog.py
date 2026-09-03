from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.models import Product
from backend.db.session import get_db

router = APIRouter(prefix="/catalog", tags=["catalog"])


class ProductOut(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock: int
    category: str
    image_url: Optional[str] = None


@router.get("", response_model=list[ProductOut])
def list_catalog(db: Session = __import__("fastapi").Depends(get_db)) -> list[ProductOut]:
    products = db.query(Product).all()
    return [
        ProductOut(
            id=item.id,
            name=item.name,
            description=item.description,
            price=item.price,
            stock=item.stock,
            category=item.category,
            image_url=item.image_url,
        )
        for item in products
    ]


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = __import__("fastapi").Depends(get_db)) -> ProductOut:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return ProductOut(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        category=product.category,
        image_url=product.image_url,
    )
