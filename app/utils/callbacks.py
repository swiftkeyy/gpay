from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class NavCb(CallbackData, prefix="nav"):
    target: str
    entity_id: int | None = None
    page: int | None = None


class AdminCb(CallbackData, prefix="adm"):
    section: str
    action: str
    entity_id: int | None = None
    page: int | None = None
