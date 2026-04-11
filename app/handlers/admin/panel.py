from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.admin_role import AdminPermissionFilter
from app.keyboards.admin import admin_menu_kb

router = Router(name='admin_panel')
router.message.filter(AdminPermissionFilter('orders.view'))


@router.message(Command('admin'))
async def admin_panel(message: Message) -> None:
    await message.answer('👮 <b>Админ-панель Game Pay</b>', reply_markup=admin_menu_kb(), parse_mode='HTML')
