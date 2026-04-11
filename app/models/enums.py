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