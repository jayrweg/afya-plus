# Payment gateway integration guide (Afyabot)

Right now Afyabot uses a placeholder payment flow:

- It generates a token
- User simulates payment by sending: `paid <token>`

This is intentional so you can plug in real gateways later with minimal changes.

## Where to integrate

See `afyabot/payments.py`:

- `PaymentProvider` (interface)
- `DummyPaymentProvider` (current)

To integrate real payments, create a new provider class, e.g.:

- `MpesaPaymentProvider`
- `FlutterwavePaymentProvider`
- `PesapalPaymentProvider`
- `SelcomPaymentProvider`

and replace the provider instance in `afyabot/engine.py`.

## Recommended approach (best for Tanzania)

### Option A: Aggregator (simplest)

Use an aggregator that supports multiple local methods:

- Flutterwave (Mobile Money, cards)
- Pesapal (cards + mobile money depending on country)
- DPO (cards)
- Selcom (strong Tanzania coverage)

Benefits:

- One integration, many payment methods
- Built-in checkout pages
- Webhook callbacks

### Option B: Direct Mobile Money

Directly integrate:

- Vodacom M-Pesa
- Airtel Money
- Tigo Pesa
- HaloPesa

Benefits:

- Potentially lower fees
- More control

Costs:

- More integrations
- More compliance + operational work

## What you will add in code

1) **Create checkout**

When user selects a service, create a payment intent/checkout and return:

- `checkout_url`
- `reference`

2) **Webhook endpoint**

You’ll need an endpoint like:

- `POST /payments/webhook/<provider>`

to receive asynchronous confirmations.

3) **Verify and mark paid**

When a webhook confirms payment, mark the order as paid.

## Minimal data you should store

Even if you keep it lightweight, store:

- `order_id`
- `service_code`
- `amount_tzs`
- `customer_phone`
- `provider_reference`
- `status` (pending/paid/failed)

Right now Afyabot stores this in memory only (`Session.active_order`). For production, you should persist it (SQLite/Postgres).

## Security notes

- Never hardcode API keys. Use env vars.
- Validate webhook signatures.
- Always re-query provider API to confirm payment if possible.
