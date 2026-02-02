from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict

from .payments import PaymentInitResult, PaymentProvider


@dataclass
class PesapalConfig:
    consumer_key: str
    consumer_secret: str
    ipn_url: str  # Where Pesapal will send notifications


def _pesapal_post(url: str, body: Dict[str, Any], token: str | None = None) -> Dict[str, Any]:
    """Helper to POST to Pesapal APIs."""
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        return json.loads(raw)


class PesapalPaymentProvider(PaymentProvider):
    def __init__(self, cfg: PesapalConfig) -> None:
        self._cfg = cfg
        self._base = "https://cybqa.pesapal.com/pesapalv3"  # Sandbox for testing
        self._access_token: str | None = None
        self._ipn_id: str | None = None

    def _register_ipn(self) -> str:
        """Register IPN URL and return IPN ID"""
        if self._ipn_id:
            return self._ipn_id
        
        token = self._ensure_token()
        url = f"{self._base}/api/URLSetup/RegisterIPN"
        payload = {
            "url": self._cfg.ipn_url or "https://httpbin.org/post",  # Fallback for testing
            "ipn_notification_type": "POST"
        }
        
        print(f"Registering IPN: {payload}")
        resp = _pesapal_post(url, payload, token=token)
        print(f"IPN Response: {resp}")
        
        ipn_id = resp.get("ipn_id")
        if not ipn_id:
            raise RuntimeError(f"Failed to register IPN: {resp}")
        
        self._ipn_id = ipn_id
        return ipn_id

    def _ensure_token(self) -> str:
        if self._access_token:
            return self._access_token
        url = f"{self._base}/api/Auth/RequestToken"
        payload = {
            "consumer_key": self._cfg.consumer_key,
            "consumer_secret": self._cfg.consumer_secret,
        }
        print(f"Requesting token from: {url}")
        print(f"Payload: {payload}")
        resp = _pesapal_post(url, payload)
        print(f"Token response: {resp}")
        token = resp.get("token")
        if not token:
            print(f"Authentication failed. Full response: {resp}")
            raise RuntimeError(f"Pesapal authentication failed: {resp}")
        self._access_token = token
        return token

    def create_checkout(self, *, amount_tzs: int, description: str) -> PaymentInitResult:
        try:
            print("Creating Pesapal checkout...")
            token = self._ensure_token()
            print(f"Got token: {token[:10]}..." if token else "No token")
            
            # Register IPN first to get notification_id
            ipn_id = self._register_ipn()
            print(f"Got IPN ID: {ipn_id}")
            
            url = f"{self._base}/api/Transactions/SubmitOrderRequest"
            payload = {
                "id": f"AFYA-{amount_tzs}-{os.urandom(4).hex()}",
                "currency": "TZS",
                "amount": float(amount_tzs),
                "description": description,
                "callback_url": "https://httpbin.org/post",  # Test callback
                "notification_id": ipn_id,
                "branch": "Afya+",
                "redirect_mode": "TOP_WINDOW",
                "billing_address": {
                    "email_address": "test@example.com",  # Required
                    "phone_number": "0712345678",  # Required
                    "country_code": "TZ",
                    "first_name": "Test",
                    "last_name": "User"
                }
            }
            print(f"Sending to {url}: {payload}")
            resp = _pesapal_post(url, payload, token=token)
            print(f"Pesapal response: {resp}")
            
            order_id = resp.get("order_tracking_id")
            redirect_url = resp.get("redirect_url")
            
            if not order_id:
                print(f"Pesapal error: {resp}")
                raise RuntimeError(f"Pesapal order creation failed: {resp}")
            
            # Use iframe URL for seamless payment
            instructions = f"Please pay TZS {amount_tzs} via Pesapal. Order ID: {order_id}"
            
            return PaymentInitResult(
                token=order_id,
                pay_instructions=instructions,
                checkout_url=redirect_url,
            )
        except Exception as e:
            print(f"Exception in create_checkout: {e}")
            raise

    def verify_transaction(self, order_id: str) -> Dict[str, Any]:
        token = self._ensure_token()
        url = f"{self._base}/api/Transactions/GetTransactionStatus?orderTrackingId={urllib.parse.quote(order_id)}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"}, method="GET")
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)
