from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine, session_factory
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


settings = get_settings()


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_or_create_media(
    session: AsyncSession,
    *,
    file_unique_id: str,
    telegram_file_id: str,
    alt_text: str,
    entity_type: EntityType = EntityType.DEFAULT,
    media_type: MediaType = MediaType.PHOTO,
) -> MediaFile:
    result = await session.execute(
        select(MediaFile).where(MediaFile.file_unique_id == file_unique_id)
    )
    media = result.scalar_one_or_none()
    if media:
        return media

    media = MediaFile(
        telegram_file_id=telegram_file_id,
        file_unique_id=file_unique_id,
        media_type=media_type,
        entity_type=entity_type,
        alt_text=alt_text,
        created_by_admin_id=None,
    )
    session.add(media)
    await session.flush()
    return media


async def get_or_create_user(
    session: AsyncSession,
    *,
    telegram_id: int,
    username: str,
    first_name: str,
    last_name: str,
) -> User | None:
    if not telegram_id:
        return None

    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user:
        updated = False
        if user.username != username:
            user.username = username
            updated = True
        if user.first_name != first_name:
            user.first_name = first_name
            updated = True
        if user.last_name != last_name:
            user.last_name = last_name
            updated = True
        if updated:
            await session.flush()
        return user

    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        is_blocked=False,
        block_reason=None,
        personal_discount_percent=0,
        referral_code=f"REF{telegram_id}",
    )
    session.add(user)
    await session.flush()
    return user


async def get_or_create_admin(
    session: AsyncSession,
    *,
    user: User | None,
    role: AdminRole,
) -> Admin | None:
    if user is None:
        return None

    result = await session.execute(select(Admin).where(Admin.user_id == user.id))
    admin = result.scalar_one_or_none()
    if admin:
        if admin.role != role:
            admin.role = role
        if not admin.is_active:
            admin.is_active = True
        await session.flush()
        return admin

    admin = Admin(
        user_id=user.id,
        role=role,
        is_active=True,
    )
    session.add(admin)
    await session.flush()
    return admin


async def get_or_create_game(
    session: AsyncSession,
    *,
    slug: str,
    title: str,
    description: str,
    image_id: int | None,
    sort_order: int,
) -> Game:
    result = await session.execute(select(Game).where(Game.slug == slug))
    game = result.scalar_one_or_none()
    if game:
        game.title = title
        game.description = description
        game.image_id = image_id
        game.is_active = True
        game.sort_order = sort_order
        game.is_deleted = False
        await session.flush()
        return game

    game = Game(
        slug=slug,
        title=title,
        description=description,
        image_id=image_id,
        is_active=True,
        sort_order=sort_order,
        is_deleted=False,
    )
    session.add(game)
    await session.flush()
    return game


async def get_or_create_category(
    session: AsyncSession,
    *,
    game_id: int,
    slug: str,
    title: str,
    description: str,
    image_id: int | None,
    sort_order: int,
) -> Category:
    result = await session.execute(
        select(Category).where(Category.game_id == game_id, Category.slug == slug)
    )
    category = result.scalar_one_or_none()
    if category:
        category.title = title
        category.description = description
        category.image_id = image_id
        category.is_active = True
        category.sort_order = sort_order
        category.is_deleted = False
        await session.flush()
        return category

    category = Category(
        game_id=game_id,
        slug=slug,
        title=title,
        description=description,
        image_id=image_id,
        is_active=True,
        sort_order=sort_order,
        is_deleted=False,
    )
    session.add(category)
    await session.flush()
    return category


