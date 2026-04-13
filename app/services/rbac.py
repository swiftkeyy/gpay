from __future__ import annotations

from app.models import AdminRole


class RBACService:
    SUPER_ADMIN_PERMISSIONS = {
        "admins.manage",
        "broadcasts.manage",
        "categories.manage",
        "games.manage",
        "images.manage",
        "logs.view",
        "orders.manage",
        "orders.view",
        "prices.manage",
        "products.manage",
        "promos.manage",
        "referrals.manage",
        "reviews.manage",
        "settings.manage",
        "stats.view",
        "users.block",
        "users.view",
        "admin.panel",
    }

    ADMIN_PERMISSIONS = {
        "broadcasts.manage",
        "categories.manage",
        "games.manage",
        "logs.view",
        "orders.manage",
        "orders.view",
        "prices.manage",
        "products.manage",
        "promos.manage",
        "reviews.manage",
        "settings.manage",
        "stats.view",
        "users.block",
        "users.view",
        "admin.panel",
    }

    ALIASES = {
        "admin_panel": "admin.panel",
        "manage_admins": "admins.manage",
        "manage_broadcasts": "broadcasts.manage",
        "manage_categories": "categories.manage",
        "manage_games": "games.manage",
        "manage_images": "images.manage",
        "view_logs": "logs.view",
        "manage_orders": "orders.manage",
        "view_all_orders": "orders.view",
        "manage_prices": "prices.manage",
        "manage_products": "products.manage",
        "manage_promocodes": "promos.manage",
        "manage_referrals": "referrals.manage",
        "manage_reviews": "reviews.manage",
        "manage_settings": "settings.manage",
        "manage_user_blocks": "users.block",
        "view_users": "users.view",
        "view_stats": "stats.view",
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
            if permission == "categories.manage":
                return can_manage_categories or True
            return permission in self.ADMIN_PERMISSIONS

        return False
