from aiogram.fsm.state import State, StatesGroup


class CheckoutStates(StatesGroup):
    collecting_fields = State()
    entering_promo = State()
    leaving_review = State()
    contacting_support = State()


class SellerStates(StatesGroup):
    waiting_shop_name = State()
    waiting_shop_description = State()
    waiting_lot_title = State()
    waiting_lot_description = State()
    waiting_lot_price = State()
    waiting_stock_items = State()
    waiting_withdrawal_amount = State()
    waiting_withdrawal_details = State()


class DealStates(StatesGroup):
    waiting_message = State()
    waiting_dispute_reason = State()
    waiting_delivery_data = State()


class LotCreationStates(StatesGroup):
    selecting_product = State()
    entering_title = State()
    entering_description = State()
    entering_price = State()
    selecting_delivery_type = State()
    entering_stock_items = State()
