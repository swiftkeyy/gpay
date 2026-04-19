from __future__ import annotations

from enum import StrEnum


class AdminRole(StrEnum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"


class OrderStatus(StrEnum):
    NEW = "new"
    WAITING_PAYMENT = "waiting_payment"
    PAID = "paid"
    PROCESSING = "processing"
    FULFILLED = "fulfilled"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"
    DISPUTE = "dispute"


class FulfillmentType(StrEnum):
    MANUAL = "manual"
    EXTERNAL_OFFICIAL_REDIRECT = "external_official_redirect"
    ACCOUNT_ID_BASED = "account_id_based"
    ADMIN_PROCESSED = "admin_processed"


class MediaType(StrEnum):
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"


class EntityType(StrEnum):
    GAME = "game"
    CATEGORY = "category"
    PRODUCT = "product"
    BANNER = "banner"
    SETTING = "setting"
    BROADCAST = "broadcast"
    DEFAULT = "default"


class PromoType(StrEnum):
    PERCENT = "percent"
    FIXED = "fixed"


class ReviewStatus(StrEnum):
    HIDDEN = "hidden"
    PUBLISHED = "published"
    REJECTED = "rejected"


class BroadcastStatus(StrEnum):
    DRAFT = "draft"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    CANCELED = "canceled"


class DiscountScope(StrEnum):
    GLOBAL = "global"
    GAME = "game"
    PRODUCT = "product"
    PERSONAL = "personal"
    ACCUMULATIVE = "accumulative"
    SEASONAL = "seasonal"


class AuditAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    STATUS_CHANGE = "status_change"
    LOGIN = "login"
    BROADCAST = "broadcast"
    BLOCK = "block"
    UNBLOCK = "unblock"
    OTHER = "other"


class PaymentProviderType(StrEnum):
    MANUAL = "manual"
    STUB = "stub"


class ReferralRewardType(StrEnum):
    FIXED = "fixed"
    PERCENT = "percent"


class BlockActionScope(StrEnum):
    ORDERS = "orders"
    PROMO_CODES = "promo_codes"
    REFERRALS = "referrals"
    FULL = "full"


class SellerStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"


class LotStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    OUT_OF_STOCK = "out_of_stock"
    DELETED = "deleted"


class LotDeliveryType(StrEnum):
    AUTO = "auto"
    MANUAL = "manual"
    COORDINATES = "coordinates"


class DealStatus(StrEnum):
    CREATED = "created"
    PAID = "paid"
    IN_PROGRESS = "in_progress"
    WAITING_CONFIRMATION = "waiting_confirmation"
    COMPLETED = "completed"
    CANCELED = "canceled"
    DISPUTE = "dispute"
    REFUNDED = "refunded"


class TransactionType(StrEnum):
    DEPOSIT = "deposit"
    PURCHASE = "purchase"
    SALE = "sale"
    REFUND = "refund"
    WITHDRAWAL = "withdrawal"
    COMMISSION = "commission"
    BONUS = "bonus"
    PENALTY = "penalty"
    BOOST = "boost"


class TransactionStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class WithdrawalStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELED = "canceled"


class DisputeStatus(StrEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    CLOSED = "closed"


class NotificationType(StrEnum):
    NEW_MESSAGE = "new_message"
    NEW_ORDER = "new_order"
    ORDER_STATUS = "order_status"
    PAYMENT = "payment"
    REVIEW = "review"
    SYSTEM = "system"
    PRICE_ALERT = "price_alert"
    SELLER_APPROVED = "seller_approved"
    SELLER_REJECTED = "seller_rejected"


class LotStockStatus(StrEnum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    EXPIRED = "expired"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"


class PaymentProvider(StrEnum):
    YOOKASSA = "yookassa"
    TINKOFF = "tinkoff"
    CLOUDPAYMENTS = "cloudpayments"
    CRYPTOBOT = "cryptobot"
    TELEGRAM_STARS = "telegram_stars"
