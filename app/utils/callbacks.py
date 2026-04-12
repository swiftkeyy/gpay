from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class NavCb(CallbackData, prefix="nav"):
    target: str
    page: int | None = None
    entity_id: int | None = None
    extra: str | None = None


class CartCb(CallbackData, prefix="cart"):
    action: str
    item_id: int | None = None
    product_id: int | None = None


class AdminActionCb(CallbackData, prefix="adm"):
    section: str
    action: str
    entity_id: int | None = None
    page: int | None = None


class AdminCb(CallbackData, prefix="adm"):
    section: str
    action: str
    entity_id: int | None = None
    page: int | None = None
