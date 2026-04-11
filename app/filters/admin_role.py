from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from app.repositories.users import AdminRepository
from app.services.rbac import RBACService


class AdminPermissionFilter(BaseFilter):
    def __init__(self, permission: str):
        self.permission = permission
        self.rbac = RBACService()

    async def __call__(self, event: Message | CallbackQuery, session) -> bool:
        telegram_id = event.from_user.id
        admin = await AdminRepository(session).get_by_telegram_id(telegram_id)
        if not admin:
            return False
        return self.rbac.has_permission(admin.role, self.permission, can_manage_categories=admin.can_manage_categories)
