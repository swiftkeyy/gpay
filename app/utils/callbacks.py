from aiogram.filters.callback_data import CallbackData


class NavCb(CallbackData, prefix='n'):
    target: str
    entity_id: int = 0
    page: int = 1


class CartCb(CallbackData, prefix='c'):
    action: str
    product_id: int


class AdminCb(CallbackData, prefix='a'):
    section: str
    action: str
    entity_id: int = 0
    page: int = 1


class ConfirmCb(CallbackData, prefix='y'):
    action: str
    entity_id: int
    token: str
