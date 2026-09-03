from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.db.models import Product
from backend.db.session import SessionLocal, init_db


def build_seed_catalog() -> list[dict[str, Any]]:
    return [
        {
            "id": 1,
            "name": "Cloudmilk Barrier Cream",
            "description": "A soothing moisturizer for dry skin with ceramides and oat extract.",
            "price": 649,
            "stock": 18,
            "category": "moisturizer",
            "image_url": "",
        },
        {
            "id": 2,
            "name": "Dewdrop Daily Sun Shield",
            "description": "Lightweight sunscreen made for everyday use and reapplication ease.",
            "price": 799,
            "stock": 21,
            "category": "sunscreen",
            "image_url": "",
        },
        {
            "id": 3,
            "name": "Glowcore Vitamin C Serum",
            "description": "Brightening serum with antioxidant support for tired morning skin.",
            "price": 899,
            "stock": 15,
            "category": "serum",
            "image_url": "",
        },
        {
            "id": 4,
            "name": "Petal Reset Cleanser",
            "description": "A low-foam gel cleanser that removes sunscreen and buildup without tightness.",
            "price": 549,
            "stock": 32,
            "category": "cleanser",
            "image_url": "",
        },
        {
            "id": 5,
            "name": "Velvet Bloom Face Oil",
            "description": "A nourishing oil suited for evenings and dry patches around the cheeks.",
            "price": 940,
            "stock": 10,
            "category": "face oil",
            "image_url": "",
        },
        {
            "id": 6,
            "name": "Hydra Duo Starter Set",
            "description": "A balanced routine set with cleanser, serum, and moisturizer.",
            "price": 1499,
            "stock": 7,
            "category": "sets",
            "image_url": "",
        },
        {
            "id": 7,
            "name": "Rose Tint Daily Tint",
            "description": "Buildable, soft-focus makeup with skin-friendly hydration.",
            "price": 1199,
            "stock": 12,
            "category": "makeup",
            "image_url": "",
        },
        {
            "id": 8,
            "name": "Calmwater Overnight Mask",
            "description": "A rich overnight treatment designed for dry and stressed skin.",
            "price": 799,
            "stock": 9,
            "category": "skincare",
            "image_url": "",
        },
    ]


def seed_catalog() -> None:
    init_db()
    db: Session = SessionLocal()
    try:
        product_count = db.query(Product).count()
        if product_count > 0:
            return

        for item in build_seed_catalog():
            db.add(Product(**item))

        db.commit()
    finally:
        db.close()
