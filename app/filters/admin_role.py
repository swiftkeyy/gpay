from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from app.core.config import get_settings
from app.models import Admin, AdminRole
from app.services.rbac import RBACService

settings = get_settings()


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
        tg_user = getattr(event, "from_user", None)
        tg_user_id = getattr(tg_user, "id", None)

        if admin is not None:
            can_manage_categories = getattr(admin, "can_manage_categories", False)
            return self.rbac.has_permission(
                admin.role,
                self.permission,
                can_manage_categories=can_manage_categories,
            )

        if tg_user_id in {settings.super_admin_tg_id, settings.second_admin_tg_id}:
            fallback_role = AdminRole.SUPER_ADMIN if tg_user_id == settings.super_admin_tg_id else AdminRole.ADMIN
            return self.rbac.has_permission(
                fallback_role,
                self.permission,
                can_manage_categories=True,
            )

        return False


class AdminRoleFilter(AdminPermissionFilter):
    pass
