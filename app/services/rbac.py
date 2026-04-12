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
        "admin_panel",
    }

    ADMIN_PERMISSIONS = {
        "manage_products",
        "manage_orders",
        "view_users",
        "manage_reviews",
        "admin_panel",
    }

    def has_permission(
        self,
        role: AdminRole | str,
        permission: str,
        *,
        can_manage_categories: bool = False,
    ) -> bool:
        role_value = role.value if hasattr(role, "value") else str(role)

        if role_value == AdminRole.SUPER_ADMIN.value:
            return True

        if role_value == AdminRole.ADMIN.value:
            if permission == "manage_categories":
                return can_manage_categories
            return permission in self.ADMIN_PERMISSIONS

        return False
