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
