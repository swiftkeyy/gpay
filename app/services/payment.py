from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings
from app.models import Order

settings = get_settings()


class PaymentError(Exception):
    pass


@dataclass(slots=True)
class CryptoBotInvoice:
    invoice_id: int
    status: str
    bot_invoice_url: str
    mini_app_invoice_url: str | None = None
    web_app_invoice_url: str | None = None
    amount: str | None = None
    fiat: str | None = None
    asset: str | None = None
    paid_asset: str | None = None
    paid_amount: str | None = None


class TelegramStarsPaymentService:
    @staticmethod
    def build_payload(order_id: int, telegram_user_id: int) -> str:
        return f"stars:order:{order_id}:user:{telegram_user_id}"

    @staticmethod
    def parse_payload(payload: str) -> tuple[int, int] | None:
        parts = payload.split(":")
        if len(parts) != 5 or parts[0] != "stars" or parts[1] != "order" or parts[3] != "user":
            return None
        try:
            return int(parts[2]), int(parts[4])
        except ValueError:
            return None

    @staticmethod
    def stars_amount(order: Order) -> int:
        raw = (Decimal(order.total_amount) * settings.telegram_stars_per_rub).quantize(
            Decimal("1"),
            rounding=ROUND_CEILING,
        )
        return max(int(raw), 1)


class CryptoBotClient:
    def __init__(self) -> None:
        if not settings.cryptobot_api_token:
            raise PaymentError("CRYPTOBOT_API_TOKEN не задан")
        self.base_url = settings.cryptobot_api_base_url.rstrip("/")
        self.token = settings.cryptobot_api_token

    async def create_invoice(self, order: Order) -> CryptoBotInvoice:
        payload: dict[str, Any] = {
            "amount": f"{Decimal(order.total_amount):.2f}",
            "description": f"Оплата заказа {order.order_number}",
            "payload": json.dumps({"order_id": order.id, "order_number": order.order_number}),
            "allow_comments": settings.cryptobot_allow_comments,
            "allow_anonymous": settings.cryptobot_allow_anonymous,
            "expires_in": settings.cryptobot_expires_in,
        }

        if settings.cryptobot_currency_type == "fiat":
            payload.update(
                {
                    "currency_type": "fiat",
                    "fiat": settings.cryptobot_fiat or order.currency_code,
                    "accepted_assets": settings.cryptobot_accepted_assets,
                }
            )
        else:
            payload.update(
                {
                    "currency_type": "crypto",
                    "asset": settings.cryptobot_asset,
                }
            )

        result = await self._request("createInvoice", payload)
        return self._parse_invoice(result)

    async def get_invoice(self, invoice_id: int) -> CryptoBotInvoice:
        result = await self._request("getInvoices", {"invoice_ids": str(invoice_id)})
        items = result.get("items") or []
        if not items:
            raise PaymentError("Инвойс Crypto Bot не найден")
        return self._parse_invoice(items[0])

    async def _request(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Crypto-Pay-API-Token": self.token,
            "Content-Type": "application/json",
        }
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            url=f"{self.base_url}/{method}",
            data=data,
            headers=headers,
            method="POST",
        )

        def _do_request() -> dict[str, Any]:
            try:
                with urlopen(request, timeout=20) as response:
                    body = response.read().decode("utf-8")
            except HTTPError as exc:
                body = exc.read().decode("utf-8", errors="ignore")
                raise PaymentError(f"Crypto Bot HTTP {exc.code}: {body}") from exc
            except URLError as exc:
                raise PaymentError(f"Crypto Bot недоступен: {exc.reason}") from exc

            try:
                parsed = json.loads(body)
            except json.JSONDecodeError as exc:
                raise PaymentError("Crypto Bot вернул невалидный JSON") from exc

            if not parsed.get("ok"):
                raise PaymentError(parsed.get("error") or "Crypto Bot вернул ошибку")
            return parsed.get("result") or {}

        return await asyncio.to_thread(_do_request)

    @staticmethod
    def _parse_invoice(data: dict[str, Any]) -> CryptoBotInvoice:
        return CryptoBotInvoice(
            invoice_id=int(data["invoice_id"]),
            status=str(data.get("status") or "unknown"),
            bot_invoice_url=str(data.get("bot_invoice_url") or data.get("pay_url") or ""),
            mini_app_invoice_url=data.get("mini_app_invoice_url"),
            web_app_invoice_url=data.get("web_app_invoice_url"),
            amount=data.get("amount"),
            fiat=data.get("fiat"),
            asset=data.get("asset"),
            paid_asset=data.get("paid_asset"),
            paid_amount=data.get("paid_amount"),
        )
