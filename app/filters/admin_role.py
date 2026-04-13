from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from app.models import Admin
from app.services.rbac import RBACService


class AdminPermissionFilter(BaseFilter):
    def __init__(self, permission: str) -> None:
        self.permission = permission
        self.rbac = RBACService()

    async def __call__(
        self,
        event: Message | CallbackQuery,
        admin: Admin | None = None,
        **kwargs,
    ) -> bool:
        if admin is None:
            return False

        can_manage_categories = getattr(admin, "can_manage_categories", False)
        permission = self.rbac.normalize_permission(self.permission)

        return self.rbac.has_permission(
            admin.role,
            permission,
            can_manage_categories=can_manage_categories,
        )


class AdminRoleFilter(AdminPermissionFilter):
    pass
