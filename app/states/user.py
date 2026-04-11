from aiogram.fsm.state import State, StatesGroup


class CheckoutStates(StatesGroup):
    collecting_fields = State()
    entering_promo = State()
    leaving_review = State()
    contacting_support = State()
