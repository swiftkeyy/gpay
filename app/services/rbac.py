from __future__ import annotations

from app.models import AdminRole


class RBACService:
    SUPER_ADMIN_PERMISSIONS = {
        "manage_admins",
        "manage_prices",
        "manage_games",
        "manage_categories",
        "manage_products",
        "manage_images",
        "view_all_orders",
        "manage_broadcasts",
        "manage_promocodes",
        "manage_discounts",
        "manage_user_blocks",
        "view_logs",
        "manage_settings",
        "manage_reviews",
        "manage_referrals",
        "manage_orders",
        "view_users",
        "orders.view",
        "orders.manage",
        "settings.manage",
        "users.view",
        "users.block",
        "logs.view",
        "admins.manage",
        "broadcasts.manage",
        "promos.manage",
        "prices.manage",
        "games.manage",
        "categories.manage",
        "products.manage",
        "reviews.manage",
        "referrals.manage",
        "stats.view",
        "admin_panel",
    }

    ADMIN_PERMISSIONS = {
        "manage_products",
        "manage_orders",
        "view_users",
        "manage_reviews",
        "orders.view",
        "orders.manage",
        "users.view",
        "reviews.manage",
        "products.manage",
        "stats.view",
        "admin_panel",
    }

    ALIASES = {
        "orders.view": "manage_orders",
        "orders.manage": "manage_orders",
        "settings.manage": "manage_settings",
        "users.view": "view_users",
        "users.block": "manage_user_blocks",
        "logs.view": "view_logs",
        "admins.manage": "manage_admins",
        "broadcasts.manage": "manage_broadcasts",
        "promos.manage": "manage_promocodes",
        "prices.manage": "manage_prices",
        "games.manage": "manage_games",
        "categories.manage": "manage_categories",
        "products.manage": "manage_products",
        "reviews.manage": "manage_reviews",
        "referrals.manage": "manage_referrals",
        "stats.view": "view_all_orders",
        "admin.panel": "admin_panel",
        "admin_panel": "admin_panel",
    }

    def normalize_permission(self, permission: str) -> str:
        return self.ALIASES.get(permission, permission)

    def has_permission(
        self,
        role: AdminRole | str,
        permission: str,
        *,
        can_manage_categories: bool = False,
    ) -> bool:
        role_value = role.value if hasattr(role, "value") else str(role)
        permission = self.normalize_permission(permission)

        if role_value == AdminRole.SUPER_ADMIN.value:
            return True

        if role_value == AdminRole.ADMIN.value:
            if permission == "manage_categories":
                return can_manage_categories
            return permission in self.ADMIN_PERMISSIONS

        return False
