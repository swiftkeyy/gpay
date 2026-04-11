# Game Pay full source code

## .env.example

```example

BOT_TOKEN=replace_me
BOT_USERNAME=game_pay_bot
APP_ENV=dev
LOG_LEVEL=INFO
DB_HOST=db
DB_PORT=5432
DB_NAME=game_pay
DB_USER=game_pay
DB_PASSWORD=game_pay
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
SUPER_ADMIN_TELEGRAM_ID=111111111
SECOND_ADMIN_TELEGRAM_ID=222222222
POSTGRES_INIT_SEED=true


```

## Dockerfile

```

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["bash", "-lc", "alembic upgrade head && python seed.py && python -m app.main"]


```

## PROJECT_TREE.txt

```txt

./.env.example
./Dockerfile
./PROJECT_TREE.txt
./README.md
./__pycache__/seed.cpython-313.pyc
./alembic/versions/__init__.py
./app/__init__.py
./app/__pycache__/__init__.cpython-313.pyc
./app/__pycache__/main.cpython-313.pyc
./app/core/__init__.py
./app/core/config.py
./app/core/logging.py
./app/db/__init__.py
./app/db/base.py
./app/db/session.py
./app/filters/__init__.py
./app/filters/admin_role.py
./app/handlers/__init__.py
./app/keyboards/__init__.py
./app/keyboards/admin.py
./app/keyboards/common.py
./app/keyboards/user.py
./app/main.py
./app/middlewares/__init__.py
./app/middlewares/block.py
./app/middlewares/db.py
./app/middlewares/rate_limit.py
./app/middlewares/user_context.py
./app/models/__init__.py
./app/models/entities.py
./app/models/enums.py
./app/repositories/__init__.py
./app/repositories/base.py
./app/repositories/cart.py
./app/repositories/catalog.py
./app/repositories/orders.py
./app/repositories/promo.py
./app/repositories/settings.py
./app/repositories/users.py
./app/services/__init__.py
./app/services/audit.py
./app/services/broadcast.py
./app/services/cart.py
./app/services/media.py
./app/services/orders.py
./app/services/payment.py
./app/services/pricing.py
./app/services/promo.py
./app/services/rbac.py
./app/services/referral.py
./app/services/settings.py
./app/states/__init__.py
./app/states/admin.py
./app/states/user.py
./app/templates/__init__.py
./app/utils/__init__.py
./app/utils/callbacks.py
./app/utils/idempotency.py
./app/utils/pagination.py
./app/utils/texts.py
./app/utils/validators.py
./docker-compose.yml
./requirements.txt
./seed.py


```

## README.md

```md

# Game Pay

Game Pay — production-ready Telegram marketplace bot for gaming goods with inline-only UX, layered architecture, async SQLAlchemy, PostgreSQL, Redis FSM, RBAC, audit logging, dynamic order fields, promo codes, referrals, and admin panel.

## Stack
- Python 3.12
- aiogram 3.x
- PostgreSQL
- SQLAlchemy 2.x async
- Redis
- pydantic-settings
- Docker / docker-compose

## Run with Docker
```bash
cp .env.example .env
# set BOT_TOKEN and admin telegram IDs
docker compose up --build
```

## Local run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed.py
python -m app.main
```

## What is seeded
- shop name: Game Pay
- games: Brawl Stars, Standoff 2
- categories: Валюта, Подписки
- products:
  - Brawl Stars: Gems 30 / 80 / 170, Brawl Pass
  - Standoff 2: Gold 100 / 500 / 1000, Battle Pass
- 2 admins from `.env`
- default media placeholders
- welcome text, rules, support contact, payment methods

## Security model
- no account passwords are requested, stored, or logged
- Brawl Stars uses safe manual / official redirect style flow only
- Standoff 2 uses storefront + manual/admin processed flow only
- dynamic order fields support player_id / nickname / region / email / comment / screenshot note / admin note
- payment is abstracted and currently implemented as manual payment provider
- admin actions are logged into `audit_logs`
- blocking, promo restrictions, idempotent checkout key, and rate limiting are included

## Architecture
```text
app/
  core/         config, logging
  db/           base and async session
  models/       SQLAlchemy entities and enums
  repositories/ DB access layer
  services/     business logic
  handlers/     aiogram routers for user/admin
  keyboards/    inline keyboard factories
  middlewares/  db session, user registration, blocking, rate limit
  filters/      RBAC admin permission filter
  states/       FSM states
  utils/        callback factories, validators, pagination, texts
```

## Business rules implemented
- all primary user navigation is inline-based
- catalog is database-driven, no hardcoded assortment in bot logic
- new games/categories/products appear automatically when added to DB/admin flow
- pricing is handled by separate pricing service with discount priority support
- dynamic order fields are driven by `products.extra_fields_schema_json`
- manual payment and status confirmation by admin are implemented

## How to add a new game
1. Open `/admin`
2. Go to `🎮 Игры`
3. Click add game and send title
4. Add/edit description, image and active flag in DB/admin flow
5. Create categories and products for that game

## How to add a new category
1. Open `/admin`
2. Go to `🗂 Категории`
3. Create category and link it to a game in DB/admin flow
4. Set `is_active=true`

## How to add a new product
1. Open `/admin`
2. Go to `🛍 Товары`
3. Create product for game/category
4. Set fulfillment type and required order fields
5. Add current price in `💸 Цены`

## How to change price
1. Open `/admin`
2. Go to product card
3. Click `💸 Изменить цену`
4. Send new price value

## How to change image
- Upload Telegram file id into `media_files`
- Link `image_id` in `games`, `categories`, or `products`
- The media layer falls back to text if media is unavailable

## How to assign administrator
1. Create or locate user in `users`
2. Insert row into `admins`
3. Set role: `super_admin` or `admin`
4. Optionally enable `can_manage_categories`

## How to enable/disable a game
- In admin game card use `🔁 Вкл/Выкл`
- Or update `games.is_active`

## How to change welcome and rules texts
- Update `bot_settings` keys:
  - `welcome_text`
  - `rules_text`
  - `support_contact`
  - `payment_methods_text`
  - `faq_text`

## DB initialization
`seed.py` creates tables through SQLAlchemy metadata and fills initial data. This project includes SQLAlchemy-driven initialization instead of hand-written hardcoded SQL migrations.

## Notes
- The admin panel is inline-first. Some creation/edit steps request text messages after an inline action to keep callback payloads short and maintainable.
- Callback data uses compact prefixes: `n`, `c`, `a`, `y`.
- For production, place the bot behind process supervision and configure proper secrets management.


```

## alembic/versions/__init__.py

```py



```

## app/__init__.py

```py



```

## app/core/__init__.py

```py



```

## app/core/config.py

```py

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    bot_token: str = Field(alias='BOT_TOKEN')
    bot_username: str = Field(alias='BOT_USERNAME')
    app_env: str = Field(default='dev', alias='APP_ENV')
    log_level: str = Field(default='INFO', alias='LOG_LEVEL')

    db_host: str = Field(alias='DB_HOST')
    db_port: int = Field(alias='DB_PORT')
    db_name: str = Field(alias='DB_NAME')
    db_user: str = Field(alias='DB_USER')
    db_password: str = Field(alias='DB_PASSWORD')

    redis_host: str = Field(alias='REDIS_HOST')
    redis_port: int = Field(alias='REDIS_PORT')
    redis_db: int = Field(default=0, alias='REDIS_DB')

    super_admin_telegram_id: int = Field(alias='SUPER_ADMIN_TELEGRAM_ID')
    second_admin_telegram_id: int = Field(alias='SECOND_ADMIN_TELEGRAM_ID')
    postgres_init_seed: bool = Field(default=True, alias='POSTGRES_INIT_SEED')

    @property
    def database_url(self) -> str:
        return (
            f'postgresql+asyncpg://{self.db_user}:{self.db_password}'
            f'@{self.db_host}:{self.db_port}/{self.db_name}'
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f'postgresql://{self.db_user}:{self.db_password}'
            f'@{self.db_host}:{self.db_port}/{self.db_name}'
        )

    @property
    def redis_url(self) -> str:
        return f'redis://{self.redis_host}:{self.redis_port}/{self.redis_db}'


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


```

## app/core/logging.py

```py

import logging
import sys

from app.core.config import get_settings


def setup_logging() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
    )


```

## app/db/__init__.py

```py



```

## app/db/base.py

```py

from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + 's'


```

## app/db/session.py

```py

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


```

## app/filters/__init__.py

```py



```

## app/filters/admin_role.py

```py

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from app.repositories.users import AdminRepository
from app.services.rbac import RBACService


class AdminPermissionFilter(BaseFilter):
    def __init__(self, permission: str):
        self.permission = permission
        self.rbac = RBACService()

    async def __call__(self, event: Message | CallbackQuery, session) -> bool:
        telegram_id = event.from_user.id
        admin = await AdminRepository(session).get_by_telegram_id(telegram_id)
        if not admin:
            return False
        return self.rbac.has_permission(admin.role, self.permission, can_manage_categories=admin.can_manage_categories)


```

## app/handlers/__init__.py

```py



```

## app/handlers/admin/__init__.py

```py



```

## app/handlers/admin/broadcasts.py

```py

from __future__ import annotations

from aiogram import F, Router
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin_role import AdminPermissionFilter
from app.models.enums import BroadcastStatus
from app.repositories.settings import BroadcastRepository
from app.services.broadcast import BroadcastService
from app.states.admin import AdminCatalogStates
from app.utils.callbacks import AdminCb

router = Router(name='admin_broadcasts')


@router.callback_query(AdminCb.filter(F.section == 'broadcasts'), AdminPermissionFilter('broadcasts.manage'))
async def broadcast_entry(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession, state: FSMContext) -> None:
    broadcasts = await BroadcastRepository(session).list(limit=30)
    lines = [f'• {b.title} | {b.status}' for b in broadcasts]
    await callback.message.edit_text('📢 <b>Рассылки</b>\n\n' + ('\n'.join(lines) or 'Пока нет рассылок.'), parse_mode='HTML')
    await callback.message.answer('Введите текст новой рассылки сообщением.')
    await state.set_state(AdminCatalogStates.waiting_broadcast_text)
    await callback.answer()


