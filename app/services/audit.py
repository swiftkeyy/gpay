from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AuditAction, EntityType
from app.repositories.settings import AuditLogRepository


class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AuditLogRepository(session)

    async def log(
        self,
        *,
        action: AuditAction,
        entity_type: EntityType,
        entity_id: int | None = None,
        actor_user_id: int | None = None,
        actor_admin_id: int | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await self.repo.create(
            actor_user_id=actor_user_id,
            actor_admin_id=actor_admin_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values or {},
            new_values=new_values or {},
            metadata_json=metadata or {},
        )
