from decimal import Decimal

from app.models import Game, Order, Product, User


def main_menu_text(shop_name: str, welcome_text: str) -> str:
    return (
        f'🎮 <b>{shop_name}</b>\n\n'
        f'{welcome_text}\n\n'
        f'💎 <b>Нажми "🛍️ Открыть магазин" для доступа к веб-версии!</b>\n\n'
        f'Или используй кнопки ниже для быстрого доступа:'
    )


def game_caption(game: Game) -> str:
    description = game.description or 'Каталог игровых товаров и подписок.'
    return f'🎮 <b>{game.title}</b>\n\n{description}'


def product_caption(product: Product, price: Decimal, currency: str) -> str:
    description = product.description or 'Безопасный сценарий оформления заказа без паролей от аккаунта.'
    fields = []
    if product.requires_player_id:
        fields.append('player_id')
    if product.requires_nickname:
        fields.append('nickname')
    if product.requires_region:
        fields.append('region')
    if product.requires_screenshot:
        fields.append('screenshot')
    req = ', '.join(fields) if fields else 'не требуются'
    return (
        f'🛍 <b>{product.title}</b>\n\n{description}\n\n'
        f'💸 Цена: <b>{price} {currency}</b>\n'
        f'🚚 Выдача: <code>{product.fulfillment_type}</code>\n'
        f'📝 Поля заказа: {req}'
    )


def cart_caption(subtotal: Decimal, discount: Decimal, total: Decimal, currency: str) -> str:
    return (
        '🛒 <b>Корзина</b>\n\n'
        f'Промежуточный итог: <b>{subtotal} {currency}</b>\n'
        f'Скидка: <b>{discount} {currency}</b>\n'
        f'Итого: <b>{total} {currency}</b>'
    )


def order_card(order: Order) -> str:
    items = '\n'.join(f'• {item.product_title} × {item.quantity} = {item.line_total} {order.currency_code}' for item in order.items)
    return (
        f'📦 <b>{order.order_number}</b>\n'
        f'Статус: <b>{order.status}</b>\n'
        f'Сумма: <b>{order.total_amount} {order.currency_code}</b>\n\n'
        f'{items}'
    )


def profile_text(user: User, orders_count: int, total_spent: Decimal, referral_code: str) -> str:
    return (
        '👤 <b>Профиль</b>\n\n'
        f'ID: <code>{user.telegram_id}</code>\n'
        f'Username: @{user.username or "-"}\n'
        f'Заказов: <b>{orders_count}</b>\n'
        f'Сумма покупок: <b>{total_spent}</b>\n'
        f'Персональная скидка: <b>{user.personal_discount_percent}%</b>\n'
        f'Реферальный код: <code>{referral_code}</code>'
    )