@router.message(AdminCatalogStates.waiting_broadcast_text, AdminPermissionFilter('broadcasts.manage'))
async def broadcast_create(message: Message, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    repo = BroadcastRepository(session)
    item = await repo.create(title='Broadcast', text=message.text or '', status=BroadcastStatus.DRAFT)
    sent = await BroadcastService(session).send(bot, item)
    await state.clear()
    await message.answer(f'Рассылка отправлена. Получателей: {sent}')


```

## app/handlers/admin/catalog.py

```py

from __future__ import annotations

from decimal import Decimal
import secrets

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin_role import AdminPermissionFilter
from app.keyboards.admin import (
    categories_admin_kb,
    game_actions_kb,
    games_admin_kb,
    product_actions_kb,
    products_admin_kb,
)
from app.keyboards.common import confirm_keyboard
from app.models import Category, Game, Price, Product
from app.models.enums import AuditAction, EntityType, FulfillmentType
from app.repositories.catalog import CategoryRepository, GameRepository, ProductRepository
from app.services.audit import AuditService
from app.states.admin import AdminCatalogStates
from app.utils.callbacks import AdminCb, ConfirmCb, NavCb
from app.utils.validators import ValidationError, validate_non_empty, validate_price

router = Router(name='admin_catalog')


@router.callback_query(AdminCb.filter(F.section == 'games'), AdminPermissionFilter('games.manage'))
async def admin_games(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession, state: FSMContext) -> None:
    repo = GameRepository(session)
    if callback_data.action == 'list':
        games = await repo.list(limit=100)
        await callback.message.edit_text('🎮 <b>Игры</b>', reply_markup=games_admin_kb(games), parse_mode='HTML')
    elif callback_data.action == 'create':
        await state.set_state(AdminCatalogStates.waiting_game_title)
        await callback.message.answer('Введите название новой игры сообщением.')
    elif callback_data.action == 'view':
        game = await repo.get(callback_data.entity_id)
        if not game:
            await callback.answer('Игра не найдена.', show_alert=True)
            return
        text = f'🎮 <b>{game.title}</b>\n\nSlug: <code>{game.slug}</code>\nАктивна: {game.is_active}'
        await callback.message.edit_text(text, reply_markup=game_actions_kb(game.id, game.is_active), parse_mode='HTML')
    elif callback_data.action == 'toggle':
        game = await repo.get(callback_data.entity_id)
        if game:
            old = {'is_active': game.is_active}
            game.is_active = not game.is_active
            await AuditService(session).log(
                action=AuditAction.UPDATE,
                entity_type=EntityType.GAME,
                entity_id=game.id,
                old_values=old,
                new_values={'is_active': game.is_active},
            )
            await callback.answer('Статус игры обновлён.')
            await admin_games(callback, AdminCb(section='games', action='view', entity_id=game.id), session, state)
            return
    elif callback_data.action == 'delete':
        token = secrets.token_hex(4)
        await state.update_data(confirm_delete_game=token)
        await callback.message.answer('Подтвердите удаление игры.', reply_markup=confirm_keyboard('game_delete', callback_data.entity_id, token, 'admin_home'))
    await callback.answer()


@router.message(AdminCatalogStates.waiting_game_title, AdminPermissionFilter('games.manage'))
async def create_game(message: Message, session: AsyncSession, state: FSMContext) -> None:
    title = validate_non_empty(message.text or '', 'title')
    slug = title.lower().replace(' ', '_').replace('-', '_')[:64]
    game = await GameRepository(session).create(title=title, slug=slug, description='Новое описание игры', is_active=True)
    await AuditService(session).log(
        action=AuditAction.CREATE,
        entity_type=EntityType.GAME,
        entity_id=game.id,
        new_values={'title': game.title, 'slug': game.slug},
    )
    await state.clear()
    await message.answer(f'Игра создана: {game.title}')


@router.callback_query(ConfirmCb.filter(F.action == 'game_delete'), AdminPermissionFilter('games.manage'))
async def confirm_delete_game(callback: CallbackQuery, callback_data: ConfirmCb, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    if data.get('confirm_delete_game') != callback_data.token:
        await callback.answer('Подтверждение устарело.', show_alert=True)
        return
    game = await GameRepository(session).get(callback_data.entity_id)
    if not game:
        await callback.answer('Игра не найдена.', show_alert=True)
        return
    game.is_deleted = True
    game.is_active = False
    await AuditService(session).log(action=AuditAction.DELETE, entity_type=EntityType.GAME, entity_id=game.id, old_values={'title': game.title})
    await state.clear()
    await callback.message.edit_text('Игра помечена как удалённая.')
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == 'categories'), AdminPermissionFilter('categories.manage'))
async def admin_categories(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession) -> None:
    categories = await CategoryRepository(session).list(limit=200)
    await callback.message.edit_text('🗂 <b>Категории</b>', reply_markup=categories_admin_kb(categories), parse_mode='HTML')
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == 'products'), AdminPermissionFilter('products.manage'))
async def admin_products(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession) -> None:
    repo = ProductRepository(session)
    if callback_data.action == 'list':
        products = await repo.list(limit=200)
        await callback.message.edit_text('🛍 <b>Товары</b>', reply_markup=products_admin_kb(products), parse_mode='HTML')
    elif callback_data.action == 'view':
        product = await repo.get_full(callback_data.entity_id)
        if not product:
            await callback.answer('Товар не найден.', show_alert=True)
            return
        text = (
            f'🛍 <b>{product.title}</b>\n'
            f'Slug: <code>{product.slug}</code>\n'
            f'Выдача: <code>{product.fulfillment_type}</code>\n'
            f'Активен: {product.is_active}'
        )
        await callback.message.edit_text(text, reply_markup=product_actions_kb(product.id), parse_mode='HTML')
    await callback.answer()


```

## app/handlers/admin/misc.py

```py

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin_role import AdminPermissionFilter
from app.keyboards.admin import admin_menu_kb
from app.models import Admin, BotSetting, PromoCode, User
from app.models.enums import AdminRole, AuditAction, EntityType, PromoType
from app.repositories.settings import BotSettingRepository
from app.repositories.users import AdminRepository, UserRepository
from app.services.audit import AuditService
from app.states.admin import AdminCatalogStates
from app.utils.callbacks import AdminCb, NavCb
from app.utils.validators import ValidationError, validate_non_empty

router = Router(name='admin_misc')


@router.callback_query(NavCb.filter(F.target == 'admin_home'), AdminPermissionFilter('orders.view'))
async def admin_home(callback: CallbackQuery) -> None:
    await callback.message.edit_text('👮 <b>Админ-панель Game Pay</b>', reply_markup=admin_menu_kb(), parse_mode='HTML')
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == 'settings'), AdminPermissionFilter('settings.manage'))
async def admin_settings(callback: CallbackQuery, session: AsyncSession) -> None:
    repo = BotSettingRepository(session)
    settings = await repo.list(limit=100)
    lines = [f'• <code>{item.key}</code> = {item.value}' for item in settings]
    await callback.message.edit_text('⚙️ <b>Настройки</b>\n\n' + '\n'.join(lines), parse_mode='HTML')
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == 'users'), AdminPermissionFilter('users.view'))
async def admin_users(callback: CallbackQuery, session: AsyncSession) -> None:
    users = await UserRepository(session).list(limit=30)
    text = '👥 <b>Пользователи</b>\n\n' + '\n'.join(f'• {u.id} | {u.telegram_id} | @{u.username or "-"}' for u in users)
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == 'blocks'), AdminPermissionFilter('users.block'))
async def admin_blocks(callback: CallbackQuery, session: AsyncSession) -> None:
    users = list(await session.scalars(select(User).where(User.is_blocked.is_(True)).limit(50)))
    text = '🚫 <b>Блокировки</b>\n\n' + ('\n'.join(f'• {u.telegram_id}: {u.block_reason}' for u in users) or 'Нет блокировок.')
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == 'admins'), AdminPermissionFilter('admins.manage'))
async def admin_admins(callback: CallbackQuery, session: AsyncSession) -> None:
    admins = await AdminRepository(session).list(limit=30)
    text = '👮 <b>Админы</b>\n\n' + '\n'.join(f'• user_id={a.user_id} | role={a.role}' for a in admins)
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == 'logs'), AdminPermissionFilter('logs.view'))
async def admin_logs(callback: CallbackQuery, session: AsyncSession) -> None:
    from app.repositories.settings import AuditLogRepository

    logs = await AuditLogRepository(session).list(limit=30)
    text = '🧾 <b>Логи</b>\n\n' + '\n'.join(
        f'• {log.created_at:%Y-%m-%d %H:%M} | {log.action} | {log.entity_type}:{log.entity_id}' for log in logs
    )
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


@router.callback_query(AdminCb.filter(F.section == 'stats'), AdminPermissionFilter('orders.view'))
async def admin_stats(callback: CallbackQuery, session: AsyncSession) -> None:
    users_count = int(await session.scalar(select(func.count()).select_from(User)) or 0)
    orders_count = int(await session.scalar(select(func.count()).select_from(__import__('app.models', fromlist=['Order']).Order)) or 0)
    revenue = await session.scalar(select(func.coalesce(func.sum(__import__('app.models', fromlist=['Order']).Order.total_amount), 0)))
    text = f'📊 <b>Статистика</b>\n\nПользователей: {users_count}\nЗаказов: {orders_count}\nОборот: {revenue}'
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


```

## app/handlers/admin/orders.py

```py

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin_role import AdminPermissionFilter
from app.keyboards.admin import order_admin_actions_kb, orders_admin_kb
from app.models.enums import AuditAction, EntityType, OrderStatus
from app.repositories.orders import OrderRepository
from app.services.audit import AuditService
from app.services.orders import OrderService
from app.utils.callbacks import AdminCb
from app.utils.texts import order_card

router = Router(name='admin_orders')


@router.callback_query(AdminCb.filter(F.section == 'orders'), AdminPermissionFilter('orders.view'))
async def admin_orders(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession) -> None:
    repo = OrderRepository(session)
    if callback_data.action == 'list':
        orders = await repo.list_recent(limit=100)
        await callback.message.edit_text('📦 <b>Заказы</b>', reply_markup=orders_admin_kb(orders), parse_mode='HTML')
    elif callback_data.action == 'view':
        order = await repo.get_full(callback_data.entity_id)
        if not order:
            await callback.answer('Заказ не найден.', show_alert=True)
            return
        await callback.message.edit_text(order_card(order), reply_markup=order_admin_actions_kb(order.id), parse_mode='HTML')
    else:
        order = await repo.get_full(callback_data.entity_id)
        if not order:
            await callback.answer('Заказ не найден.', show_alert=True)
            return
        status = OrderStatus(callback_data.action)
        await OrderService(session).change_status(order=order, status=status, actor_user_id=None, actor_label='admin')
        await AuditService(session).log(
            action=AuditAction.STATUS_CHANGE,
            entity_type=EntityType.DEFAULT,
            entity_id=order.id,
            old_values={'status': str(order.status)},
            new_values={'status': str(status)},
        )
        await callback.answer('Статус заказа обновлён.')
        await callback.message.edit_text(order_card(order), reply_markup=order_admin_actions_kb(order.id), parse_mode='HTML')
        return
    await callback.answer()


```

## app/handlers/admin/panel.py

```py

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin_role import AdminPermissionFilter
from app.keyboards.admin import admin_menu_kb

router = Router(name='admin_panel')
router.message.filter(AdminPermissionFilter('orders.view'))


@router.message(Command('admin'))
async def admin_panel(message: Message) -> None:
    await message.answer('👮 <b>Админ-панель Game Pay</b>', reply_markup=admin_menu_kb(), parse_mode='HTML')


```

## app/handlers/admin/prices.py

```py

from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin_role import AdminPermissionFilter
from app.models import Price
from app.repositories.catalog import ProductRepository
from app.states.admin import AdminCatalogStates
from app.utils.callbacks import AdminCb
from app.utils.validators import validate_price

router = Router(name='admin_prices')


@router.callback_query(AdminCb.filter(F.section == 'prices'), AdminPermissionFilter('prices.manage'))
async def price_set_start(callback: CallbackQuery, callback_data: AdminCb, state: FSMContext) -> None:
    if callback_data.action == 'set':
        await state.set_state(AdminCatalogStates.waiting_price_value)
        await state.update_data(price_product_id=callback_data.entity_id)
        await callback.message.answer('Введите новую цену сообщением, например 199.00')
    await callback.answer()


