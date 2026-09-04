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
        {
            "id": 9,
            "name": "Aquapour Daily Gel Moisturizer",
            "description": "A featherlight water-gel moisturizer for oily and combination skin.",
            "price": 299,
            "stock": 25,
            "category": "moisturizer",
            "image_url": "",
        },
        {
            "id": 10,
            "name": "Midnight Ceramide Repair Cream",
            "description": "A rich overnight repair cream with ceramides for very dry, aging skin.",
            "price": 1899,
            "stock": 8,
            "category": "moisturizer",
            "image_url": "",
        },
        {
            "id": 11,
            "name": "Cottonlight SPF 30 Stick",
            "description": "A pocketable SPF 30 mineral stick for quick, no-mess reapplication.",
            "price": 449,
            "stock": 22,
            "category": "sunscreen",
            "image_url": "",
        },
        {
            "id": 12,
            "name": "Dermaseal SPF 70 Glow Fluid",
            "description": "High-protection SPF 70 fluid with a subtle glow finish.",
            "price": 1499,
            "stock": 11,
            "category": "sunscreen",
            "image_url": "",
        },
        {
            "id": 13,
            "name": "Freshdose Niacinamide Serum",
            "description": "A gentle 5% niacinamide serum for reducing excess oil and dullness.",
            "price": 599,
            "stock": 19,
            "category": "serum",
            "image_url": "",
        },
        {
            "id": 14,
            "name": "Radiance Triple-A Serum",
            "description": "A multi-active serum with vitamin C, retinol, and peptides for advanced repair.",
            "price": 2199,
            "stock": 6,
            "category": "serum",
            "image_url": "",
        },
        {
            "id": 15,
            "name": "Morning Dew Cream Cleanser",
            "description": "An ultra-gentle cream cleanser for sensitive, easily-stripped skin.",
            "price": 349,
            "stock": 28,
            "category": "cleanser",
            "image_url": "",
        },
        {
            "id": 16,
            "name": "Claydeep Purge Wash",
            "description": "A clarifying clay wash that controls oil and purges congested pores.",
            "price": 1299,
            "stock": 13,
            "category": "cleanser",
            "image_url": "",
        },
        {
            "id": 17,
            "name": "Softglow Marula Oil",
            "description": "A fast-absorbing marula oil for radiant, non-greasy nourishment.",
            "price": 699,
            "stock": 14,
            "category": "face oil",
            "image_url": "",
        },
        {
            "id": 18,
            "name": "Midnight Botanic Elixir Oil",
            "description": "A botanical blend oil for overnight renewal and improved elasticity.",
            "price": 1999,
            "stock": 7,
            "category": "face oil",
            "image_url": "",
        },
        {
            "id": 19,
            "name": "Minimalist Fresh Kit",
            "description": "A pared-back starter set with cleanser, moisturizer, and SPF.",
            "price": 999,
            "stock": 16,
            "category": "sets",
            "image_url": "",
        },
        {
            "id": 20,
            "name": "Glow Ritual Complete Set",
            "description": "A full 5-step routine set for a complete morning and night ritual.",
            "price": 2599,
            "stock": 5,
            "category": "sets",
            "image_url": "",
        },
        {
            "id": 21,
            "name": "Sheertone Lip Tint",
            "description": "A buildable sheer lip tint with moisturizing cushion.",
            "price": 499,
            "stock": 20,
            "category": "makeup",
            "image_url": "",
        },
        {
            "id": 22,
            "name": "Velvet Matte Powder Set",
            "description": "A two-piece velvet matte powder and brush set for an everyday finish.",
            "price": 1799,
            "stock": 9,
            "category": "makeup",
            "image_url": "",
        },
        {
            "id": 23,
            "name": "Soothfresh Sheet Mask 5-Pack",
            "description": "Hydrating sheet masks with aloe for a quick calming reset.",
            "price": 399,
            "stock": 24,
            "category": "skincare",
            "image_url": "",
        },
        {
            "id": 24,
            "name": "Brighten Renewal Peel Mask",
            "description": "A weekly renewal peel mask that visibly brightens and smooths.",
            "price": 1599,
            "stock": 10,
            "category": "skincare",
            "image_url": "",
        },
        {
            "id": 25,
            "name": "Calmbody Ashwagandha Gummies",
            "description": "Stress-support ashwagandha gummies for a steady daily calm.",
            "price": 899,
            "stock": 18,
            "category": "wellness",
            "image_url": "",
        },
        {
            "id": 26,
            "name": "Unwind Sleep Capsules",
            "description": "Vegan sleep capsules with melatonin for deeper, more restful sleep.",
            "price": 1499,
            "stock": 12,
            "category": "wellness",
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
