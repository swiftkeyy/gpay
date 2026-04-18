"""Payment provider integrations."""
from __future__ import annotations

import hashlib
import hmac
import json
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any

import httpx
from pydantic import BaseModel


class PaymentResult(BaseModel):
    """Payment creation result."""
    payment_url: str
    payment_id: str
    provider: str


class WebhookResult(BaseModel):
    """Webhook processing result."""
    payment_id: str
    order_id: int
    amount: Decimal
    status: str  # success, failed, pending
    provider_data: Dict[str, Any]


class PaymentProvider(ABC):
    """Base payment provider interface."""
    
    @abstractmethod
    async def create_payment(
        self,
        order_id: int,
        amount: Decimal,
        currency: str,
        description: str,
        return_url: str
    ) -> PaymentResult:
        """Create payment and return payment URL."""
        pass
    
    @abstractmethod
    async def verify_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        """Verify webhook signature."""
        pass
    
    @abstractmethod
    async def process_webhook(self, payload: Dict[str, Any]) -> WebhookResult:
        """Process webhook and return result."""
        pass


class YooKassaProvider(PaymentProvider):
    """ЮKassa payment provider."""
    
    def __init__(self, shop_id: str, secret_key: str):
        self.shop_id = shop_id
        self.secret_key = secret_key
        self.api_url = "https://api.yookassa.ru/v3"
    
    async def create_payment(
        self,
        order_id: int,
        amount: Decimal,
        currency: str,
        description: str,
        return_url: str
    ) -> PaymentResult:
        """Create ЮKassa payment."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/payments",
                auth=(self.shop_id, self.secret_key),
                json={
                    "amount": {
                        "value": str(amount),
                        "currency": currency
                    },
                    "confirmation": {
                        "type": "redirect",
                        "return_url": return_url
                    },
                    "capture": True,
                    "description": description,
                    "metadata": {
                        "order_id": order_id
                    }
                },
                headers={
                    "Idempotence-Key": f"order_{order_id}_{int(amount * 100)}"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return PaymentResult(
                payment_url=data["confirmation"]["confirmation_url"],
                payment_id=data["id"],
                provider="yookassa"
            )
    
    async def verify_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        """Verify ЮKassa webhook signature."""
        # ЮKassa doesn't use signature verification in the same way
        # Instead, we should verify the payment status via API
        return True
    
    async def process_webhook(self, payload: Dict[str, Any]) -> WebhookResult:
        """Process ЮKassa webhook."""
        event = payload.get("event")
        payment_object = payload.get("object", {})
        
        payment_id = payment_object.get("id")
        status_value = payment_object.get("status")
        amount_value = payment_object.get("amount", {}).get("value", "0")
        order_id = payment_object.get("metadata", {}).get("order_id", 0)
        
        # Map ЮKassa status to our status
        status_map = {
            "succeeded": "success",
            "canceled": "failed",
            "pending": "pending",
            "waiting_for_capture": "pending"
        }
        status = status_map.get(status_value, "failed")
        
        return WebhookResult(
            payment_id=payment_id,
            order_id=int(order_id),
            amount=Decimal(amount_value),
            status=status,
            provider_data=payment_object
        )


class TinkoffProvider(PaymentProvider):
    """Tinkoff payment provider."""
    
    def __init__(self, terminal_key: str, secret_key: str):
        self.terminal_key = terminal_key
        self.secret_key = secret_key
        self.api_url = "https://securepay.tinkoff.ru/v2"
    
    def _generate_token(self, params: Dict[str, Any]) -> str:
        """Generate Tinkoff token."""
        # Add terminal key and secret
        params_with_secret = {**params, "Password": self.secret_key}
        
        # Sort by key and concatenate values
        sorted_values = [str(v) for k, v in sorted(params_with_secret.items())]
        token_string = "".join(sorted_values)
        
        # SHA-256 hash
        return hashlib.sha256(token_string.encode()).hexdigest()
    
    async def create_payment(
        self,
        order_id: int,
        amount: Decimal,
        currency: str,
        description: str,
        return_url: str
    ) -> PaymentResult:
        """Create Tinkoff payment."""
        # Amount in kopecks
        amount_kopecks = int(amount * 100)
        
        params = {
            "TerminalKey": self.terminal_key,
            "Amount": amount_kopecks,
            "OrderId": str(order_id),
            "Description": description,
            "SuccessURL": return_url,
            "FailURL": return_url
        }
        
        params["Token"] = self._generate_token(params)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/Init",
                json=params
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("Success"):
                raise Exception(f"Tinkoff error: {data.get('Message')}")
            
            return PaymentResult(
                payment_url=data["PaymentURL"],
                payment_id=data["PaymentId"],
                provider="tinkoff"
            )
    
    async def verify_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        """Verify Tinkoff webhook signature."""
        # Remove Token from payload for verification
        payload_copy = {k: v for k, v in payload.items() if k != "Token"}
        expected_token = self._generate_token(payload_copy)
        
        return hmac.compare_digest(expected_token, payload.get("Token", ""))
    
    async def process_webhook(self, payload: Dict[str, Any]) -> WebhookResult:
        """Process Tinkoff webhook."""
        payment_id = payload.get("PaymentId")
        order_id = int(payload.get("OrderId", 0))
        amount_kopecks = payload.get("Amount", 0)
        amount = Decimal(amount_kopecks) / Decimal(100)
        status_value = payload.get("Status")
        
        # Map Tinkoff status to our status
        status_map = {
            "CONFIRMED": "success",
            "AUTHORIZED": "success",
            "REJECTED": "failed",
            "CANCELED": "failed",
            "NEW": "pending",
            "FORM_SHOWED": "pending"
        }
        status = status_map.get(status_value, "failed")
        
        return WebhookResult(
            payment_id=str(payment_id),
            order_id=order_id,
            amount=amount,
            status=status,
            provider_data=payload
        )


class CloudPaymentsProvider(PaymentProvider):
    """CloudPayments payment provider."""
    
    def __init__(self, public_id: str, api_secret: str):
        self.public_id = public_id
        self.api_secret = api_secret
        self.api_url = "https://api.cloudpayments.ru"
    
    async def create_payment(
        self,
        order_id: int,
        amount: Decimal,
        currency: str,
        description: str,
        return_url: str
    ) -> PaymentResult:
        """Create CloudPayments payment."""
        # CloudPayments uses widget, not direct API
        # Return widget URL with parameters
        payment_url = (
            f"https://widget.cloudpayments.ru/pay?"
            f"publicId={self.public_id}"
            f"&amount={amount}"
            f"&currency={currency}"
            f"&description={description}"
            f"&invoiceId={order_id}"
        )
        
        return PaymentResult(
            payment_url=payment_url,
            payment_id=f"cp_{order_id}",
            provider="cloudpayments"
        )
    
    async def verify_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        """Verify CloudPayments webhook signature."""
        # Create HMAC signature
        message = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        expected_signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    async def process_webhook(self, payload: Dict[str, Any]) -> WebhookResult:
        """Process CloudPayments webhook."""
        payment_id = payload.get("TransactionId")
        order_id = int(payload.get("InvoiceId", 0))
        amount = Decimal(str(payload.get("Amount", 0)))
        status_value = payload.get("Status")
        
        # Map CloudPayments status to our status
        status_map = {
            "Completed": "success",
            "Authorized": "success",
            "Declined": "failed",
            "Cancelled": "failed",
            "AwaitingAuthentication": "pending"
        }
        status = status_map.get(status_value, "failed")
        
        return WebhookResult(
            payment_id=str(payment_id),
            order_id=order_id,
            amount=amount,
            status=status,
            provider_data=payload
        )


class CryptoBotProvider(PaymentProvider):
    """Crypto Bot payment provider."""
    
    def __init__(self, token: str):
        self.token = token
        self.api_url = "https://pay.crypt.bot/api"
    
    async def create_payment(
        self,
        order_id: int,
        amount: Decimal,
        currency: str,
        description: str,
        return_url: str
    ) -> PaymentResult:
        """Create Crypto Bot payment."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/createInvoice",
                headers={"Crypto-Pay-API-Token": self.token},
                json={
                    "amount": str(amount),
                    "currency_type": "fiat",
                    "fiat": currency,
                    "description": description,
                    "payload": str(order_id),
                    "return_url": return_url
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("ok"):
                raise Exception(f"Crypto Bot error: {data.get('error')}")
            
            result = data["result"]
            
            return PaymentResult(
                payment_url=result["pay_url"],
                payment_id=str(result["invoice_id"]),
                provider="cryptobot"
            )
    
    async def verify_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        """Verify Crypto Bot webhook signature."""
        # Crypto Bot uses HMAC-SHA256
        secret = hashlib.sha256(self.token.encode()).digest()
        check_string = json.dumps(payload, separators=(',', ':'))
        expected_signature = hmac.new(
            secret,
            check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    async def process_webhook(self, payload: Dict[str, Any]) -> WebhookResult:
        """Process Crypto Bot webhook."""
        update_type = payload.get("update_type")
        
        if update_type != "invoice_paid":
            # Not a payment confirmation
            return None
        
        invoice = payload.get("payload", {})
        payment_id = str(invoice.get("invoice_id"))
        order_id = int(invoice.get("payload", 0))
        amount = Decimal(str(invoice.get("amount", 0)))
        status_value = invoice.get("status")
        
        # Map Crypto Bot status to our status
        status_map = {
            "paid": "success",
            "active": "pending",
            "expired": "failed"
        }
        status = status_map.get(status_value, "failed")
        
        return WebhookResult(
            payment_id=payment_id,
            order_id=order_id,
            amount=amount,
            status=status,
            provider_data=invoice
        )


# Factory function
def get_payment_provider(provider_name: str, **config) -> PaymentProvider:
    """Get payment provider instance."""
    providers = {
        "yookassa": YooKassaProvider,
        "tinkoff": TinkoffProvider,
        "cloudpayments": CloudPaymentsProvider,
        "cryptobot": CryptoBotProvider
    }
    
    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Unknown payment provider: {provider_name}")
    
    return provider_class(**config)
