from aiogram.fsm.state import State, StatesGroup


class AdminCrudStates(StatesGroup):
    waiting_game_title = State()
    waiting_game_edit_title = State()

    waiting_category_game_id = State()
    waiting_category_title = State()
    waiting_category_edit_title = State()

    waiting_product_category_id = State()
    waiting_product_title = State()
    waiting_product_slug = State()
    waiting_product_description = State()
    waiting_product_edit_title = State()

    waiting_price_product_id = State()
    waiting_price_value = State()


class AdminCatalogStates(AdminCrudStates):
    waiting_broadcast_text = State()
    waiting_promo_code = State()
    waiting_order_search = State()
    waiting_user_search = State()
