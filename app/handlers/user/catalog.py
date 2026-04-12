@router.callback_query(F.data.startswith("buy:now:"))
async def buy_now(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User | None = None,
) -> None:
    tg_user = callback.from_user

    if db_user is None and tg_user is not None:
        user_result = await session.execute(
            select(User).where(User.telegram_id == tg_user.id)
        )
        db_user = user_result.scalar_one_or_none()

        if db_user is None:
            db_user = User(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                is_blocked=False,
                block_reason=None,
                personal_discount_percent=0,
                referral_code=f"REF{tg_user.id}",
            )
            session.add(db_user)
            await session.flush()
            await session.commit()

            user_result = await session.execute(
                select(User).where(User.telegram_id == tg_user.id)
            )
            db_user = user_result.scalar_one_or_none()

    if db_user is None or getattr(db_user, "id", None) is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    try:
        _, _, product_id_raw = callback.data.split(":")
        product_id = int(product_id_raw)
    except (ValueError, AttributeError):
        await callback.answer("Некорректный товар", show_alert=True)
        return

    product_result = await session.execute(
        select(Product).where(
            Product.id == product_id,
            Product.is_active.is_(True),
            Product.is_deleted.is_(False),
        )
    )
    product = product_result.scalar_one_or_none()
    if product is None:
        await callback.answer("Товар не найден", show_alert=True)
        return

    cart_service = CartService(session)
    await cart_service.add_item(db_user.id, product, quantity=1)

    if callback.message:
        await callback.message.edit_text(
            "✅ Товар добавлен в корзину.\n\nТеперь откройте корзину и оформите заказ.",
            parse_mode="HTML",
        )
    await callback.answer("Товар добавлен")
