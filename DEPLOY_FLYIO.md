# Deploy Afyabot on Fly.io

This guide deploys Afyabot as a small HTTP service.

## 1) Prerequisites

- A Fly.io account
- Fly CLI installed
- A payment method may be required by Fly (even if you stay within free allowances)

Install Fly CLI (Windows):

- https://fly.io/docs/hands-on/install-flyctl/

Login:

```bash
fly auth login
```

## 2) Project structure expectation

Your project folder should look like:

- `afyabot/` (python package)
- `Dockerfile`

Afyabot listens on `PORT` env var (default `8008`).

## 3) Create a Dockerfile

Use this Dockerfile (already included if you keep it):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY ./afyabot ./afyabot

ENV HOST=0.0.0.0
ENV PORT=8080

EXPOSE 8080

CMD ["python", "-m", "afyabot.server"]
```

## 4) Launch on Fly

From the folder that contains the Dockerfile:

```bash
fly launch
```

- Choose an app name (e.g. `afyabot-prod`)
- Region: choose closest to your users
- When asked to deploy now: yes

Fly will create a `fly.toml`.

## 5) Configure Fly to use port 8080

In `fly.toml`, ensure `internal_port = 8080`.

Example snippet:

```toml
[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 1
```

Note: `auto_stop_machines=false` helps avoid sleeping, but may cost more depending on Fly plan.

## 6) Set WhatsApp secrets (if using WhatsApp Cloud API)

```bash
fly secrets set WHATSAPP_ACCESS_TOKEN="..." \
  WHATSAPP_VERIFY_TOKEN="..." \
  WHATSAPP_API_VERSION="v19.0"
```

## 7) Deploy

```bash
fly deploy
```

## 8) Test

After deploy, you’ll get a URL like:

- `https://<app-name>.fly.dev/health`
- `https://<app-name>.fly.dev/chat`
- `https://<app-name>.fly.dev/whatsapp/webhook`

Test `/chat` quickly:

```bash
curl -X POST https://<app-name>.fly.dev/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hi"}'
```
