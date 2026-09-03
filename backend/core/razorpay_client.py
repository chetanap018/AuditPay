from __future__ import annotations

import os
from importlib import import_module
from typing import Any


def get_client() -> Any:
    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:
        raise RuntimeError("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be set in the environment.")

    try:
        razorpay = import_module("razorpay")
    except ImportError as exc:
        raise RuntimeError("The razorpay package must be installed.") from exc

    return razorpay.Client(auth=(key_id, key_secret))
