from aiogram.fsm.state import State, StatesGroup


class AdminCatalogStates(StatesGroup):
    waiting_game_title = State()
    waiting_game_description = State()
    waiting_category_title = State()
    waiting_product_title = State()
    waiting_product_description = State()
    waiting_price_value = State()
    waiting_setting_value = State()
    waiting_broadcast_text = State()
    waiting_promo_code = State()
