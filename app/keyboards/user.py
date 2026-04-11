from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models import Cart, Category, Game, Order, Product
from app.utils.callbacks import CartCb, NavCb
from app.utils.pagination import total_pages



def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    items = [
        ('🎮 Игры', NavCb(target='games').pack()),
        ('🛒 Корзина', NavCb(target='cart').pack()),
        ('📦 Мои заказы', NavCb(target='orders_current').pack()),
        ('🕘 История заказов', NavCb(target='orders_history').pack()),
        ('🎁 Промокод', NavCb(target='promo').pack()),
        ('⭐ Отзывы', NavCb(target='reviews').pack()),
        ('👤 Профиль', NavCb(target='profile').pack()),
        ('🤝 Реферальная система', NavCb(target='ref').pack()),
        ('🆘 Поддержка', NavCb(target='support').pack()),
        ('ℹ️ Информация / Правила', NavCb(target='info').pack()),
    ]
    for text, cb in items:
        builder.button(text=text, callback_data=cb)
    builder.adjust(2)
    return builder.as_markup()



def games_kb(games: list[Game]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for game in games:
        builder.button(text=game.title, callback_data=NavCb(target='game', entity_id=game.id).pack())
    builder.button(text='🏠 Главное меню', callback_data=NavCb(target='home').pack())
    builder.adjust(1)
    return builder.as_markup()



def categories_kb(game_id: int, categories: list[Category]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(text=category.title, callback_data=NavCb(target='category', entity_id=category.id).pack())
    builder.button(text='🔙 К играм', callback_data=NavCb(target='games').pack())
    builder.adjust(1)
    return builder.as_markup()



def products_kb(category_id: int, products: list[Product], page: int, total: int, page_size: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(text=product.title, callback_data=NavCb(target='product', entity_id=product.id, page=page).pack())
    pages = total_pages(total, page_size)
    if page > 1:
        builder.button(text='⬅️', callback_data=NavCb(target='category', entity_id=category_id, page=page - 1).pack())
    builder.button(text=f'{page}/{pages}', callback_data='noop')
    if page < pages:
        builder.button(text='➡️', callback_data=NavCb(target='category', entity_id=category_id, page=page + 1).pack())
    builder.button(text='🔙 К категориям', callback_data=NavCb(target='game_from_category', entity_id=category_id).pack())
    builder.adjust(1, 3, 1)
    return builder.as_markup()



def product_kb(product_id: int, back_category_id: int, page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='➕ Добавить в корзину', callback_data=CartCb(action='add', product_id=product_id).pack())
    builder.button(text='⚡ Купить сразу', callback_data=CartCb(action='buy_now', product_id=product_id).pack())
    builder.button(text='🔙 Назад', callback_data=NavCb(target='category', entity_id=back_category_id, page=page).pack())
    builder.adjust(1)
    return builder.as_markup()



def cart_kb(cart: Cart) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in cart.items:
        builder.button(text=f'➕ {item.product.title}', callback_data=CartCb(action='inc', product_id=item.product_id).pack())
        builder.button(text=f'➖ {item.product.title}', callback_data=CartCb(action='dec', product_id=item.product_id).pack())
        builder.button(text=f'❌ {item.product.title}', callback_data=CartCb(action='del', product_id=item.product_id).pack())
    builder.button(text='🗑 Очистить', callback_data=NavCb(target='cart_clear').pack())
    builder.button(text='🎁 Применить промокод', callback_data=NavCb(target='promo').pack())
    builder.button(text='✅ Оформить заказ', callback_data=NavCb(target='checkout').pack())
    builder.button(text='🏠 Главное меню', callback_data=NavCb(target='home').pack())
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()



def orders_kb(orders: list[Order], back_target: str = 'home') -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for order in orders:
        builder.button(text=f'{order.order_number} · {order.status}', callback_data=NavCb(target='order', entity_id=order.id).pack())
    builder.button(text='🔙 Назад', callback_data=NavCb(target=back_target).pack())
    builder.adjust(1)
    return builder.as_markup()



def order_actions_kb(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='🔁 Повторить заказ', callback_data=NavCb(target='repeat_order', entity_id=order_id).pack())
    builder.button(text='⭐ Оставить отзыв', callback_data=NavCb(target='review_create', entity_id=order_id).pack())
    builder.button(text='🔙 К заказам', callback_data=NavCb(target='orders_current').pack())
    builder.adjust(1)
    return builder.as_markup()