@router.message(AdminCatalogStates.waiting_price_value, AdminPermissionFilter('prices.manage'))
async def price_set_finish(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    product_id = data.get('price_product_id')
    product = await ProductRepository(session).get(product_id)
    if not product:
        await message.answer('Товар не найден.')
        await state.clear()
        return
    value = Decimal(validate_price(message.text or '0'))
    session.add(Price(product_id=product.id, base_price=value, discounted_price=value, currency_code='RUB', is_active=True))
    await state.clear()
    await message.answer(f'Цена для {product.title} обновлена: {value} RUB')


```

## app/handlers/admin/promos.py

```py

from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin_role import AdminPermissionFilter
from app.models import PromoCode
from app.models.enums import PromoType
from app.repositories.promo import PromoCodeRepository
from app.states.admin import AdminCatalogStates
from app.utils.callbacks import AdminCb

router = Router(name='admin_promos')


@router.callback_query(AdminCb.filter(F.section == 'promos'), AdminPermissionFilter('promos.manage'))
async def promos(callback: CallbackQuery, callback_data: AdminCb, session: AsyncSession, state: FSMContext) -> None:
    repo = PromoCodeRepository(session)
    if callback_data.action == 'list':
        promos = await repo.list(limit=50)
        text = '🎁 <b>Промокоды</b>\n\n' + '\n'.join(f'• {p.code} | {p.promo_type} | {p.value}' for p in promos)
        text += '\n\nНажмите кнопку ниже, чтобы создать новый промокод.'
        await callback.message.edit_text(text, parse_mode='HTML')
        await callback.message.answer('Для создания введите сообщением: CODE;title;percent|fixed;value')
        await state.set_state(AdminCatalogStates.waiting_promo_code)
    await callback.answer()


@router.message(AdminCatalogStates.waiting_promo_code, AdminPermissionFilter('promos.manage'))
async def promo_create(message: Message, session: AsyncSession, state: FSMContext) -> None:
    try:
        code, title, promo_type, value = [part.strip() for part in (message.text or '').split(';', maxsplit=3)]
    except ValueError:
        await message.answer('Формат: CODE;title;percent|fixed;value')
        return
    promo = await PromoCodeRepository(session).create(
        code=code.upper(),
        title=title,
        promo_type=PromoType.PERCENT if promo_type == 'percent' else PromoType.FIXED,
        value=Decimal(value),
        is_enabled=True,
    )
    await state.clear()
    await message.answer(f'Промокод создан: {promo.code}')


```

## app/handlers/user/__init__.py

```py



```

## app/handlers/user/cart.py

```py

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.user import cart_kb
from app.models import User
from app.repositories.catalog import ProductRepository
from app.services.cart import CartService
from app.services.promo import PromoService, PromoValidationError
from app.states.user import CheckoutStates
from app.utils.callbacks import CartCb, NavCb
from app.utils.idempotency import build_checkout_key
from app.utils.texts import cart_caption

router = Router(name='user_cart')


async def render_cart(callback_or_message, session: AsyncSession, db_user: User) -> None:
    cart_service = CartService(session)
    cart = await cart_service.get_cart(db_user.id)
    if not cart.items:
        text = '🛒 <b>Корзина пуста.</b>'
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.message.edit_text(text, parse_mode='HTML')
            await callback_or_message.answer()
        else:
            await callback_or_message.answer(text, parse_mode='HTML')
        return
    promo = None
    if cart.promo_code_id:
        promo = await PromoService(session).repo.get(cart.promo_code_id)
    totals = await cart_service.compute_totals(cart, db_user, promo)
    lines = [f'• {item.product.title} × {item.quantity}' for item in cart.items]
    text = cart_caption(totals.subtotal, totals.discount, totals.total, totals.currency_code) + '\n\n' + '\n'.join(lines)
    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.message.edit_text(text, reply_markup=cart_kb(cart), parse_mode='HTML')
        await callback_or_message.answer()
    else:
        await callback_or_message.answer(text, reply_markup=cart_kb(cart), parse_mode='HTML')


@router.callback_query(NavCb.filter(F.target == 'cart'))
async def open_cart(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await render_cart(callback, session, db_user)


@router.callback_query(CartCb.filter())
async def cart_actions(callback: CallbackQuery, callback_data: CartCb, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    repo = ProductRepository(session)
    product = await repo.get_full(callback_data.product_id)
    cart_service = CartService(session)
    if callback_data.action == 'add' and product:
        await cart_service.add_item(db_user.id, product)
        await callback.answer('Товар добавлен в корзину.')
    elif callback_data.action == 'buy_now' and product:
        await cart_service.clear(db_user.id)
        await cart_service.add_item(db_user.id, product)
        await callback.answer('Товар добавлен. Переходим к оформлению.')
        await start_checkout(callback, session, db_user, state)
        return
    elif callback_data.action == 'inc':
        await cart_service.change_quantity(db_user.id, callback_data.product_id, 1)
    elif callback_data.action == 'dec':
        await cart_service.change_quantity(db_user.id, callback_data.product_id, -1)
    elif callback_data.action == 'del':
        await cart_service.remove_item(db_user.id, callback_data.product_id)
    else:
        await callback.answer('Некорректное действие.', show_alert=True)
        return
    await render_cart(callback, session, db_user)


@router.callback_query(NavCb.filter(F.target == 'cart_clear'))
async def clear_cart(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await CartService(session).clear(db_user.id)
    await callback.answer('Корзина очищена.')
    await render_cart(callback, session, db_user)


@router.callback_query(NavCb.filter(F.target == 'promo'))
async def promo_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CheckoutStates.entering_promo)
    await callback.message.answer('Введите промокод сообщением. Для отмены нажмите /start')
    await callback.answer()


@router.message(CheckoutStates.entering_promo)
async def promo_apply(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    cart_service = CartService(session)
    cart = await cart_service.get_cart(db_user.id)
    product_ids = [item.product_id for item in cart.items]
    game_ids = [item.product.game_id for item in cart.items]
    try:
        promo = await PromoService(session).validate_code(message.text or '', user=db_user, product_ids=product_ids, game_ids=game_ids)
        cart.promo_code_id = promo.id
        await state.clear()
        await message.answer(f'🎁 Промокод {promo.code} применён.')
    except PromoValidationError as exc:
        await message.answer(f'Ошибка: {exc}')


```

## app/handlers/user/catalog.py

```py

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.user import categories_kb, games_kb, product_kb, products_kb
from app.repositories.catalog import CategoryRepository, GameRepository, ProductRepository
from app.services.media import MediaService
from app.services.pricing import PricingService
from app.utils.callbacks import NavCb
from app.utils.pagination import get_offset
from app.utils.texts import game_caption, product_caption

router = Router(name='user_catalog')
PAGE_SIZE = 5


@router.callback_query(NavCb.filter(F.target == 'games'))
async def games_list(callback: CallbackQuery, session: AsyncSession) -> None:
    games = await GameRepository(session).list_active()
    await callback.message.edit_text('🎮 <b>Игры</b>', reply_markup=games_kb(games), parse_mode='HTML')
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'game'))
async def game_view(callback: CallbackQuery, callback_data: NavCb, session: AsyncSession) -> None:
    game = await GameRepository(session).get(callback_data.entity_id)
    if not game or not game.is_active:
        await callback.answer('Игра не найдена.', show_alert=True)
        return
    categories = await CategoryRepository(session).list_by_game(game.id)
    caption = game_caption(game)
    await callback.message.edit_text(caption, reply_markup=categories_kb(game.id, categories), parse_mode='HTML')
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'game_from_category'))
async def game_from_category(callback: CallbackQuery, callback_data: NavCb, session: AsyncSession) -> None:
    category = await CategoryRepository(session).get(callback_data.entity_id)
    if not category:
        await callback.answer('Категория не найдена.', show_alert=True)
        return
    cb = NavCb(target='game', entity_id=category.game_id)
    await game_view(callback, cb, session)


@router.callback_query(NavCb.filter(F.target == 'category'))
async def category_view(callback: CallbackQuery, callback_data: NavCb, session: AsyncSession) -> None:
    category = await CategoryRepository(session).get(callback_data.entity_id)
    if not category:
        await callback.answer('Категория не найдена.', show_alert=True)
        return
    page = callback_data.page or 1
    repo = ProductRepository(session)
    total = await repo.count_by_category(category.id)
    products = await repo.list_by_category(category.id, limit=PAGE_SIZE, offset=get_offset(page, PAGE_SIZE))
    title = f'🗂 <b>{category.title}</b>\n\nВыберите товар:'
    await callback.message.edit_text(
        title,
        reply_markup=products_kb(category.id, products, page, total, PAGE_SIZE),
        parse_mode='HTML',
    )
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'product'))
async def product_view(callback: CallbackQuery, callback_data: NavCb, session: AsyncSession, db_user) -> None:
    product = await ProductRepository(session).get_full(callback_data.entity_id)
    if not product or not product.is_active:
        await callback.answer('Товар не найден.', show_alert=True)
        return
    quote = await PricingService(session).get_product_price(product, user=db_user)
    caption = product_caption(product, quote.final_price, quote.currency_code)
    await callback.message.edit_text(
        caption,
        reply_markup=product_kb(product.id, product.category_id, callback_data.page or 1),
        parse_mode='HTML',
    )
    await callback.answer()


```

## app/handlers/user/checkout.py

```py

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product, User
from app.services.cart import CartService
from app.services.orders import OrderService
from app.services.payment import ManualPaymentProvider
from app.states.user import CheckoutStates
from app.utils.callbacks import NavCb
from app.utils.idempotency import build_checkout_key
from app.utils.validators import ValidationError, validate_dynamic_field

router = Router(name='user_checkout')


def _build_dynamic_fields(products: list[Product]) -> list[dict]:
    fields: list[dict] = []
    for product in products:
        prefix = product.slug
        if product.requires_player_id:
            fields.append({'key': f'{prefix}.player_id', 'label': f'{product.title}: player_id', 'type': 'text', 'required': True})
        if product.requires_nickname:
            fields.append({'key': f'{prefix}.nickname', 'label': f'{product.title}: nickname', 'type': 'text', 'required': True})
        if product.requires_region:
            fields.append({'key': f'{prefix}.region', 'label': f'{product.title}: region', 'type': 'text', 'required': True})
        if product.requires_screenshot:
            fields.append({'key': f'{prefix}.screenshot_note', 'label': f'{product.title}: ссылка/комментарий к скриншоту', 'type': 'text', 'required': True})
        for item in product.extra_fields_schema_json:
            schema = dict(item)
            schema['key'] = f'{prefix}.{schema["key"]}'
            schema['label'] = f'{product.title}: {schema.get("label", schema["key"])}'
            fields.append(schema)
    return fields


async def start_checkout(callback: CallbackQuery, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    cart = await CartService(session).get_cart(db_user.id)
    if not cart.items:
        await callback.answer('Корзина пуста.', show_alert=True)
        return
    fields = _build_dynamic_fields([item.product for item in cart.items])
    await state.set_state(CheckoutStates.collecting_fields)
    await state.update_data(checkout_fields=fields, answers={}, step=0)
    if fields:
        await callback.message.answer(f'Оформление заказа.\n\nВведите: {fields[0]["label"]}')
    else:
        await finalize_checkout(callback.message, session, db_user, state)
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'checkout'))
async def checkout_entry(callback: CallbackQuery, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    await start_checkout(callback, session, db_user, state)


@router.message(CheckoutStates.collecting_fields)
async def collect_checkout_fields(message: Message, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    data = await state.get_data()
    fields: list[dict] = data.get('checkout_fields', [])
    step: int = data.get('step', 0)
    answers: dict = data.get('answers', {})
    if step >= len(fields):
        await finalize_checkout(message, session, db_user, state)
        return
    field = fields[step]
    try:
        answers[field['key']] = validate_dynamic_field(field, message.text or '')
    except ValidationError as exc:
        await message.answer(str(exc))
        return
    step += 1
    await state.update_data(answers=answers, step=step)
    if step < len(fields):
        await message.answer(f'Введите: {fields[step]["label"]}')
    else:
        await finalize_checkout(message, session, db_user, state)


async def finalize_checkout(message: Message, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    cart_service = CartService(session)
    cart = await cart_service.get_cart(db_user.id)
    if not cart.items:
        await state.clear()
        await message.answer('Корзина пуста.')
        return
    data = await state.get_data()
    answers = data.get('answers', {})
    checkout_key = build_checkout_key(db_user.id, cart.id, cart.version)
    order = await OrderService(session).create_order_from_cart(
        cart=cart,
        user=db_user,
        metadata={'answers': answers},
        checkout_key=checkout_key,
        actor_user_id=db_user.id,
    )
    instruction = await ManualPaymentProvider().build_instruction(order)
    await state.clear()
    await message.answer(instruction.text)


```

## app/handlers/user/orders.py

```py

from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.user import order_actions_kb, orders_kb
from app.models import Order, OrderStatus, User
from app.repositories.orders import OrderRepository
from app.services.cart import CartService
from app.utils.callbacks import NavCb
from app.utils.texts import order_card, profile_text

router = Router(name='user_orders')


@router.callback_query(NavCb.filter(F.target == 'orders_current'))
async def current_orders(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    orders = await OrderRepository(session).list_by_user(db_user.id)
    active = [order for order in orders if order.status not in {OrderStatus.COMPLETED, OrderStatus.CANCELED, OrderStatus.FAILED}]
    await callback.message.edit_text('📦 <b>Текущие заказы</b>', reply_markup=orders_kb(active), parse_mode='HTML')
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'orders_history'))
async def history_orders(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    orders = await OrderRepository(session).list_by_user(db_user.id)
    history = [order for order in orders if order.status in {OrderStatus.COMPLETED, OrderStatus.CANCELED, OrderStatus.FAILED}]
    await callback.message.edit_text('🕘 <b>История заказов</b>', reply_markup=orders_kb(history), parse_mode='HTML')
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'order'))
async def order_view(callback: CallbackQuery, callback_data: NavCb, session: AsyncSession) -> None:
    order = await OrderRepository(session).get_full(callback_data.entity_id)
    if not order:
        await callback.answer('Заказ не найден.', show_alert=True)
        return
    await callback.message.edit_text(order_card(order), reply_markup=order_actions_kb(order.id), parse_mode='HTML')
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'repeat_order'))
async def repeat_order(callback: CallbackQuery, callback_data: NavCb, session: AsyncSession, db_user: User) -> None:
    order = await OrderRepository(session).get_full(callback_data.entity_id)
    if not order:
        await callback.answer('Заказ не найден.', show_alert=True)
        return
    cart_service = CartService(session)
    await cart_service.clear(db_user.id)
    from app.repositories.catalog import ProductRepository

    product_repo = ProductRepository(session)
    for item in order.items:
        product = await product_repo.get_full(item.product_id)
        if product and product.is_active:
            await cart_service.add_item(db_user.id, product, quantity=item.quantity)
    await callback.answer('Заказ повторно добавлен в корзину.')


