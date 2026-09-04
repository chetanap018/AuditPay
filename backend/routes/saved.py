from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.models import Product, SavedProduct
from backend.db.session import get_db

router = APIRouter(prefix="/saved", tags=["saved"])


class SavedProductRequest(BaseModel):
    product_id: int
    session_id: str = "demo-session"


class SavedProductOut(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock: int
    category: str
    image_url: Optional[str] = None


def to_product_out(product: Product) -> SavedProductOut:
    return SavedProductOut(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        category=product.category,
        image_url=product.image_url,
    )


@router.get("", response_model=list[SavedProductOut])
def list_saved_products(
    session_id: str = "demo-session", db: Session = Depends(get_db)
) -> list[SavedProductOut]:
    saved = (
        db.query(SavedProduct)
        .join(Product)
        .filter(SavedProduct.session_id == session_id)
        .order_by(SavedProduct.created_at.desc())
        .all()
    )
    return [to_product_out(item.product) for item in saved]


@router.post("", response_model=SavedProductOut)
def save_product(
    payload: SavedProductRequest, db: Session = Depends(get_db)
) -> SavedProductOut:
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    existing = (
        db.query(SavedProduct)
        .filter(
            SavedProduct.product_id == payload.product_id,
            SavedProduct.session_id == payload.session_id,
        )
        .first()
    )
    if not existing:
        db.add(SavedProduct(product_id=product.id, session_id=payload.session_id))
        db.commit()
    return to_product_out(product)


@router.delete("/{product_id}")
def remove_saved_product(
    product_id: int, session_id: str = "demo-session", db: Session = Depends(get_db)
) -> dict[str, bool]:
    saved = (
        db.query(SavedProduct)
        .filter(
            SavedProduct.product_id == product_id,
            SavedProduct.session_id == session_id,
        )
        .first()
    )
    if saved:
        db.delete(saved)
        db.commit()
    return {"success": True}