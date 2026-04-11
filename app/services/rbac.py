from __future__ import annotations

from app.models.enums import AdminRole


ROLE_PERMISSIONS: dict[AdminRole, set[str]] = {
    AdminRole.SUPER_ADMIN: {
        'admins.manage', 'prices.manage', 'games.manage', 'categories.manage', 'products.manage', 'images.manage',
        'orders.view', 'orders.manage', 'broadcasts.manage', 'promos.manage', 'discounts.manage', 'users.block',
        'logs.view', 'settings.manage', 'reviews.moderate', 'users.view'
    },
    AdminRole.ADMIN: {
        'orders.view', 'orders.manage', 'products.manage', 'users.view', 'reviews.moderate'
    },
}


class RBACService:
    def has_permission(self, role: AdminRole, permission: str, *, can_manage_categories: bool = False) -> bool:
        if permission == 'categories.manage' and can_manage_categories:
            return True
        return permission in ROLE_PERMISSIONS.get(role, set())
