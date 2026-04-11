from __future__ import annotations

from dataclasses import dataclass

from app.models import Order


@dataclass(slots=True)
class PaymentInstruction:
    provider_name: str
    text: str


class PaymentProvider:
    async def build_instruction(self, order: Order) -> PaymentInstruction:
        raise NotImplementedError


class ManualPaymentProvider(PaymentProvider):
    async def build_instruction(self, order: Order) -> PaymentInstruction:
        return PaymentInstruction(
            provider_name='manual',
            text=(
                f'💳 Заказ {order.order_number}\n'
                f'Сумма: {order.total_amount} {order.currency_code}\n\n'
                'Оплата сейчас работает в ручном режиме. После перевода отправьте подтверждение в поддержку. '
                'Администратор проверит оплату и переведёт заказ в обработку.'
            ),
        )