```

## app/handlers/user/profile.py

```py

from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, Referral, User
from app.services.referral import ReferralService
from app.utils.callbacks import NavCb
from app.utils.texts import profile_text

router = Router(name='user_profile')


@router.callback_query(NavCb.filter(F.target == 'profile'))
async def profile_view(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    orders_count = int(await session.scalar(select(func.count()).select_from(Order).where(Order.user_id == db_user.id)) or 0)
    total_spent = await session.scalar(select(func.coalesce(func.sum(Order.total_amount), 0)).where(Order.user_id == db_user.id))
    referral_code = await ReferralService(session).get_or_create_user_ref_code(db_user)
    text = profile_text(db_user, orders_count, Decimal(total_spent or 0), referral_code)
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'ref'))
async def referral_view(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    referral_code = await ReferralService(session).get_or_create_user_ref_code(db_user)
    bot_username = await __import__('app.services.settings', fromlist=['SettingsService']).SettingsService(session).get('bot_username', 'game_pay_bot')
    text = (
        '🤝 <b>Реферальная система</b>\n\n'
        f'Ваш код: <code>{referral_code}</code>\n'
        f'Ссылка: https://t.me/{bot_username}?start=ref_{db_user.id}'
    )
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


```

## app/handlers/user/reviews.py

```py

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, OrderStatus, Review, ReviewStatus, User
from app.repositories.settings import ReviewRepository
from app.states.user import CheckoutStates
from app.utils.callbacks import NavCb
from app.utils.validators import validate_positive_int

router = Router(name='user_reviews')


@router.callback_query(NavCb.filter(F.target == 'reviews'))
async def reviews_info(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        '⭐ <b>Отзывы</b>\n\nОставить отзыв можно после выполненного заказа.', parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'review_create'))
async def review_start(callback: CallbackQuery, callback_data: NavCb, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    order = await session.get(Order, callback_data.entity_id)
    if not order or order.user_id != db_user.id or order.status not in {OrderStatus.FULFILLED, OrderStatus.COMPLETED}:
        await callback.answer('Оставить отзыв можно только после выполненного заказа.', show_alert=True)
        return
    await state.set_state(CheckoutStates.leaving_review)
    await state.update_data(review_order_id=order.id)
    await callback.message.answer('Введите отзыв в формате: <оценка 1-5> ; <текст отзыва>')
    await callback.answer()


@router.message(CheckoutStates.leaving_review)
async def review_submit(message: Message, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    payload = (message.text or '').split(';', maxsplit=1)
    if len(payload) != 2:
        await message.answer('Формат: 5 ; отличный сервис')
        return
    rating = validate_positive_int(payload[0].strip(), 'rating')
    text = payload[1].strip()
    data = await state.get_data()
    order_id = data.get('review_order_id')
    await ReviewRepository(session).create(
        user_id=db_user.id,
        order_id=order_id,
        rating=min(rating, 5),
        text=text,
        status=ReviewStatus.HIDDEN,
    )
    await state.clear()
    await message.answer('Спасибо! Отзыв отправлен на модерацию.')


```

## app/handlers/user/start.py

```py

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.user import main_menu_kb
from app.models import Order, User
from app.repositories.users import UserRepository
from app.services.referral import ReferralService
from app.services.settings import SettingsService
from app.utils.callbacks import NavCb
from app.utils.texts import main_menu_text

router = Router(name='user_start')


async def _render_home(target: Message | CallbackQuery, session: AsyncSession, db_user: User) -> None:
    settings_service = SettingsService(session)
    welcome = await settings_service.get('welcome_text', 'Добро пожаловать в Game Pay.')
    shop_name = await settings_service.get('shop_name', 'Game Pay')
    text = main_menu_text(shop_name, welcome)
    if isinstance(target, Message):
        await target.answer(text, reply_markup=main_menu_kb(), parse_mode='HTML')
    else:
        await target.message.edit_text(text, reply_markup=main_menu_kb(), parse_mode='HTML')
        await target.answer()


@router.message(CommandStart())
async def start_handler(message: Message, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    await state.clear()
    args = (message.text or '').split(maxsplit=1)
    if len(args) > 1 and args[1].startswith('ref_'):
        code_user_id = args[1].removeprefix('ref_')
        if code_user_id.isdigit():
            referrer = await UserRepository(session).get(int(code_user_id))
            if referrer:
                await ReferralService(session).register_referral(referrer, db_user)
    await _render_home(message, session, db_user)


@router.callback_query(NavCb.filter(F.target == 'home'))
async def home_callback(callback: CallbackQuery, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    await state.clear()
    await _render_home(callback, session, db_user)


```

## app/handlers/user/support.py

```py

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.settings import SettingsService
from app.utils.callbacks import NavCb

router = Router(name='user_support')


@router.callback_query(NavCb.filter(F.target == 'support'))
async def support_view(callback: CallbackQuery, session: AsyncSession) -> None:
    settings = SettingsService(session)
    contact = await settings.get('support_contact', '@support')
    faq = await settings.get('faq_text', 'По вопросам оплаты и заказа напишите в поддержку.')
    text = f'🆘 <b>Поддержка</b>\n\nКонтакт: {contact}\n\n{faq}'
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == 'info'))
async def info_view(callback: CallbackQuery, session: AsyncSession) -> None:
    settings = SettingsService(session)
    rules = await settings.get('rules_text', 'Соблюдайте правила магазина.')
    payment = await settings.get('payment_methods_text', 'Ручная оплата через оператора.')
    text = f'ℹ️ <b>Информация / Правила</b>\n\n{rules}\n\n💳 Способы оплаты:\n{payment}'
    await callback.message.edit_text(text, parse_mode='HTML')
    await callback.answer()


```

## app/keyboards/__init__.py

```py



```

## app/keyboards/admin.py

```py

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


```

## app/keyboards/common.py

```py

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.callbacks import ConfirmCb, NavCb


def back_button(target: str, entity_id: int = 0, page: int = 1) -> InlineKeyboardButton:
    return InlineKeyboardButton(text='🔙 Назад', callback_data=NavCb(target=target, entity_id=entity_id, page=page).pack())


def confirm_keyboard(action: str, entity_id: int, token: str, cancel_target: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='✅ Подтвердить', callback_data=ConfirmCb(action=action, entity_id=entity_id, token=token).pack())
    builder.button(text='❌ Отмена', callback_data=NavCb(target=cancel_target).pack())
    builder.adjust(1)
    return builder.as_markup()


```

## app/keyboards/user.py

```py

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


```

## app/main.py

```py

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import CallbackQuery, ErrorEvent, Message, Update
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.handlers.admin import broadcasts, catalog as admin_catalog, misc as admin_misc, orders as admin_orders, panel, prices, promos
from app.handlers.user import cart, catalog, checkout, orders, profile, reviews, start, support
from app.middlewares.block import BlockCheckMiddleware
from app.middlewares.db import DbSessionMiddleware
from app.middlewares.rate_limit import RateLimitMiddleware
from app.middlewares.user_context import UserContextMiddleware

logger = logging.getLogger(__name__)


def build_dispatcher() -> Dispatcher:
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url)
    storage = RedisStorage(redis=redis)
    dp = Dispatcher(storage=storage)

    middlewares = [DbSessionMiddleware(), UserContextMiddleware(), BlockCheckMiddleware(), RateLimitMiddleware()]
    for mw in middlewares:
        dp.update.middleware(mw)

    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(checkout.router)
    dp.include_router(orders.router)
    dp.include_router(profile.router)
    dp.include_router(reviews.router)
    dp.include_router(support.router)

    dp.include_router(panel.router)
    dp.include_router(admin_catalog.router)
    dp.include_router(admin_orders.router)
    dp.include_router(prices.router)
    dp.include_router(promos.router)
    dp.include_router(broadcasts.router)
    dp.include_router(admin_misc.router)

    @dp.callback_query(F.data == 'noop')
    async def noop(callback: CallbackQuery) -> None:
        await callback.answer()

    @dp.errors()
    async def on_error(event: ErrorEvent) -> None:
        update = event.update
        exc = event.exception
        logger.exception('Unhandled error: %s', exc)
        try:
            if update.callback_query:
                await update.callback_query.answer('Произошла ошибка. Попробуйте ещё раз.', show_alert=True)
            elif update.message:
                await update.message.answer('Произошла ошибка. Команда не выполнена.')
        except TelegramBadRequest:
            pass

    return dp


async def main() -> None:
    setup_logging()
    settings = get_settings()
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = build_dispatcher()
    logger.info('Starting Game Pay bot')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())


```

## app/middlewares/__init__.py

```py



```

## app/middlewares/block.py

```py

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message


class BlockCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[Any, dict[str, Any]], Awaitable[Any]], event: Any, data: dict[str, Any]) -> Any:
        user = data.get('db_user')
        if user and user.is_blocked:
            text = '⛔ Ваш доступ ограничен. Обратитесь в поддержку.'
            if isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
                return None
            if isinstance(event, Message):
                await event.answer(text)
                return None
        return await handler(event, data)


```

## app/middlewares/db.py

```py

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware

from app.db.session import AsyncSessionLocal


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[Any, dict[str, Any]], Awaitable[Any]], event: Any, data: dict[str, Any]) -> Any:
        async with AsyncSessionLocal() as session:
            data['session'] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise


```

## app/middlewares/rate_limit.py

```py

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, interval_seconds: float = 0.7):
        self.interval_seconds = interval_seconds
        self._storage: dict[tuple[int, str], float] = {}

    async def __call__(self, handler: Callable[[Any, dict[str, Any]], Awaitable[Any]], event: Any, data: dict[str, Any]) -> Any:
        event_from_user = data.get('event_from_user')
        if event_from_user is None:
            return await handler(event, data)
        key = (event_from_user.id, getattr(handler, '__name__', 'handler'))
        now = time.monotonic()
        prev = self._storage.get(key, 0)
        if now - prev < self.interval_seconds:
            if isinstance(event, CallbackQuery):
                await event.answer('Слишком быстро. Попробуйте ещё раз через секунду.', show_alert=False)
                return None
            if isinstance(event, Message):
                return None
        self._storage[key] = now
        return await handler(event, data)


```

## app/middlewares/user_context.py

```py

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware

from app.repositories.users import UserRepository


class UserContextMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[Any, dict[str, Any]], Awaitable[Any]], event: Any, data: dict[str, Any]) -> Any:
        session = data['session']
        event_from_user = data.get('event_from_user')
        if event_from_user:
            repo = UserRepository(session)
            user = await repo.get_by_telegram_id(event_from_user.id)
            if user is None:
                user = await repo.create(
                    telegram_id=event_from_user.id,
                    username=event_from_user.username,
                    first_name=event_from_user.first_name,
                    last_name=event_from_user.last_name,
                )
            else:
                user.username = event_from_user.username
                user.first_name = event_from_user.first_name
                user.last_name = event_from_user.last_name
            data['db_user'] = user
        return await handler(event, data)


```

## app/models/__init__.py

```py

