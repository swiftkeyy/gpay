from __future__ import annotations

import hashlib


def build_checkout_key(user_id: int, cart_id: int, cart_version: int) -> str:
    return hashlib.sha256(f'{user_id}:{cart_id}:{cart_version}'.encode()).hexdigest()[:32]