async def get_or_create_product(
    session: AsyncSession,
    *,
    game_id: int,
    category_id: int,
    slug: str,
    title: str,
    description: str,
    image_id: int | None,
    fulfillment_type: FulfillmentType,
    requires_player_id: bool,
    requires_nickname: bool,
    requires_region: bool,
    requires_manual_review: bool,
    requires_screenshot: bool,
    extra_fields_schema_json: dict,
    sort_order: int,
) -> Product:
    result = await session.execute(
        select(Product).where(Product.game_id == game_id, Product.slug == slug)
    )
    product = result.scalar_one_or_none()
    if product:
        product.category_id = category_id
        product.title = title
        product.description = description
        product.image_id = image_id
        product.fulfillment_type = fulfillment_type
        product.requires_player_id = requires_player_id
        product.requires_nickname = requires_nickname
        product.requires_region = requires_region
        product.requires_manual_review = requires_manual_review
        product.requires_screenshot = requires_screenshot
        product.extra_fields_schema_json = extra_fields_schema_json
        product.is_active = True
        product.is_featured = False
        product.sort_order = sort_order
        product.is_deleted = False
        await session.flush()
        return product

    product = Product(
        game_id=game_id,
        category_id=category_id,
        slug=slug,
        title=title,
        description=description,
        image_id=image_id,
        fulfillment_type=fulfillment_type,
        requires_player_id=requires_player_id,
        requires_nickname=requires_nickname,
        requires_region=requires_region,
        requires_manual_review=requires_manual_review,
        requires_screenshot=requires_screenshot,
        extra_fields_schema_json=extra_fields_schema_json,
        is_active=True,
        is_featured=False,
        sort_order=sort_order,
        is_deleted=False,
    )
    session.add(product)
    await session.flush()
    return product


async def get_or_create_price(
    session: AsyncSession,
    *,
    product_id: int,
    base_price: Decimal,
    discounted_price: Decimal | None,
    currency_code: str,
    changed_by_admin_id: int | None,
) -> Price:
    result = await session.execute(
        select(Price).where(Price.product_id == product_id, Price.is_active.is_(True))
    )
    price = result.scalar_one_or_none()
    if price:
        price.base_price = base_price
        price.discounted_price = discounted_price
        price.currency_code = currency_code
        price.changed_by_admin_id = changed_by_admin_id
        await session.flush()
        return price

    price = Price(
        product_id=product_id,
        base_price=base_price,
        discounted_price=discounted_price,
        currency_code=currency_code,
        starts_at=None,
        ends_at=None,
        is_active=True,
        changed_by_admin_id=changed_by_admin_id,
    )
    session.add(price)
    await session.flush()
    return price