from app.models.entities import *  # noqa: F401,F403
from app.models.enums import *  # noqa: F401,F403


```

## app/models/entities.py

```py

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    AdminRole,
    AuditAction,
    BroadcastStatus,
    DiscountScope,
    EntityType,
    FulfillmentType,
    MediaType,
    OrderStatus,
    PaymentProviderType,
    PromoType,
    ReviewStatus,
)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')


class MediaFile(Base):
    __tablename__ = 'media_files'

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    file_unique_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    media_type: Mapped[MediaType] = mapped_column(Enum(MediaType, name='media_type_enum'), nullable=False)
    entity_type: Mapped[EntityType] = mapped_column(Enum(EntityType, name='entity_type_enum'), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(255))
    created_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey('admins.id', ondelete='SET NULL'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Game(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'games'
    __table_args__ = (
        UniqueConstraint('slug', name='uq_games_slug'),
        Index('ix_games_active_sort', 'is_active', 'sort_order'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    image_id: Mapped[int | None] = mapped_column(ForeignKey('media_files.id', ondelete='SET NULL'))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default='true')
    sort_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False, server_default='100')

    categories: Mapped[list[Category]] = relationship(back_populates='game')
    products: Mapped[list[Product]] = relationship(back_populates='game')
    image: Mapped[MediaFile | None] = relationship(foreign_keys=[image_id])


class Category(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'categories'
    __table_args__ = (
        UniqueConstraint('game_id', 'slug', name='uq_categories_game_slug'),
        Index('ix_categories_game_active_sort', 'game_id', 'is_active', 'sort_order'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    image_id: Mapped[int | None] = mapped_column(ForeignKey('media_files.id', ondelete='SET NULL'))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default='true')
    sort_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False, server_default='100')

    game: Mapped[Game] = relationship(back_populates='categories')
    products: Mapped[list[Product]] = relationship(back_populates='category')
    image: Mapped[MediaFile | None] = relationship(foreign_keys=[image_id])


class Product(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'products'
    __table_args__ = (
        UniqueConstraint('category_id', 'slug', name='uq_products_category_slug'),
        Index('ix_products_category_active_sort', 'category_id', 'is_active', 'sort_order'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    image_id: Mapped[int | None] = mapped_column(ForeignKey('media_files.id', ondelete='SET NULL'))
    fulfillment_type: Mapped[FulfillmentType] = mapped_column(
        Enum(FulfillmentType, name='fulfillment_type_enum'), nullable=False
    )
    requires_player_id: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')
    requires_nickname: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')
    requires_region: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')
    requires_manual_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')
    requires_screenshot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')
    extra_fields_schema_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default='true')
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')
    sort_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False, server_default='100')

    game: Mapped[Game] = relationship(back_populates='products')
    category: Mapped[Category] = relationship(back_populates='products')
    image: Mapped[MediaFile | None] = relationship(foreign_keys=[image_id])
    prices: Mapped[list[Price]] = relationship(back_populates='product')


class User(Base, TimestampMixin):
    __tablename__ = 'users'
    __table_args__ = (
        UniqueConstraint('telegram_id', name='uq_users_telegram_id'),
        Index('ix_users_blocked', 'is_blocked'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')
    block_reason: Mapped[str | None] = mapped_column(Text)
    referred_by_user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    personal_discount_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default='0')

    referred_by: Mapped[User | None] = relationship(remote_side=[id])
    admin: Mapped[Admin | None] = relationship(back_populates='user', uselist=False)


class Admin(Base):
    __tablename__ = 'admins'
    __table_args__ = (UniqueConstraint('user_id', name='uq_admins_user_id'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role: Mapped[AdminRole] = mapped_column(Enum(AdminRole, name='admin_role_enum'), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default='true')
    can_manage_categories: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates='admin')


class Price(Base, TimestampMixin):
    __tablename__ = 'prices'
    __table_args__ = (Index('ix_prices_product_active_dates', 'product_id', 'is_active', 'starts_at', 'ends_at'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discounted_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency_code: Mapped[str] = mapped_column(String(8), nullable=False, default='RUB', server_default='RUB')
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default='true')
    changed_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey('admins.id', ondelete='SET NULL'))

    product: Mapped[Product] = relationship(back_populates='prices')


class Cart(Base, TimestampMixin):
    __tablename__ = 'carts'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    promo_code_id: Mapped[int | None] = mapped_column(ForeignKey('promo_codes.id', ondelete='SET NULL'))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default='true')
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False, server_default='1')

    items: Mapped[list[CartItem]] = relationship(back_populates='cart', cascade='all, delete-orphan')


class CartItem(Base, TimestampMixin):
    __tablename__ = 'cart_items'
    __table_args__ = (UniqueConstraint('cart_id', 'product_id', name='uq_cart_product'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey('carts.id', ondelete='CASCADE'), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False, server_default='1')
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    cart: Mapped[Cart] = relationship(back_populates='items')
    product: Mapped[Product] = relationship()


class PromoCode(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'promo_codes'
    __table_args__ = (UniqueConstraint('code', name='uq_promo_codes_code'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    promo_type: Mapped[PromoType] = mapped_column(Enum(PromoType, name='promo_type_enum'), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    usage_limit: Mapped[int | None] = mapped_column(Integer)
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default='0')
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    game_id: Mapped[int | None] = mapped_column(ForeignKey('games.id', ondelete='SET NULL'))
    product_id: Mapped[int | None] = mapped_column(ForeignKey('products.id', ondelete='SET NULL'))
    only_new_users: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default='true')


class PromoCodeUsage(Base):
    __tablename__ = 'promo_code_usages'
    __table_args__ = (UniqueConstraint('promo_code_id', 'user_id', 'order_id', name='uq_promo_usage_unique'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    promo_code_id: Mapped[int] = mapped_column(ForeignKey('promo_codes.id', ondelete='CASCADE'), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Order(Base, TimestampMixin):
    __tablename__ = 'orders'
    __table_args__ = (
        UniqueConstraint('order_number', name='uq_orders_order_number'),
        UniqueConstraint('checkout_key', name='uq_orders_checkout_key'),
        Index('ix_orders_user_status', 'user_id', 'status'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[str] = mapped_column(String(32), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    cart_id: Mapped[int | None] = mapped_column(ForeignKey('carts.id', ondelete='SET NULL'))
    promo_code_id: Mapped[int | None] = mapped_column(ForeignKey('promo_codes.id', ondelete='SET NULL'))
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name='order_status_enum'), nullable=False, default=OrderStatus.NEW, server_default='new'
    )
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default='0')
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(8), nullable=False, default='RUB', server_default='RUB')
    fulfillment_type: Mapped[FulfillmentType] = mapped_column(
        Enum(FulfillmentType, name='order_fulfillment_type_enum'), nullable=False
    )
    payment_provider: Mapped[PaymentProviderType] = mapped_column(
        Enum(PaymentProviderType, name='payment_provider_type_enum'), nullable=False, server_default='manual'
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    admin_comment: Mapped[str | None] = mapped_column(Text)
    checkout_key: Mapped[str] = mapped_column(String(64), nullable=False)

    items: Mapped[list[OrderItem]] = relationship(back_populates='order', cascade='all, delete-orphan')
    status_history: Mapped[list[OrderStatusHistory]] = relationship(
        back_populates='order', cascade='all, delete-orphan'
    )


class OrderItem(Base):
    __tablename__ = 'order_items'

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='RESTRICT'), nullable=False)
    product_title: Mapped[str] = mapped_column(String(120), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fulfillment_type: Mapped[FulfillmentType] = mapped_column(Enum(FulfillmentType, name='order_item_fulfillment_type_enum'))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    order: Mapped[Order] = relationship(back_populates='items')


class OrderStatusHistory(Base):
    __tablename__ = 'order_status_history'
    __table_args__ = (Index('ix_order_status_history_order_id', 'order_id'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus, name='order_status_history_enum'), nullable=False)
    changed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    actor_label: Mapped[str] = mapped_column(String(120), nullable=False, default='system', server_default='system')
    comment: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    order: Mapped[Order] = relationship(back_populates='status_history')


class Review(Base, TimestampMixin):
    __tablename__ = 'reviews'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey('products.id', ondelete='SET NULL'))
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, name='review_status_enum'), nullable=False, server_default='hidden'
    )
    moderated_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey('admins.id', ondelete='SET NULL'))

    __table_args__ = (CheckConstraint('rating >= 1 and rating <= 5', name='ck_review_rating_range'),)


class Referral(Base, TimestampMixin):
    __tablename__ = 'referrals'
    __table_args__ = (UniqueConstraint('referrer_user_id', 'referred_user_id', name='uq_referral_pair'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    referrer_user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    referred_user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    referral_code: Mapped[str] = mapped_column(String(32), nullable=False)
    first_order_id: Mapped[int | None] = mapped_column(ForeignKey('orders.id', ondelete='SET NULL'))
    is_rewarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')


class ReferralReward(Base):
    __tablename__ = 'referral_rewards'

    id: Mapped[int] = mapped_column(primary_key=True)
    referral_id: Mapped[int] = mapped_column(ForeignKey('referrals.id', ondelete='CASCADE'), nullable=False)
    referrer_user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    referred_user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    order_id: Mapped[int | None] = mapped_column(ForeignKey('orders.id', ondelete='SET NULL'))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class BotSetting(Base, TimestampMixin):
    __tablename__ = 'bot_settings'
    __table_args__ = (UniqueConstraint('key', name='uq_bot_settings_key'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[Any] = mapped_column(JSONB, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class Broadcast(Base, TimestampMixin):
    __tablename__ = 'broadcasts'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    image_id: Mapped[int | None] = mapped_column(ForeignKey('media_files.id', ondelete='SET NULL'))
    status: Mapped[BroadcastStatus] = mapped_column(
        Enum(BroadcastStatus, name='broadcast_status_enum'), nullable=False, server_default='draft'
    )
    target_filter_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey('admins.id', ondelete='SET NULL'))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    send_hash: Mapped[str | None] = mapped_column(String(128), unique=True)


class DiscountRule(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'discount_rules'
    __table_args__ = (Index('ix_discount_rules_scope_active', 'scope', 'is_active'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    scope: Mapped[DiscountScope] = mapped_column(Enum(DiscountScope, name='discount_scope_enum'), nullable=False)
    percent: Mapped[int | None] = mapped_column(Integer)
    fixed_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    game_id: Mapped[int | None] = mapped_column(ForeignKey('games.id', ondelete='CASCADE'))
    product_id: Mapped[int | None] = mapped_column(ForeignKey('products.id', ondelete='CASCADE'))
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    min_total_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False, server_default='100')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default='true')


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    __table_args__ = (Index('ix_audit_logs_entity', 'entity_type', 'entity_id'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    actor_admin_id: Mapped[int | None] = mapped_column(ForeignKey('admins.id', ondelete='SET NULL'))
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction, name='audit_action_enum'), nullable=False)
    entity_type: Mapped[EntityType] = mapped_column(Enum(EntityType, name='audit_entity_type_enum'), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer)
    old_values: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    new_values: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


```

## app/models/enums.py

```py

from enum import StrEnum


class AdminRole(StrEnum):
    SUPER_ADMIN = 'super_admin'
    ADMIN = 'admin'


class OrderStatus(StrEnum):
    NEW = 'new'
    WAITING_PAYMENT = 'waiting_payment'
    PAID = 'paid'
    PROCESSING = 'processing'
    FULFILLED = 'fulfilled'
    COMPLETED = 'completed'
    CANCELED = 'canceled'
    FAILED = 'failed'
    DISPUTE = 'dispute'


class FulfillmentType(StrEnum):
    MANUAL = 'manual'
    EXTERNAL_OFFICIAL_REDIRECT = 'external_official_redirect'
    ACCOUNT_ID_BASED = 'account_id_based'
    ADMIN_PROCESSED = 'admin_processed'


class MediaType(StrEnum):
    PHOTO = 'photo'
    DOCUMENT = 'document'


class EntityType(StrEnum):
    GAME = 'game'
    CATEGORY = 'category'
    PRODUCT = 'product'
    BANNER = 'banner'
    SETTING = 'setting'
    DEFAULT = 'default'


class PromoType(StrEnum):
    PERCENT = 'percent'
    FIXED = 'fixed'


class ReviewStatus(StrEnum):
    HIDDEN = 'hidden'
    PUBLISHED = 'published'
    REJECTED = 'rejected'


class BroadcastStatus(StrEnum):
    DRAFT = 'draft'
    SENT = 'sent'
    FAILED = 'failed'


class DiscountScope(StrEnum):
    GLOBAL = 'global'
    GAME = 'game'
    PRODUCT = 'product'
    PERSONAL = 'personal'
    ACCUMULATIVE = 'accumulative'


class AuditAction(StrEnum):
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'
    STATUS_CHANGE = 'status_change'
    LOGIN = 'login'
    BROADCAST = 'broadcast'
    BLOCK = 'block'
    UNBLOCK = 'unblock'
    OTHER = 'other'


class PaymentProviderType(StrEnum):
    MANUAL = 'manual'
    STUB = 'stub'


```

## app/repositories/__init__.py

```py



```

## app/repositories/base.py

```py

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar('ModelT', bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession):
        self.session = session

    def query(self) -> Select[tuple[ModelT]]:
        return select(self.model)

    async def get(self, entity_id: Any) -> ModelT | None:
        return await self.session.get(self.model, entity_id)

    async def list(self, *, limit: int = 20, offset: int = 0, **filters: Any) -> list[ModelT]:
        stmt = self.query().filter_by(**filters).limit(limit).offset(offset)
        result = await self.session.scalars(stmt)
        return list(result)

    async def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model).filter_by(**filters)
        return int(await self.session.scalar(stmt) or 0)

    async def create(self, **kwargs: Any) -> ModelT:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update_by_id(self, entity_id: Any, **kwargs: Any) -> ModelT | None:
        stmt = update(self.model).where(self.model.id == entity_id).values(**kwargs).returning(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_by_id(self, entity_id: Any) -> None:
        await self.session.execute(delete(self.model).where(self.model.id == entity_id))


```

## app/repositories/cart.py

```py

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models import Cart, CartItem
from app.repositories.base import BaseRepository


class CartRepository(BaseRepository[Cart]):
    model = Cart

    async def get_or_create_active(self, user_id: int) -> Cart:
        stmt = (
            select(Cart)
            .where(Cart.user_id == user_id, Cart.is_active.is_(True))
            .options(joinedload(Cart.items).joinedload(CartItem.product))
            .with_for_update()
        )
        cart = await self.session.scalar(stmt)
        if cart:
            return cart
        cart = Cart(user_id=user_id)
        self.session.add(cart)
        await self.session.flush()
        return cart

    async def get_full_active(self, user_id: int) -> Cart | None:
        stmt = (
            select(Cart)
            .where(Cart.user_id == user_id, Cart.is_active.is_(True))
            .options(joinedload(Cart.items).joinedload(CartItem.product))
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()


class CartItemRepository(BaseRepository[CartItem]):
    model = CartItem


```

## app/repositories/catalog.py

```py

from __future__ import annotations

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models import Category, Game, Price, Product
from app.repositories.base import BaseRepository


class GameRepository(BaseRepository[Game]):
    model = Game

    async def list_active(self) -> list[Game]:
        stmt = (
            select(Game)
            .where(Game.is_active.is_(True), Game.is_deleted.is_(False))
            .options(joinedload(Game.image))
            .order_by(Game.sort_order.asc(), Game.id.asc())
        )
        return list(await self.session.scalars(stmt))


class CategoryRepository(BaseRepository[Category]):
    model = Category

    async def list_by_game(self, game_id: int) -> list[Category]:
        stmt = (
            select(Category)
            .where(
                Category.game_id == game_id,
                Category.is_active.is_(True),
                Category.is_deleted.is_(False),
            )
            .options(joinedload(Category.image))
            .order_by(Category.sort_order.asc(), Category.id.asc())
        )
        return list(await self.session.scalars(stmt))


class ProductRepository(BaseRepository[Product]):
    model = Product

    async def get_full(self, product_id: int) -> Product | None:
        stmt = (
            select(Product)
            .where(Product.id == product_id, Product.is_deleted.is_(False))
            .options(joinedload(Product.image), joinedload(Product.game), joinedload(Product.category), selectinload(Product.prices))
        )
        return await self.session.scalar(stmt)

    async def list_by_category(self, category_id: int, *, limit: int, offset: int) -> list[Product]:
        stmt = (
            select(Product)
            .where(
                Product.category_id == category_id,
                Product.is_active.is_(True),
                Product.is_deleted.is_(False),
            )
            .options(joinedload(Product.image), selectinload(Product.prices))
            .order_by(Product.sort_order.asc(), Product.id.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(await self.session.scalars(stmt))

    async def count_by_category(self, category_id: int) -> int:
        stmt = select(Product.id).where(
            Product.category_id == category_id,
            Product.is_active.is_(True),
            Product.is_deleted.is_(False),
        )
        return len(list(await self.session.scalars(stmt)))


class PriceRepository(BaseRepository[Price]):
    model = Price

    async def get_current_for_product(self, product_id: int) -> Price | None:
        from sqlalchemy import func

        now = func.now()
        stmt = (
            select(Price)
            .where(
                Price.product_id == product_id,
                Price.is_active.is_(True),
                or_(Price.starts_at.is_(None), Price.starts_at <= now),
                or_(Price.ends_at.is_(None), Price.ends_at >= now),
            )
            .order_by(Price.created_at.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)


```

## app/repositories/orders.py

```py

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from app.models import Order, OrderStatusHistory
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    model = Order

    async def get_full(self, order_id: int) -> Order | None:
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items), selectinload(Order.status_history))
        )
        return await self.session.scalar(stmt)

    async def get_by_checkout_key(self, checkout_key: str) -> Order | None:
        stmt = select(Order).where(Order.checkout_key == checkout_key)
        return await self.session.scalar(stmt)

    async def list_by_user(self, user_id: int, *, status: str | None = None, limit: int = 20) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        if status:
            stmt = stmt.where(Order.status == status)
        return list(await self.session.scalars(stmt))

    async def list_recent(self, *, limit: int = 20) -> list[Order]:
        stmt = (
            select(Order)
            .options(selectinload(Order.items), joinedload(Order.status_history))
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars())


class OrderStatusHistoryRepository(BaseRepository[OrderStatusHistory]):
    model = OrderStatusHistory


```

## app/repositories/promo.py

```py

from __future__ import annotations

from sqlalchemy import select

from app.models import PromoCode, PromoCodeUsage
from app.repositories.base import BaseRepository


class PromoCodeRepository(BaseRepository[PromoCode]):
    model = PromoCode

    async def get_by_code(self, code: str) -> PromoCode | None:
        stmt = select(PromoCode).where(PromoCode.code == code.upper(), PromoCode.is_deleted.is_(False))
        return await self.session.scalar(stmt)


class PromoCodeUsageRepository(BaseRepository[PromoCodeUsage]):
    model = PromoCodeUsage


```

## app/repositories/settings.py

```py

from __future__ import annotations

from sqlalchemy import select

from app.models import BotSetting, Broadcast, DiscountRule, Review, Referral, ReferralReward, AuditLog
from app.repositories.base import BaseRepository


class BotSettingRepository(BaseRepository[BotSetting]):
    model = BotSetting

    async def get_by_key(self, key: str) -> BotSetting | None:
        stmt = select(BotSetting).where(BotSetting.key == key)
        return await self.session.scalar(stmt)


class DiscountRuleRepository(BaseRepository[DiscountRule]):
    model = DiscountRule


class ReviewRepository(BaseRepository[Review]):
    model = Review


class ReferralRepository(BaseRepository[Referral]):
    model = Referral


class ReferralRewardRepository(BaseRepository[ReferralReward]):
    model = ReferralReward


class BroadcastRepository(BaseRepository[Broadcast]):
    model = Broadcast


class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog


```

## app/repositories/users.py

```py

from __future__ import annotations

from sqlalchemy import select

from app.models import Admin, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        return await self.session.scalar(stmt)


class AdminRepository(BaseRepository[Admin]):
    model = Admin

    async def get_by_telegram_id(self, telegram_id: int) -> Admin | None:
        stmt = select(Admin).join(User).where(User.telegram_id == telegram_id, Admin.is_active.is_(True))
        return await self.session.scalar(stmt)


```

## app/services/__init__.py

```py



```

## app/services/audit.py

```py

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AuditAction, EntityType
from app.repositories.settings import AuditLogRepository


class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AuditLogRepository(session)

    async def log(
        self,
        *,
        action: AuditAction,
        entity_type: EntityType,
        entity_id: int | None = None,
        actor_user_id: int | None = None,
        actor_admin_id: int | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await self.repo.create(
            actor_user_id=actor_user_id,
            actor_admin_id=actor_admin_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values or {},
            new_values=new_values or {},
            metadata_json=metadata or {},
        )


```

## app/services/broadcast.py

```py

from __future__ import annotations

import hashlib

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Broadcast, User
from app.models.enums import BroadcastStatus
from app.repositories.settings import BroadcastRepository


class BroadcastService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BroadcastRepository(session)

    async def send(self, bot: Bot, broadcast: Broadcast) -> int:
        send_hash = hashlib.sha256(f'{broadcast.title}:{broadcast.text}'.encode()).hexdigest()
        if broadcast.send_hash and broadcast.send_hash == send_hash and broadcast.status == BroadcastStatus.SENT:
            raise ValueError('Такая рассылка уже была отправлена.')
        users = list(await self.session.scalars(select(User).where(User.is_blocked.is_(False))))
        sent = 0
        for user in users:
            try:
                await bot.send_message(user.telegram_id, broadcast.text)
                sent += 1
            except TelegramBadRequest:
                continue
        broadcast.status = BroadcastStatus.SENT
        broadcast.send_hash = send_hash
        await self.session.flush()
        return sent


```

## app/services/cart.py

```py

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Cart, CartItem, Product, User
from app.repositories.cart import CartItemRepository, CartRepository
from app.services.pricing import PricingService


@dataclass(slots=True)
class CartTotals:
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    currency_code: str


class CartService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.cart_repo = CartRepository(session)
        self.item_repo = CartItemRepository(session)
        self.pricing = PricingService(session)

    async def get_cart(self, user_id: int) -> Cart:
        return await self.cart_repo.get_or_create_active(user_id)

    async def add_item(self, user_id: int, product: Product, quantity: int = 1) -> Cart:
        cart = await self.cart_repo.get_or_create_active(user_id)
        for item in cart.items:
            if item.product_id == product.id:
                item.quantity += quantity
                cart.version += 1
                await self.session.flush()
                return cart
        self.session.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity))
        cart.version += 1
        await self.session.flush()
        return cart

    async def change_quantity(self, user_id: int, product_id: int, delta: int) -> Cart:
        cart = await self.cart_repo.get_or_create_active(user_id)
        target = next((item for item in cart.items if item.product_id == product_id), None)
        if not target:
            return cart
        target.quantity += delta
        if target.quantity <= 0:
            await self.session.delete(target)
        cart.version += 1
        await self.session.flush()
        return cart

    async def remove_item(self, user_id: int, product_id: int) -> Cart:
        cart = await self.cart_repo.get_or_create_active(user_id)
        target = next((item for item in cart.items if item.product_id == product_id), None)
        if target:
            await self.session.delete(target)
            cart.version += 1
            await self.session.flush()
        return cart

    async def clear(self, user_id: int) -> Cart:
        cart = await self.cart_repo.get_or_create_active(user_id)
        for item in list(cart.items):
            await self.session.delete(item)
        cart.version += 1
        await self.session.flush()
        return cart

    async def compute_totals(self, cart: Cart, user: User, promo=None) -> CartTotals:
        subtotal = Decimal('0.00')
        total = Decimal('0.00')
        currency_code = 'RUB'
        for item in cart.items:
            quote = await self.pricing.get_product_price(item.product, user=user, promo=promo)
            subtotal += quote.base_price * item.quantity
            total += quote.final_price * item.quantity
            currency_code = quote.currency_code
        discount = subtotal - total
        return CartTotals(subtotal=subtotal, discount=discount, total=total, currency_code=currency_code)


```

## app/services/media.py

```py

from __future__ import annotations

from aiogram.types import FSInputFile

from app.models import MediaFile


class MediaService:
    async def resolve_send_args(self, media: MediaFile | None, fallback_text: str) -> dict:
        if media and media.telegram_file_id:
            return {'photo': media.telegram_file_id, 'caption': fallback_text}
        return {'text': fallback_text}


```

## app/services/orders.py

```py

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Cart, Order, OrderItem, OrderStatusHistory, User
from app.models.enums import OrderStatus, PaymentProviderType
from app.repositories.orders import OrderRepository, OrderStatusHistoryRepository
from app.services.cart import CartService
from app.services.promo import PromoService


class OrderService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.order_repo = OrderRepository(session)
        self.history_repo = OrderStatusHistoryRepository(session)
        self.cart_service = CartService(session)
        self.promo_service = PromoService(session)

    async def create_order_from_cart(
        self,
        *,
        cart: Cart,
        user: User,
        metadata: dict,
        checkout_key: str,
        actor_user_id: int,
    ) -> Order:
        existing = await self.order_repo.get_by_checkout_key(checkout_key)
        if existing:
            return existing
        if not cart.items:
            raise ValueError('Корзина пуста.')

        promo = None
        if cart.promo_code_id:
            promo = await self.promo_service.repo.get(cart.promo_code_id)
        totals = await self.cart_service.compute_totals(cart, user, promo)
        order = Order(
            order_number=f'GP-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:8].upper()}',
            user_id=user.id,
            cart_id=cart.id,
            promo_code_id=cart.promo_code_id,
            status=OrderStatus.WAITING_PAYMENT,
            subtotal_amount=totals.subtotal,
            discount_amount=totals.discount,
            total_amount=totals.total,
            currency_code=totals.currency_code,
            fulfillment_type=cart.items[0].product.fulfillment_type,
            payment_provider=PaymentProviderType.MANUAL,
            metadata_json=metadata,
            checkout_key=checkout_key,
        )
        self.session.add(order)
        await self.session.flush()

        for item in cart.items:
            quote = await self.cart_service.pricing.get_product_price(item.product, user=user, promo=promo)
            self.session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    product_title=item.product.title,
                    quantity=item.quantity,
                    unit_price=quote.final_price,
                    line_total=quote.final_price * item.quantity,
                    fulfillment_type=item.product.fulfillment_type,
                    metadata_json={
                        'product_slug': item.product.slug,
                        'product_metadata': item.metadata_json,
                    },
                )
            )

        self.session.add(
            OrderStatusHistory(
                order_id=order.id,
                status=OrderStatus.NEW,
                changed_by_user_id=actor_user_id,
                actor_label='user',
                comment='Order created from cart.',
                metadata_json={'checkout_key': checkout_key},
            )
        )
        self.session.add(
            OrderStatusHistory(
                order_id=order.id,
                status=OrderStatus.WAITING_PAYMENT,
                changed_by_user_id=actor_user_id,
                actor_label='system',
                comment='Manual payment instructions issued.',
            )
        )
        if promo:
            await self.promo_service.mark_used(promo.id, user.id, order.id)
        cart.is_active = False
        await self.session.flush()
        return order

    async def change_status(
        self,
        *,
        order: Order,
        status: OrderStatus,
        actor_user_id: int | None,
        actor_label: str,
        comment: str | None = None,
    ) -> Order:
        order.status = status
        self.session.add(
            OrderStatusHistory(
                order_id=order.id,
                status=status,
                changed_by_user_id=actor_user_id,
                actor_label=actor_label,
                comment=comment,
            )
        )
        await self.session.flush()
        return order


```

## app/services/payment.py

```py

from __future__ import annotations

from dataclasses import dataclass

from app.models import Order


@dataclass(slots=True)
class PaymentInstruction:
    provider_name: str
    text: str


class PaymentProvider:
    async def build_instruction(self, order: Order) -> PaymentInstruction:
        raise NotImplementedError


class ManualPaymentProvider(PaymentProvider):
    async def build_instruction(self, order: Order) -> PaymentInstruction:
        return PaymentInstruction(
            provider_name='manual',
            text=(
                f'💳 Заказ {order.order_number}\n'
                f'Сумма: {order.total_amount} {order.currency_code}\n\n'
                'Оплата сейчас работает в ручном режиме. После перевода отправьте подтверждение в поддержку. '
                'Администратор проверит оплату и переведёт заказ в обработку.'
            ),
        )


```

## app/services/pricing.py

```py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DiscountRule, Price, Product, PromoCode, User
from app.models.enums import DiscountScope, PromoType
from app.repositories.catalog import PriceRepository


@dataclass(slots=True)
class PriceQuote:
    base_price: Decimal
    discount_amount: Decimal
    final_price: Decimal
    currency_code: str
    applied_rules: list[str]


class PricingService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.price_repo = PriceRepository(session)

    async def get_product_price(self, product: Product, user: User | None = None, promo: PromoCode | None = None) -> PriceQuote:
        price = await self.price_repo.get_current_for_product(product.id)
        if price is None:
            base = Decimal('0.00')
            currency = 'RUB'
        else:
            base = Decimal(price.discounted_price or price.base_price)
            currency = price.currency_code

        applied_rules: list[str] = []
        discount_amount = Decimal('0.00')
        discount_amount += await self._apply_discount_rules(product, base, applied_rules, user)

        if user and user.personal_discount_percent > 0:
            personal_discount = (base * Decimal(user.personal_discount_percent) / Decimal('100')).quantize(Decimal('0.01'))
            if personal_discount > discount_amount:
                discount_amount = personal_discount
                applied_rules.append(f'personal:{user.personal_discount_percent}%')

        if promo:
            promo_discount = self._promo_discount(base, promo)
            if promo_discount > discount_amount:
                discount_amount = promo_discount
                applied_rules.append(f'promo:{promo.code}')

        final_price = max(Decimal('0.00'), base - discount_amount)
        return PriceQuote(base_price=base, discount_amount=discount_amount, final_price=final_price, currency_code=currency, applied_rules=applied_rules)

    async def _apply_discount_rules(self, product: Product, base: Decimal, applied: list[str], user: User | None) -> Decimal:
        now = datetime.now(timezone.utc)
        stmt = (
            select(DiscountRule)
            .where(DiscountRule.is_deleted.is_(False), DiscountRule.is_active.is_(True))
            .order_by(DiscountRule.priority.asc(), DiscountRule.id.asc())
        )
        rules = list(await self.session.scalars(stmt))
        best = Decimal('0.00')
        for rule in rules:
            if rule.starts_at and rule.starts_at > now:
                continue
            if rule.ends_at and rule.ends_at < now:
                continue
            if rule.scope == DiscountScope.GLOBAL:
                pass
            elif rule.scope == DiscountScope.GAME and rule.game_id != product.game_id:
                continue
            elif rule.scope == DiscountScope.PRODUCT and rule.product_id != product.id:
                continue
            elif rule.scope == DiscountScope.PERSONAL and (user is None or rule.user_id != user.id):
                continue
            elif rule.scope == DiscountScope.ACCUMULATIVE and (user is None):
                continue
            candidate = Decimal('0.00')
            if rule.percent:
                candidate = (base * Decimal(rule.percent) / Decimal('100')).quantize(Decimal('0.01'))
            elif rule.fixed_amount:
                candidate = Decimal(rule.fixed_amount)
            if candidate > best:
                best = candidate
                applied.append(f'rule:{rule.title}')
        return best

    def _promo_discount(self, base: Decimal, promo: PromoCode) -> Decimal:
        if promo.promo_type == PromoType.PERCENT:
            return (base * Decimal(promo.value) / Decimal('100')).quantize(Decimal('0.01'))
        return min(base, Decimal(promo.value))


```

## app/services/promo.py

```py

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, PromoCode, User
from app.repositories.promo import PromoCodeRepository, PromoCodeUsageRepository


class PromoValidationError(ValueError):
    pass


class PromoService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PromoCodeRepository(session)
        self.usage_repo = PromoCodeUsageRepository(session)

    async def validate_code(self, code: str, *, user: User, product_ids: list[int], game_ids: list[int]) -> PromoCode:
        promo = await self.repo.get_by_code(code)
        if promo is None or not promo.is_enabled:
            raise PromoValidationError('Промокод не найден или отключён.')

        now = datetime.now(timezone.utc)
        if promo.starts_at and promo.starts_at > now:
            raise PromoValidationError('Промокод ещё не активен.')
        if promo.ends_at and promo.ends_at < now:
            raise PromoValidationError('Срок действия промокода истёк.')
        if promo.usage_limit is not None and promo.used_count >= promo.usage_limit:
            raise PromoValidationError('Лимит использования промокода исчерпан.')
        if promo.game_id and promo.game_id not in game_ids:
            raise PromoValidationError('Промокод не подходит для выбранной игры.')
        if promo.product_id and promo.product_id not in product_ids:
            raise PromoValidationError('Промокод не подходит для выбранного товара.')
        if promo.only_new_users:
            orders_count = await self.session.scalar(select(func.count()).select_from(Order).where(Order.user_id == user.id))
            if int(orders_count or 0) > 0:
                raise PromoValidationError('Промокод только для новых пользователей.')
        return promo

    async def mark_used(self, promo_code_id: int, user_id: int, order_id: int) -> None:
        promo = await self.repo.get(promo_code_id)
        if promo is None:
            return
        promo.used_count += 1
        await self.usage_repo.create(promo_code_id=promo_code_id, user_id=user_id, order_id=order_id)


```

## app/services/rbac.py

```py

from __future__ import annotations

from app.models.enums import AdminRole


ROLE_PERMISSIONS: dict[AdminRole, set[str]] = {
    AdminRole.SUPER_ADMIN: {
        'admins.manage', 'prices.manage', 'games.manage', 'categories.manage', 'products.manage', 'images.manage',
        'orders.view', 'orders.manage', 'broadcasts.manage', 'promos.manage', 'discounts.manage', 'users.block',
        'logs.view', 'settings.manage', 'reviews.moderate', 'users.view'
    },
    AdminRole.ADMIN: {
        'orders.view', 'orders.manage', 'products.manage', 'users.view', 'reviews.moderate'
    },
}


class RBACService:
    def has_permission(self, role: AdminRole, permission: str, *, can_manage_categories: bool = False) -> bool:
        if permission == 'categories.manage' and can_manage_categories:
            return True
        return permission in ROLE_PERMISSIONS.get(role, set())


```

## app/services/referral.py

```py

from __future__ import annotations

from decimal import Decimal
import secrets

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Referral, ReferralReward, User
from app.repositories.settings import ReferralRepository, ReferralRewardRepository
from app.services.settings import SettingsService


class ReferralService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ReferralRepository(session)
        self.reward_repo = ReferralRewardRepository(session)
        self.settings_service = SettingsService(session)

    def generate_ref_code(self) -> str:
        return secrets.token_hex(4).upper()

    async def get_or_create_user_ref_code(self, user: User) -> str:
        stmt = select(Referral.referral_code).where(Referral.referrer_user_id == user.id).limit(1)
        existing = await self.session.scalar(stmt)
        return existing or f'GP{user.id:06d}'

    async def register_referral(self, referrer: User, referred: User) -> None:
        count = await self.session.scalar(select(func.count()).select_from(Referral).where(Referral.referred_user_id == referred.id))
        if int(count or 0) > 0 or referrer.id == referred.id:
            return
        await self.repo.create(
            referrer_user_id=referrer.id,
            referred_user_id=referred.id,
            referral_code=await self.get_or_create_user_ref_code(referrer),
        )

    async def reward_first_purchase(self, referred_user_id: int, order_id: int, order_total: Decimal) -> None:
        stmt = select(Referral).where(Referral.referred_user_id == referred_user_id, Referral.is_rewarded.is_(False)).limit(1)
        referral = await self.session.scalar(stmt)
        if referral is None:
            return
        percent = Decimal(await self.settings_service.get('referral_reward_percent', 5))
        amount = (order_total * percent / Decimal('100')).quantize(Decimal('0.01'))
        await self.reward_repo.create(
            referral_id=referral.id,
            referrer_user_id=referral.referrer_user_id,
            referred_user_id=referred_user_id,
            order_id=order_id,
            amount=amount,
            description='Reward for first purchase of invited user.',
        )
        referral.first_order_id = order_id
        referral.is_rewarded = True
        await self.session.flush()


```

## app/services/settings.py

```py

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.settings import BotSettingRepository


class SettingsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BotSettingRepository(session)

    async def get(self, key: str, default: Any = None) -> Any:
        setting = await self.repo.get_by_key(key)
        return default if setting is None else setting.value

    async def set(self, key: str, value: Any, description: str | None = None) -> None:
        setting = await self.repo.get_by_key(key)
        if setting:
            setting.value = value
            if description is not None:
                setting.description = description
        else:
            await self.repo.create(key=key, value=value, description=description)
        await self.session.flush()

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for key in keys:
            values[key] = await self.get(key)
        return values


```

## app/states/__init__.py

```py



```

## app/states/admin.py

```py

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


```

## app/states/user.py

```py

from aiogram.fsm.state import State, StatesGroup


class CheckoutStates(StatesGroup):
    collecting_fields = State()
    entering_promo = State()
    leaving_review = State()
    contacting_support = State()


```

## app/templates/__init__.py

```py



```

## app/utils/__init__.py

```py



```

## app/utils/callbacks.py

```py

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


```

## app/utils/idempotency.py

```py

from __future__ import annotations

import hashlib


def build_checkout_key(user_id: int, cart_id: int, cart_version: int) -> str:
    return hashlib.sha256(f'{user_id}:{cart_id}:{cart_version}'.encode()).hexdigest()[:32]


```

## app/utils/pagination.py

```py

def get_offset(page: int, page_size: int) -> int:
    return max(0, (page - 1) * page_size)


def total_pages(total: int, page_size: int) -> int:
    if total <= 0:
        return 1
    return ((total - 1) // page_size) + 1


```

## app/utils/texts.py

```py

from decimal import Decimal

from app.models import Game, Order, Product, User


def main_menu_text(shop_name: str, welcome_text: str) -> str:
    return f'🎮 <b>{shop_name}</b>\n\n{welcome_text}'


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


```

## app/utils/validators.py

```py

import re
from typing import Any


class ValidationError(ValueError):
    pass


def validate_non_empty(value: str, field_name: str) -> str:
    value = value.strip()
    if not value:
        raise ValidationError(f'Поле "{field_name}" не должно быть пустым.')
    return value


def validate_slug(value: str) -> str:
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{1,62}', value):
        raise ValidationError('Slug должен содержать только латиницу, цифры, дефис и подчёркивание.')
    return value


def validate_positive_int(value: str, field_name: str) -> int:
    if not value.isdigit() or int(value) <= 0:
        raise ValidationError(f'Поле "{field_name}" должно быть положительным числом.')
    return int(value)


def validate_price(value: str) -> str:
    normalized = value.replace(',', '.').strip()
    if not re.fullmatch(r'\d+(\.\d{1,2})?', normalized):
        raise ValidationError('Цена должна быть числом, например 199 или 199.99.')
    return normalized


def validate_dynamic_field(field_schema: dict[str, Any], value: str) -> Any:
    field_type = field_schema.get('type', 'text')
    required = field_schema.get('required', False)
    if required and not value.strip():
        raise ValidationError(f'Поле "{field_schema.get("label", "value")}" обязательно для заполнения.')
    if field_type == 'number':
        return validate_positive_int(value, field_schema.get('label', 'value'))
    if field_type == 'email':
        if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', value.strip()):
            raise ValidationError('Введите корректный email.')
        return value.strip()
    if field_type == 'text':
        return value.strip()
    return value.strip()


```

## docker-compose.yml

```yml

version: '3.9'
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: game_pay
      POSTGRES_USER: game_pay
      POSTGRES_PASSWORD: game_pay
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  bot:
    build: .
    env_file:
      - .env
    depends_on:
      - db
      - redis
    restart: unless-stopped

volumes:
  postgres_data:


```

## requirements.txt

```txt

aiogram==3.20.0.post0
SQLAlchemy==2.0.40
asyncpg==0.30.0
alembic==1.15.2
redis==5.2.1
pydantic==2.11.3
pydantic-settings==2.8.1
python-dotenv==1.1.0
greenlet==3.2.0
orjson==3.10.16
uvloop==0.21.0; sys_platform != 'win32'


```

## seed.py

```py

from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal, engine
from app.db.base import Base
from app.models import (
    Admin,
    AdminRole,
    BotSetting,
    Category,
    EntityType,
    FulfillmentType,
    Game,
    MediaFile,
    MediaType,
    Price,
    Product,
    User,
)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed() -> None:
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        game_exists = await session.scalar(select(Game.id).limit(1))
        if game_exists:
            return

        placeholder_media = MediaFile(
            telegram_file_id='AgACAgIAAxkBAAIBplaceholder',
            file_unique_id='placeholder_unique_media',
            media_type=MediaType.PHOTO,
            entity_type=EntityType.DEFAULT,
            alt_text='Placeholder image',
        )
        session.add(placeholder_media)
        await session.flush()

        brawl = Game(slug='brawl_stars', title='Brawl Stars', description='Безопасное оформление через официальный flow или ручную обработку.', image_id=placeholder_media.id, is_active=True, sort_order=1)
        standoff = Game(slug='standoff_2', title='Standoff 2', description='Витрина, заказ и безопасная ручная обработка без запроса пароля.', image_id=placeholder_media.id, is_active=True, sort_order=2)
        session.add_all([brawl, standoff])
        await session.flush()

        categories = []
        for game in [brawl, standoff]:
            categories.append(Category(game_id=game.id, slug='currency', title='Валюта', description='Игровая валюта', image_id=placeholder_media.id, is_active=True, sort_order=1))
            categories.append(Category(game_id=game.id, slug='subscriptions', title='Подписки', description='Подписки и боевые пропуска', image_id=placeholder_media.id, is_active=True, sort_order=2))
        session.add_all(categories)
        await session.flush()
        category_map = {(c.game_id, c.slug): c for c in categories}

        products = [
            Product(game_id=brawl.id, category_id=category_map[(brawl.id, 'currency')].id, slug='gems_30', title='Gems 30', description='Безопасная покупка Gems. Без хранения пароля.', image_id=placeholder_media.id, fulfillment_type=FulfillmentType.MANUAL, requires_player_id=True, extra_fields_schema_json=[{'key': 'note_for_admin', 'label': 'Комментарий', 'type': 'text', 'required': False}], is_active=True, sort_order=1),
            Product(game_id=brawl.id, category_id=category_map[(brawl.id, 'currency')].id, slug='gems_80', title='Gems 80', description='Безопасная покупка Gems. Без хранения пароля.', image_id=placeholder_media.id, fulfillment_type=FulfillmentType.MANUAL, requires_player_id=True, extra_fields_schema_json=[], is_active=True, sort_order=2),
            Product(game_id=brawl.id, category_id=category_map[(brawl.id, 'currency')].id, slug='gems_170', title='Gems 170', description='Безопасная покупка Gems. Без хранения пароля.', image_id=placeholder_media.id, fulfillment_type=FulfillmentType.MANUAL, requires_player_id=True, extra_fields_schema_json=[], is_active=True, sort_order=3),
            Product(game_id=brawl.id, category_id=category_map[(brawl.id, 'subscriptions')].id, slug='brawl_pass', title='Brawl Pass', description='Brawl Pass через безопасный сценарий.', image_id=placeholder_media.id, fulfillment_type=FulfillmentType.EXTERNAL_OFFICIAL_REDIRECT, requires_player_id=True, requires_manual_review=True, extra_fields_schema_json=[{'key': 'email', 'label': 'Email для связи', 'type': 'email', 'required': False}], is_active=True, sort_order=4),
            Product(game_id=standoff.id, category_id=category_map[(standoff.id, 'currency')].id, slug='gold_100', title='Gold 100', description='Только безопасный manual/admin_processed flow.', image_id=placeholder_media.id, fulfillment_type=FulfillmentType.ADMIN_PROCESSED, requires_player_id=True, requires_nickname=True, extra_fields_schema_json=[], is_active=True, sort_order=1),
            Product(game_id=standoff.id, category_id=category_map[(standoff.id, 'currency')].id, slug='gold_500', title='Gold 500', description='Только безопасный manual/admin_processed flow.', image_id=placeholder_media.id, fulfillment_type=FulfillmentType.ADMIN_PROCESSED, requires_player_id=True, requires_nickname=True, extra_fields_schema_json=[], is_active=True, sort_order=2),
            Product(game_id=standoff.id, category_id=category_map[(standoff.id, 'currency')].id, slug='gold_1000', title='Gold 1000', description='Только безопасный manual/admin_processed flow.', image_id=placeholder_media.id, fulfillment_type=FulfillmentType.ADMIN_PROCESSED, requires_player_id=True, requires_nickname=True, extra_fields_schema_json=[], is_active=True, sort_order=3),
            Product(game_id=standoff.id, category_id=category_map[(standoff.id, 'subscriptions')].id, slug='battle_pass', title='Battle Pass', description='Оформление через безопасный сценарий.', image_id=placeholder_media.id, fulfillment_type=FulfillmentType.MANUAL, requires_player_id=True, requires_nickname=True, extra_fields_schema_json=[{'key': 'region', 'label': 'Регион', 'type': 'text', 'required': False}], is_active=True, sort_order=4),
        ]
        session.add_all(products)
        await session.flush()

        for idx, product in enumerate(products, start=1):
            price_value = Decimal('99.00') * idx
            session.add(Price(product_id=product.id, base_price=price_value, discounted_price=price_value, currency_code='RUB', is_active=True))

        super_user = User(telegram_id=settings.super_admin_telegram_id, username='super_admin', first_name='Super', last_name='Admin')
        admin_user = User(telegram_id=settings.second_admin_telegram_id, username='admin', first_name='Admin', last_name='User')
        session.add_all([super_user, admin_user])
        await session.flush()
        session.add_all([
            Admin(user_id=super_user.id, role=AdminRole.SUPER_ADMIN, is_active=True, can_manage_categories=True),
            Admin(user_id=admin_user.id, role=AdminRole.ADMIN, is_active=True, can_manage_categories=True),
        ])

        bot_settings = [
            BotSetting(key='shop_name', value='Game Pay', description='Название магазина'),
            BotSetting(key='welcome_text', value='Добро пожаловать в Game Pay — удобный маркетплейс игровых товаров с безопасным оформлением.', description='Приветственный текст'),
            BotSetting(key='rules_text', value='Магазин не запрашивает и не хранит пароли игровых аккаунтов. Все спорные ситуации решаются через поддержку.', description='Правила магазина'),
            BotSetting(key='support_contact', value='@game_pay_support', description='Контакт поддержки'),
            BotSetting(key='payment_methods_text', value='Ручная оплата по реквизитам администратора. Подключение онлайн-провайдера предусмотрено архитектурой.', description='Способы оплаты'),
            BotSetting(key='currency_code_default', value='RUB', description='Валюта'),
            BotSetting(key='referrals_enabled', value=True, description='Реферальная система'),
            BotSetting(key='promo_codes_enabled', value=True, description='Промокоды'),
            BotSetting(key='reviews_enabled', value=True, description='Отзывы'),
            BotSetting(key='minimal_order_amount', value='1.00', description='Минимальная сумма заказа'),
            BotSetting(key='shop_enabled', value=True, description='Магазин включён'),
            BotSetting(key='maintenance_mode', value=False, description='Режим обслуживания'),
            BotSetting(key='maintenance_text', value='Ведутся технические работы.', description='Текст обслуживания'),
            BotSetting(key='bot_username', value=settings.bot_username, description='Юзернейм бота'),
            BotSetting(key='faq_text', value='Если у вас вопрос по заказу, оплате или срокам, напишите в поддержку.', description='FAQ'),
            BotSetting(key='referral_reward_percent', value=5, description='Процент реферальной награды'),
        ]
        session.add_all(bot_settings)
        await session.commit()


async def main() -> None:
    await init_db()
    await seed()


if __name__ == '__main__':
    asyncio.run(main())


```
