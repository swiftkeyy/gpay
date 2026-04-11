from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models import Category, Game, Order, Product, PromoCode, User
from app.utils.callbacks import AdminCb, NavCb



def admin_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    sections = [
        ('📦 Заказы', 'orders'), ('🛍 Товары', 'products'), ('🎮 Игры', 'games'), ('🗂 Категории', 'categories'),
        ('💸 Цены', 'prices'), ('🖼 Картинки', 'images'), ('👥 Пользователи', 'users'), ('🚫 Блокировки', 'blocks'),
        ('🎁 Промокоды', 'promos'), ('⭐ Отзывы', 'reviews'), ('🤝 Рефералка', 'refs'), ('📢 Рассылка', 'broadcasts'),
        ('📊 Статистика', 'stats'), ('⚙️ Настройки', 'settings'), ('🧾 Логи', 'logs'), ('👮 Админы', 'admins'),
    ]
    for text, section in sections:
        builder.button(text=text, callback_data=AdminCb(section=section, action='list').pack())
    builder.adjust(2)
    return builder.as_markup()



def games_admin_kb(games: list[Game]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='➕ Добавить игру', callback_data=AdminCb(section='games', action='create').pack())
    for game in games:
        builder.button(text=f'✏️ {game.title}', callback_data=AdminCb(section='games', action='view', entity_id=game.id).pack())
    builder.button(text='🔙 В админку', callback_data=NavCb(target='admin_home').pack())
    builder.adjust(1)
    return builder.as_markup()



def game_actions_kb(game_id: int, active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='✏️ Изменить название', callback_data=AdminCb(section='games', action='edit', entity_id=game_id).pack())
    builder.button(text='🔁 Вкл/Выкл', callback_data=AdminCb(section='games', action='toggle', entity_id=game_id).pack())
    builder.button(text='🗑 Удалить', callback_data=AdminCb(section='games', action='delete', entity_id=game_id).pack())
    builder.button(text='🔙 К играм', callback_data=AdminCb(section='games', action='list').pack())
    builder.adjust(1)
    return builder.as_markup()



def categories_admin_kb(categories: list[Category]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='➕ Добавить категорию', callback_data=AdminCb(section='categories', action='create').pack())
    for category in categories:
        builder.button(text=f'✏️ {category.title}', callback_data=AdminCb(section='categories', action='view', entity_id=category.id).pack())
    builder.button(text='🔙 В админку', callback_data=NavCb(target='admin_home').pack())
    builder.adjust(1)
    return builder.as_markup()



def products_admin_kb(products: list[Product]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='➕ Добавить товар', callback_data=AdminCb(section='products', action='create').pack())
    for product in products:
        builder.button(text=f'✏️ {product.title}', callback_data=AdminCb(section='products', action='view', entity_id=product.id).pack())
    builder.button(text='🔙 В админку', callback_data=NavCb(target='admin_home').pack())
    builder.adjust(1)
    return builder.as_markup()



def product_actions_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='✏️ Изменить товар', callback_data=AdminCb(section='products', action='edit', entity_id=product_id).pack())
    builder.button(text='💸 Изменить цену', callback_data=AdminCb(section='prices', action='set', entity_id=product_id).pack())
    builder.button(text='🗑 Удалить', callback_data=AdminCb(section='products', action='delete', entity_id=product_id).pack())
    builder.button(text='🔙 К товарам', callback_data=AdminCb(section='products', action='list').pack())
    builder.adjust(1)
    return builder.as_markup()



def orders_admin_kb(orders: list[Order]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for order in orders:
        builder.button(text=f'{order.order_number} · {order.status}', callback_data=AdminCb(section='orders', action='view', entity_id=order.id).pack())
    builder.button(text='🔙 В админку', callback_data=NavCb(target='admin_home').pack())
    builder.adjust(1)
    return builder.as_markup()



def order_admin_actions_kb(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for action, label in [('paid', '✅ Подтвердить оплату'), ('processing', '🛠 В обработку'), ('fulfilled', '🚚 Выдан'), ('completed', '🏁 Завершён'), ('canceled', '⛔ Отменить')]:
        builder.button(text=label, callback_data=AdminCb(section='orders', action=action, entity_id=order_id).pack())
    builder.button(text='🔙 К заказам', callback_data=AdminCb(section='orders', action='list').pack())
    builder.adjust(1)
    return builder.as_markup()
