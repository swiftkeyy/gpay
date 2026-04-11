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
