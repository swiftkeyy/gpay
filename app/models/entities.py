from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text as sa_text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    AdminRole,
    AuditAction,
    BlockActionScope,
    BroadcastStatus,
    DealStatus,
    DiscountScope,
    DisputeStatus,
    EntityType,
    FulfillmentType,
    LotDeliveryType,
    LotStatus,
    MediaType,
    NotificationType,
    OrderStatus,
    PaymentProviderType,
    PromoType,
    ReferralRewardType,
    ReviewStatus,
    SellerStatus,
    TransactionStatus,
    TransactionType,
    WithdrawalStatus,
)


def enum_values(enum_cls: type) -> list[str]:
    return [item.value for item in enum_cls]


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default=sa_text("false"),
    )


class MediaFile(Base):
    __tablename__ = "media_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    file_unique_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    media_type: Mapped[MediaType] = mapped_column(
        SAEnum(MediaType, name="media_type_enum", values_callable=enum_values),
        nullable=False,
    )
    entity_type: Mapped[EntityType] = mapped_column(
        SAEnum(EntityType, name="entity_type_enum", values_callable=enum_values),
        nullable=False,
    )
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Game(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "games"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_games_slug"),
        Index("ix_games_active_sort", "is_active", "sort_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_id: Mapped[int | None] = mapped_column(ForeignKey("media_files.id", ondelete="SET NULL"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default=sa_text("100"))

    categories: Mapped[list["Category"]] = relationship(back_populates="game")
    products: Mapped[list["Product"]] = relationship(back_populates="game")
    image: Mapped["MediaFile | None"] = relationship(foreign_keys=[image_id])


class Category(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("game_id", "slug", name="uq_categories_game_slug"),
        Index("ix_categories_game_active_sort", "game_id", "is_active", "sort_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_id: Mapped[int | None] = mapped_column(ForeignKey("media_files.id", ondelete="SET NULL"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default=sa_text("100"))

    game: Mapped["Game"] = relationship(back_populates="categories")
    products: Mapped[list["Product"]] = relationship(back_populates="category")
    image: Mapped["MediaFile | None"] = relationship(foreign_keys=[image_id])


class Product(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("game_id", "slug", name="uq_products_game_slug"),
        Index("ix_products_category_active_sort", "category_id", "is_active", "sort_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_id: Mapped[int | None] = mapped_column(ForeignKey("media_files.id", ondelete="SET NULL"))
    fulfillment_type: Mapped[FulfillmentType] = mapped_column(
        SAEnum(FulfillmentType, name="fulfillment_type_enum", values_callable=enum_values),
        nullable=False,
        default=FulfillmentType.MANUAL,
        server_default=sa_text("'manual'"),
    )
    requires_player_id: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    requires_nickname: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    requires_region: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    requires_manual_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    requires_screenshot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    extra_fields_schema_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default=sa_text("100"))

    game: Mapped["Game"] = relationship(back_populates="products")
    category: Mapped["Category"] = relationship(back_populates="products")
    image: Mapped["MediaFile | None"] = relationship(foreign_keys=[image_id])
    prices: Mapped[list["Price"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class Price(Base, TimestampMixin):
    __tablename__ = "prices"
    __table_args__ = (
        Index("ix_prices_product_active_period", "product_id", "is_active", "starts_at", "ends_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discounted_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency_code: Mapped[str] = mapped_column(String(10), nullable=False, default="RUB", server_default=sa_text("'RUB'"))
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    changed_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)

    product: Mapped["Product"] = relationship(back_populates="prices")


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("telegram_id", name="uq_users_telegram_id"),
        Index("ix_users_blocked_created", "is_blocked", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    block_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    referred_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    personal_discount_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=sa_text("0"))
    referral_code: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default=sa_text("0.00"))

    referred_by: Mapped["User | None"] = relationship(remote_side=[id], uselist=False)


class Admin(Base):
    __tablename__ = "admins"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_admins_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[AdminRole] = mapped_column(
        SAEnum(AdminRole, name="admin_role_enum", values_callable=enum_values),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship()


class Cart(Base, TimestampMixin):
    __tablename__ = "carts"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_carts_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    items: Mapped[list["CartItem"]] = relationship(back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base, TimestampMixin):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "product_id", name="uq_cart_items_cart_product"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=sa_text("1"))

    cart: Mapped["Cart"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


class PromoCode(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "promo_codes"
    __table_args__ = (
        UniqueConstraint("code", name="uq_promo_codes_code"),
        Index("ix_promo_codes_active_dates", "is_active", "starts_at", "ends_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    promo_type: Mapped[PromoType] = mapped_column(
        SAEnum(PromoType, name="promo_type_enum", values_callable=enum_values),
        nullable=False,
    )
    value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    max_usages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=sa_text("0"))
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    game_id: Mapped[int | None] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), nullable=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=True)
    only_new_users: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))


class PromoCodeUsage(Base):
    __tablename__ = "promo_code_usages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    promo_code_id: Mapped[int] = mapped_column(ForeignKey("promo_codes.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Order(Base, TimestampMixin):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("order_number", name="uq_orders_order_number"),
        Index("ix_orders_user_status_created", "user_id", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[str] = mapped_column(String(32), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status_enum", values_callable=enum_values),
        nullable=False,
        default=OrderStatus.NEW,
        server_default=sa_text("'new'"),
    )
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    currency_code: Mapped[str] = mapped_column(String(10), nullable=False, default="RUB", server_default=sa_text("'RUB'"))
    promo_code_id: Mapped[int | None] = mapped_column(ForeignKey("promo_codes.id", ondelete="SET NULL"), nullable=True)
    payment_provider: Mapped[PaymentProviderType] = mapped_column(
        SAEnum(PaymentProviderType, name="payment_provider_type_enum", values_callable=enum_values),
        nullable=False,
        default=PaymentProviderType.MANUAL,
        server_default=sa_text("'manual'"),
    )
    payment_external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fulfillment_type: Mapped[FulfillmentType] = mapped_column(
        SAEnum(FulfillmentType, name="order_fulfillment_type_enum", values_callable=enum_values),
        nullable=False,
        default=FulfillmentType.MANUAL,
        server_default=sa_text("'manual'"),
    )
    customer_data_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    admin_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship()
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    title_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fulfillment_type: Mapped[FulfillmentType] = mapped_column(
        SAEnum(FulfillmentType, name="order_item_fulfillment_type_enum", values_callable=enum_values),
        nullable=False,
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product | None"] = relationship()


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"
    __table_args__ = (
        Index("ix_order_status_history_order_created", "order_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    old_status: Mapped[OrderStatus | None] = mapped_column(
        SAEnum(OrderStatus, name="order_status_history_old_enum", values_callable=enum_values),
        nullable=True,
    )
    new_status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status_history_new_enum", values_callable=enum_values),
        nullable=False,
    )
    changed_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="status_history")


class Review(Base, TimestampMixin):
    __tablename__ = "reviews"
    __table_args__ = (
        Index("ix_reviews_status_created", "status", "created_at"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ReviewStatus] = mapped_column(
        SAEnum(ReviewStatus, name="review_status_enum", values_callable=enum_values),
        nullable=False,
        default=ReviewStatus.HIDDEN,
        server_default=sa_text("'hidden'"),
    )
    moderated_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    moderated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Referral(Base, TimestampMixin):
    __tablename__ = "referrals"
    __table_args__ = (
        UniqueConstraint("referred_user_id", name="uq_referrals_referred_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    referrer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    referred_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    referral_code: Mapped[str] = mapped_column(String(32), nullable=False)


class ReferralReward(Base, TimestampMixin):
    __tablename__ = "referral_rewards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    referral_id: Mapped[int] = mapped_column(ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    reward_type: Mapped[ReferralRewardType] = mapped_column(
        SAEnum(ReferralRewardType, name="referral_reward_type_enum", values_callable=enum_values),
        nullable=False,
    )
    reward_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BotSetting(Base, TimestampMixin):
    __tablename__ = "bot_settings"
    __table_args__ = (
        UniqueConstraint("key", name="uq_bot_settings_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))


class Broadcast(Base, TimestampMixin):
    __tablename__ = "broadcasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    image_id: Mapped[int | None] = mapped_column(ForeignKey("media_files.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[BroadcastStatus] = mapped_column(
        SAEnum(BroadcastStatus, name="broadcast_status_enum", values_callable=enum_values),
        nullable=False,
        default=BroadcastStatus.DRAFT,
        server_default=sa_text("'draft'"),
    )
    target_filter_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    created_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    send_hash: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_entity_created", "entity_type", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[AuditAction] = mapped_column(
        SAEnum(AuditAction, name="audit_action_enum", values_callable=enum_values),
        nullable=False,
    )
    entity_type: Mapped[EntityType] = mapped_column(
        SAEnum(EntityType, name="audit_entity_type_enum", values_callable=enum_values),
        nullable=False,
    )
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    old_values_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    new_values_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class UserBlock(Base, TimestampMixin):
    __tablename__ = "user_blocks"
    __table_args__ = (
        Index("ix_user_blocks_user_scope", "user_id", "scope"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    blocked_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    scope: Mapped[BlockActionScope] = mapped_column(
        SAEnum(BlockActionScope, name="block_action_scope_enum", values_callable=enum_values),
        nullable=False,
        default=BlockActionScope.FULL,
        server_default=sa_text("'full'"),
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)



class Seller(Base, TimestampMixin):
    __tablename__ = "sellers"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_sellers_user_id"),
        Index("ix_sellers_status_rating", "status", "rating"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[SellerStatus] = mapped_column(
        SAEnum(SellerStatus, name="seller_status_enum", values_callable=enum_values),
        nullable=False,
        default=SellerStatus.PENDING,
        server_default=sa_text("'pending'"),
    )
    shop_name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=Decimal("0.00"), server_default=sa_text("0.00"))
    total_sales: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=sa_text("0"))
    total_reviews: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=sa_text("0"))
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default=sa_text("0.00"))
    commission_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("10.00"), server_default=sa_text("10.00"))
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship()
    lots: Mapped[list["Lot"]] = relationship(back_populates="seller")


class Lot(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "lots"
    __table_args__ = (
        Index("ix_lots_product_seller_status", "product_id", "seller_id", "status"),
        Index("ix_lots_status_price", "status", "price"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(10), nullable=False, default="RUB", server_default=sa_text("'RUB'"))
    delivery_type: Mapped[LotDeliveryType] = mapped_column(
        SAEnum(LotDeliveryType, name="lot_delivery_type_enum", values_callable=enum_values),
        nullable=False,
        default=LotDeliveryType.MANUAL,
        server_default=sa_text("'manual'"),
    )
    stock_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=sa_text("0"))
    reserved_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=sa_text("0"))
    sold_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=sa_text("0"))
    status: Mapped[LotStatus] = mapped_column(
        SAEnum(LotStatus, name="lot_status_enum", values_callable=enum_values),
        nullable=False,
        default=LotStatus.DRAFT,
        server_default=sa_text("'draft'"),
    )
    auto_delivery_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    delivery_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))

    seller: Mapped["Seller"] = relationship(back_populates="lots")
    product: Mapped["Product"] = relationship()
    stock_items: Mapped[list["LotStockItem"]] = relationship(back_populates="lot", cascade="all, delete-orphan")


class LotStockItem(Base, TimestampMixin):
    __tablename__ = "lot_stock_items"
    __table_args__ = (
        Index("ix_lot_stock_items_lot_status", "lot_id", "is_sold", "is_reserved"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lot_id: Mapped[int] = mapped_column(ForeignKey("lots.id", ondelete="CASCADE"), nullable=False)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    is_sold: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    is_reserved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    reserved_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sold_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deal_id: Mapped[int | None] = mapped_column(ForeignKey("deals.id", ondelete="SET NULL"), nullable=True)

    lot: Mapped["Lot"] = relationship(back_populates="stock_items")


class Deal(Base, TimestampMixin):
    __tablename__ = "deals"
    __table_args__ = (
        UniqueConstraint("order_id", name="uq_deals_order_id"),
        Index("ix_deals_buyer_status", "buyer_id", "status"),
        Index("ix_deals_seller_status", "seller_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    seller_id: Mapped[int] = mapped_column(ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False)
    lot_id: Mapped[int] = mapped_column(ForeignKey("lots.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[DealStatus] = mapped_column(
        SAEnum(DealStatus, name="deal_status_enum", values_callable=enum_values),
        nullable=False,
        default=DealStatus.CREATED,
        server_default=sa_text("'created'"),
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    commission_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    seller_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    escrow_released: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    escrow_released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_complete_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    buyer_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    buyer_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    order: Mapped["Order"] = relationship()
    buyer: Mapped["User"] = relationship(foreign_keys=[buyer_id])
    seller: Mapped["Seller"] = relationship()
    lot: Mapped["Lot"] = relationship()
    messages: Mapped[list["DealMessage"]] = relationship(back_populates="deal", cascade="all, delete-orphan")


class DealMessage(Base):
    __tablename__ = "deal_messages"
    __table_args__ = (
        Index("ix_deal_messages_deal_created", "deal_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_id: Mapped[int | None] = mapped_column(ForeignKey("media_files.id", ondelete="SET NULL"), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    deal: Mapped["Deal"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship()


class DealDispute(Base, TimestampMixin):
    __tablename__ = "deal_disputes"
    __table_args__ = (
        UniqueConstraint("deal_id", name="uq_deal_disputes_deal_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)
    initiator_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DisputeStatus] = mapped_column(
        SAEnum(DisputeStatus, name="dispute_status_enum", values_callable=enum_values),
        nullable=False,
        default=DisputeStatus.OPEN,
        server_default=sa_text("'open'"),
    )
    admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_user_type_created", "user_id", "transaction_type", "created_at"),
        Index("ix_transactions_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(
        SAEnum(TransactionType, name="transaction_type_enum", values_callable=enum_values),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(10), nullable=False, default="RUB", server_default=sa_text("'RUB'"))
    status: Mapped[TransactionStatus] = mapped_column(
        SAEnum(TransactionStatus, name="transaction_status_enum", values_callable=enum_values),
        nullable=False,
        default=TransactionStatus.PENDING,
        server_default=sa_text("'pending'"),
    )
    balance_before: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship()


class SellerWithdrawal(Base, TimestampMixin):
    __tablename__ = "seller_withdrawals"
    __table_args__ = (
        Index("ix_seller_withdrawals_seller_status", "seller_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(10), nullable=False, default="RUB", server_default=sa_text("'RUB'"))
    status: Mapped[WithdrawalStatus] = mapped_column(
        SAEnum(WithdrawalStatus, name="withdrawal_status_enum", values_callable=enum_values),
        nullable=False,
        default=WithdrawalStatus.PENDING,
        server_default=sa_text("'pending'"),
    )
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_details: Mapped[str] = mapped_column(Text, nullable=False)
    processed_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    seller: Mapped["Seller"] = relationship()


class SellerReview(Base, TimestampMixin):
    __tablename__ = "seller_reviews"
    __table_args__ = (
        Index("ix_seller_reviews_seller_status", "seller_id", "status"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_seller_reviews_rating_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False)
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ReviewStatus] = mapped_column(
        SAEnum(ReviewStatus, name="seller_review_status_enum", values_callable=enum_values),
        nullable=False,
        default=ReviewStatus.PUBLISHED,
        server_default=sa_text("'published'"),
    )
    seller_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    seller_replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    seller: Mapped["Seller"] = relationship()
    buyer: Mapped["User"] = relationship()


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "lot_id", name="uq_favorites_user_lot"),
        Index("ix_favorites_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lot_id: Mapped[int] = mapped_column(ForeignKey("lots.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship()
    lot: Mapped["Lot"] = relationship()


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_read_created", "user_id", "is_read", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notification_type: Mapped[NotificationType] = mapped_column(
        SAEnum(NotificationType, name="notification_type_enum", values_callable=enum_values),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship()
