# Afyabot (Afya+)

Afyabot is a simple intent/menu-based health chatbot based on `Afya+.txt`.

It supports:

- English / Kiswahili selection at the start
- Service menu:
  - GP (General Practitioner)
  - Specialist
  - Home Doctor
  - Workplace / Corporate health solutions
  - Pharmacy / Health & wellness
- Payment-ready flow with Pesapal integration and admin email notifications

## Run locally (HTTP server)

From the `afyabot/` folder:

```bash
python -m afyabot.server
```

By default it runs on:

- `http://127.0.0.1:8008`

Environment variables:

- `HOST` (default: `0.0.0.0`)
- `PORT` (default: `8008`)

## WhatsApp Cloud API (Meta)

Afyabot includes a WhatsApp webhook endpoint:

- `GET/POST /whatsapp/webhook`

Environment variables:

- `WHATSAPP_VERIFY_TOKEN`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_API_VERSION` (default: `v19.0`)

See `META_WHATSAPP_SETUP.md`.

## Payments & Pesapal Integration

Afyabot supports a payment flow. If Pesapal credentials are set, it uses PesapalPaymentProvider; otherwise it falls back to DummyPaymentProvider.

- POST `/payments/pesapal` — Pesapal IPN (instant payment notification) endpoint

Environment variables:

- `PESAPAL_CONSUMER_KEY`
- `PESAPAL_CONSUMER_SECRET`
- `PESAPAL_IPN_URL` — your public webhook URL
- `RESEND_API_KEY` — for admin email notifications
- `RESEND_FROM_EMAIL` — sender email
- `RESEND_ADMIN_EMAIL` — where to send payment confirmations

When Pesapal marks an order as completed, an email with user phone, selected service, and chat context is sent to `RESEND_ADMIN_EMAIL`.

See `PAYMENTS_GATEWAYS.md`.

## Test it (PowerShell)

Health check:

```powershell
curl http://127.0.0.1:8008/health
```

Start chat (language selection):

```powershell
curl -Method POST http://127.0.0.1:8008/chat `
  -ContentType "application/json" `
  -Body '{"message":"hi"}'
```

Continue same session (reuse the returned `session_id`):

```powershell
curl -Method POST http://127.0.0.1:8008/chat `
  -ContentType "application/json" `
  -Body '{"session_id":"PASTE_SESSION_ID","message":"1"}'
```

## Payment simulation (for now)

When Afyabot generates a token, simulate payment by replying:

- `paid <token>`

If Pesapal credentials are configured, real payment links will be provided and the `/payments/pesapal` webhook will update order status and email the admin on success.

## Deploy

See `DEPLOY_FLYIO.md`.

## Summary

- Pesapal is now integrated. When credentials are present, Afyabot uses real payment links and the `/payments/pesapal` webhook processes Pesapal IPNs.
- On successful payment, an email is sent to the admin with the user’s phone, selected service, and chat context.
- No user email is collected; only the admin receives notifications.
- The dummy provider is used as a fallback if Pesapal keys are missing.
