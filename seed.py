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
