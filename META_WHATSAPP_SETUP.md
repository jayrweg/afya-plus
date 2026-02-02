# Meta WhatsApp Cloud API setup (Webhook)

Afyabot supports WhatsApp Cloud API via:

- `GET  /whatsapp/webhook` (Meta verification)
- `POST /whatsapp/webhook` (incoming messages)

## 1) What you need from Meta

In Meta for Developers:

- A Meta App
- WhatsApp product added
- A WhatsApp Business Account (WABA)
- A Phone Number ID (test number is okay)
- A permanent access token (or a system user token)

## 2) Public HTTPS URL

Meta requires a public HTTPS URL.

After deploying to Fly.io, you will have something like:

- `https://<app-name>.fly.dev/whatsapp/webhook`

## 3) Configure webhook in Meta

In WhatsApp Cloud API settings:

- **Callback URL**: `https://<app-name>.fly.dev/whatsapp/webhook`
- **Verify token**: choose any string (you must also set it in your server env)

Set env vars in Fly:

- `WHATSAPP_VERIFY_TOKEN` = the same token you typed in Meta
- `WHATSAPP_ACCESS_TOKEN` = your WhatsApp Cloud API token
- `WHATSAPP_API_VERSION` = `v19.0` (default)

## 4) Subscribe to events

Subscribe at least to:

- `messages`

## 5) How replies are sent

When a message comes in, Afyabot:

- Uses the sender phone number as `session_id`
- Generates a reply using the same logic as `/chat`
- Sends a text reply through Graph API

## 6) Notes / common issues

- **Token expires**: dev/test tokens expire quickly. For production use a permanent token / system user.
- **24-hour customer care window**: WhatsApp requires templates for proactive messages outside the 24h window.
- **Phone number format**: WhatsApp sends numbers like `2557xxxxxxx` (no +). That’s fine.
- **Logs**: if you need to debug webhook payloads, tell me and I’ll add safe logging.
