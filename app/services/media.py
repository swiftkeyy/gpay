from __future__ import annotations

from aiogram.types import FSInputFile

from app.models import MediaFile


class MediaService:
    async def resolve_send_args(self, media: MediaFile | None, fallback_text: str) -> dict:
        if media and media.telegram_file_id:
            return {'photo': media.telegram_file_id, 'caption': fallback_text}
        return {'text': fallback_text}