async def set_setting(
    session: AsyncSession,
    *,
    key: str,
    value: str,
    description: str,
    is_public: bool = False,
) -> BotSetting:
    result = await session.execute(select(BotSetting).where(BotSetting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
        setting.description = description
        setting.is_public = is_public
        await session.flush()
        return setting

    setting = BotSetting(
        key=key,
        value=value,
        description=description,
        is_public=is_public,
    )
    session.add(setting)
    await session.flush()
    return setting


async def seed() -> None:
    async with session_factory() as session:
        # Admin users
        super_user = await get_or_create_user(
            session,
            telegram_id=settings.super_admin_tg_id,
            username="super_admin",
            first_name="Super",
            last_name="Admin",
        )
        admin_user = await get_or_create_user(
            session,
            telegram_id=settings.second_admin_tg_id,
            username="admin",
            first_name="Admin",
            last_name="Manager",
        )

        super_admin = await get_or_create_admin(
            session,
            user=super_user,
            role=AdminRole.SUPER_ADMIN,
        )
        await get_or_create_admin(
            session,
            user=admin_user,
            role=AdminRole.ADMIN,
        )

        changed_by_admin_id = super_admin.id if super_admin else None

        # Placeholder media
        default_game_media = await get_or_create_media(
            session,
            file_unique_id="seed_default_game_image",
            telegram_file_id="seed_default_game_image",
            alt_text="Default game image",
            entity_type=EntityType.GAME,
            media_type=MediaType.PHOTO,
        )
        default_category_media = await get_or_create_media(
            session,
            file_unique_id="seed_default_category_image",
            telegram_file_id="seed_default_category_image",
            alt_text="Default category image",
            entity_type=EntityType.CATEGORY,
            media_type=MediaType.PHOTO,
        )
        default_product_media = await get_or_create_media(
            session,
            file_unique_id="seed_default_product_image",
            telegram_file_id="seed_default_product_image",
            alt_text="Default product image",
            entity_type=EntityType.PRODUCT,
            media_type=MediaType.PHOTO,
        )

        # Games
        brawl_stars = await get_or_create_game(
            session,
            slug="brawl-stars",
            title="Brawl Stars",
            description=(
                "Безопасная витрина товаров для Brawl Stars. "
                "Заказы оформляются без хранения паролей. "
                "Для выполнения используются только безопасные сценарии: "
                "официальные потоки, идентификаторы аккаунта или ручная обработка."
            ),
            image_id=default_game_media.id,
            sort_order=10,
        )
        standoff2 = await get_or_create_game(
            session,
            slug="standoff-2",
            title="Standoff 2",
            description=(
                "Витрина товаров для Standoff 2 с безопасным оформлением заказа, "
                "статусной системой и ручной обработкой без запроса логина и пароля."
            ),
            image_id=default_game_media.id,
            sort_order=20,
        )

        # Categories
        brawl_currency = await get_or_create_category(
            session,
            game_id=brawl_stars.id,
            slug="currency",
            title="Валюта",
            description="Игровая валюта и пакеты Gems.",
            image_id=default_category_media.id,
            sort_order=10,
        )
        brawl_subs = await get_or_create_category(
            session,
            game_id=brawl_stars.id,
            slug="subscriptions",
            title="Подписки",
            description="Пропуски и подписочные продукты.",
            image_id=default_category_media.id,
            sort_order=20,
        )
        standoff_currency = await get_or_create_category(
            session,
            game_id=standoff2.id,
            slug="currency",
            title="Валюта",
            description="Игровая валюта и пакеты Gold.",
            image_id=default_category_media.id,
            sort_order=10,
        )
        standoff_subs = await get_or_create_category(
            session,
            game_id=standoff2.id,
            slug="subscriptions",
            title="Подписки",
            description="Боевые пропуски и связанные продукты.",
            image_id=default_category_media.id,
            sort_order=20,
        )

        # Dynamic field schemas
        brawl_schema = {
            "fields": [
                {
                    "name": "player_id",
                    "label": "Player ID",
                    "type": "text",
                    "required": True,
                    "min_length": 3,
                    "max_length": 64,
                    "hint": "Укажите ваш Player ID или безопасный идентификатор аккаунта.",
                },
                {
                    "name": "region",
                    "label": "Регион",
                    "type": "text",
                    "required": False,
                    "min_length": 2,
                    "max_length": 32,
                    "hint": "При необходимости укажите регион.",
                },
                {
                    "name": "note_for_admin",
                    "label": "Комментарий",
                    "type": "text",
                    "required": False,
                    "min_length": 0,
                    "max_length": 500,
                    "hint": "Дополнительная информация для обработки заказа.",
                },
            ]
        }
        standoff_schema = {
            "fields": [
                {
                    "name": "player_id",
                    "label": "Player ID",
                    "type": "text",
                    "required": True,
                    "min_length": 3,
                    "max_length": 64,
                    "hint": "Укажите ID аккаунта или безопасный идентификатор.",
                },
                {
                    "name": "nickname",
                    "label": "Никнейм",
                    "type": "text",
                    "required": True,
                    "min_length": 2,
                    "max_length": 64,
                    "hint": "Укажите игровой никнейм.",
                },
                {
                    "name": "note_for_admin",
                    "label": "Комментарий",
                    "type": "text",
                    "required": False,
                    "min_length": 0,
                    "max_length": 500,
                    "hint": "Любая полезная информация для администратора.",
                },
            ]
        }

        # Products: Brawl Stars
        p_brawl_gems_30 = await get_or_create_product(
            session,
            game_id=brawl_stars.id,
            category_id=brawl_currency.id,
            slug="gems-30",
            title="Gems 30",
            description=(
                "Пакет 30 Gems для Brawl Stars. "
                "Оформляется безопасно, без хранения паролей."
            ),
            image_id=default_product_media.id,
            fulfillment_type=FulfillmentType.ACCOUNT_ID_BASED,
            requires_player_id=True,
            requires_nickname=False,
            requires_region=False,
            requires_manual_review=True,
            requires_screenshot=False,
            extra_fields_schema_json=brawl_schema,
            sort_order=10,
        )
        p_brawl_gems_80 = await get_or_create_product(
            session,
            game_id=brawl_stars.id,
            category_id=brawl_currency.id,
            slug="gems-80",
            title="Gems 80",
            description="Пакет 80 Gems для Brawl Stars.",
            image_id=default_product_media.id,
            fulfillment_type=FulfillmentType.ACCOUNT_ID_BASED,
            requires_player_id=True,
            requires_nickname=False,
            requires_region=False,
            requires_manual_review=True,
            requires_screenshot=False,
            extra_fields_schema_json=brawl_schema,
            sort_order=20,
        )
        p_brawl_gems_170 = await get_or_create_product(
            session,
            game_id=brawl_stars.id,
            category_id=brawl_currency.id,
            slug="gems-170",
            title="Gems 170",
            description="Пакет 170 Gems для Brawl Stars.",
            image_id=default_product_media.id,
            fulfillment_type=FulfillmentType.ACCOUNT_ID_BASED,
            requires_player_id=True,
            requires_nickname=False,
            requires_region=False,
            requires_manual_review=True,
            requires_screenshot=False,
            extra_fields_schema_json=brawl_schema,
            sort_order=30,
        )
        p_brawl_pass = await get_or_create_product(
            session,
            game_id=brawl_stars.id,
            category_id=brawl_subs.id,
            slug="brawl-pass",
            title="Brawl Pass",
            description=(
                "Brawl Pass с безопасной ручной обработкой или через официальный flow, "
                "если он доступен."
            ),
            image_id=default_product_media.id,
            fulfillment_type=FulfillmentType.ADMIN_PROCESSED,
            requires_player_id=True,
            requires_nickname=False,
            requires_region=False,
            requires_manual_review=True,
            requires_screenshot=False,
            extra_fields_schema_json=brawl_schema,
            sort_order=40,
        )

        # Products: Standoff 2
        p_standoff_gold_100 = await get_or_create_product(
            session,
            game_id=standoff2.id,
            category_id=standoff_currency.id,
            slug="gold-100",
            title="Gold 100",
            description=(
                "Пакет 100 Gold для Standoff 2. "
                "Только безопасный сценарий обработки без логина и пароля."
            ),
            image_id=default_product_media.id,
            fulfillment_type=FulfillmentType.ADMIN_PROCESSED,
            requires_player_id=True,
            requires_nickname=True,
            requires_region=False,
            requires_manual_review=True,
            requires_screenshot=False,
            extra_fields_schema_json=standoff_schema,
            sort_order=10,
        )
        p_standoff_gold_500 = await get_or_create_product(
            session,
            game_id=standoff2.id,
            category_id=standoff_currency.id,
            slug="gold-500",
            title="Gold 500",
            description="Пакет 500 Gold для Standoff 2.",
            image_id=default_product_media.id,
            fulfillment_type=FulfillmentType.ADMIN_PROCESSED,
            requires_player_id=True,
            requires_nickname=True,
            requires_region=False,
            requires_manual_review=True,
            requires_screenshot=False,
            extra_fields_schema_json=standoff_schema,
            sort_order=20,
        )
        p_standoff_gold_1000 = await get_or_create_product(
            session,
            game_id=standoff2.id,
            category_id=standoff_currency.id,
            slug="gold-1000",
            title="Gold 1000",
            description="Пакет 1000 Gold для Standoff 2.",
            image_id=default_product_media.id,
            fulfillment_type=FulfillmentType.ADMIN_PROCESSED,
            requires_player_id=True,
            requires_nickname=True,
            requires_region=False,
            requires_manual_review=True,
            requires_screenshot=False,
            extra_fields_schema_json=standoff_schema,
            sort_order=30,
        )
        p_standoff_pass = await get_or_create_product(
            session,
            game_id=standoff2.id,
            category_id=standoff_subs.id,
            slug="battle-pass",
            title="Battle Pass",
            description="Battle Pass для Standoff 2 с ручной безопасной обработкой.",
            image_id=default_product_media.id,
            fulfillment_type=FulfillmentType.ADMIN_PROCESSED,
            requires_player_id=True,
            requires_nickname=True,
            requires_region=False,
            requires_manual_review=True,
            requires_screenshot=False,
            extra_fields_schema_json=standoff_schema,
            sort_order=40,
        )

        # Prices
        await get_or_create_price(
            session,
            product_id=p_brawl_gems_30.id,
            base_price=Decimal("99.00"),
            discounted_price=None,
            currency_code="RUB",
            changed_by_admin_id=changed_by_admin_id,
        )
        await get_or_create_price(
            session,
            product_id=p_brawl_gems_80.id,
            base_price=Decimal("199.00"),
            discounted_price=None,
            currency_code="RUB",
            changed_by_admin_id=changed_by_admin_id,
        )
        await get_or_create_price(
            session,
            product_id=p_brawl_gems_170.id,
            base_price=Decimal("349.00"),
            discounted_price=None,
            currency_code="RUB",
            changed_by_admin_id=changed_by_admin_id,
        )
        await get_or_create_price(
            session,
            product_id=p_brawl_pass.id,
            base_price=Decimal("699.00"),
            discounted_price=None,
            currency_code="RUB",
            changed_by_admin_id=changed_by_admin_id,
        )
        await get_or_create_price(
            session,
            product_id=p_standoff_gold_100.id,
            base_price=Decimal("89.00"),
            discounted_price=None,
            currency_code="RUB",
            changed_by_admin_id=changed_by_admin_id,
        )
        await get_or_create_price(
            session,
            product_id=p_standoff_gold_500.id,
            base_price=Decimal("379.00"),
            discounted_price=None,
            currency_code="RUB",
            changed_by_admin_id=changed_by_admin_id,
        )
        await get_or_create_price(
            session,
            product_id=p_standoff_gold_1000.id,
            base_price=Decimal("699.00"),
            discounted_price=None,
            currency_code="RUB",
            changed_by_admin_id=changed_by_admin_id,
        )
        await get_or_create_price(
            session,
            product_id=p_standoff_pass.id,
            base_price=Decimal("599.00"),
            discounted_price=None,
            currency_code="RUB",
            changed_by_admin_id=changed_by_admin_id,
        )

        # Settings
        await set_setting(
            session,
            key="shop_name",
            value=settings.shop_name,
            description="Название магазина.",
            is_public=True,
        )
        await set_setting(
            session,
            key="welcome_text",
            value=(
                "Добро пожаловать в Game Pay.\n\n"
                "Здесь можно безопасно оформить заказ на игровые товары, "
                "подписки и пропуски без передачи паролей от аккаунтов."
            ),
            description="Приветственный текст бота.",
            is_public=True,
        )
        await set_setting(
            session,
            key="support_contact",
            value="@game_pay_support",
            description="Контакт поддержки.",
            is_public=True,
        )
        await set_setting(
            session,
            key="rules_text",
            value=(
                "1. Мы не запрашиваем и не храним пароли от игровых аккаунтов.\n"
                "2. Заказы обрабатываются только безопасными и легальными способами.\n"
                "3. Для части товаров возможна ручная проверка администратором.\n"
                "4. После оплаты следите за изменением статуса заказа в боте."
            ),
            description="Правила магазина.",
            is_public=True,
        )
        await set_setting(
            session,
            key="payment_methods_text",
            value=(
                "Доступные способы оплаты: ручная оплата и подтверждение администратором. "
                "Интеграции с платёжными провайдерами можно подключить позже."
            ),
            description="Текст способов оплаты.",
            is_public=True,
        )
        await set_setting(
            session,
            key="currency_code_default",
            value="RUB",
            description="Валюта по умолчанию.",
            is_public=False,
        )
        await set_setting(
            session,
            key="referrals_enabled",
            value="true",
            description="Включена ли реферальная система.",
            is_public=False,
        )
        await set_setting(
            session,
            key="promo_codes_enabled",
            value="true",
            description="Включены ли промокоды.",
            is_public=False,
        )
        await set_setting(
            session,
            key="reviews_enabled",
            value="true",
            description="Включены ли отзывы.",
            is_public=False,
        )
        await set_setting(
            session,
            key="minimal_order_amount",
            value="1.00",
            description="Минимальная сумма заказа.",
            is_public=False,
        )
        await set_setting(
            session,
            key="shop_enabled",
            value="true",
            description="Включён ли магазин.",
            is_public=False,
        )
        await set_setting(
            session,
            key="maintenance_mode",
            value="false",
            description="Режим обслуживания.",
            is_public=False,
        )
        await set_setting(
            session,
            key="maintenance_text",
            value="Магазин временно недоступен. Попробуйте позже.",
            description="Текст режима обслуживания.",
            is_public=False,
        )

        await session.commit()


async def main() -> None:
    await init_db()
    await seed()


if __name__ == "__main__":
    asyncio.run(main())
