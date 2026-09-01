# WhatsApp Bot

A minimal webhook bot for the [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api).
Replies to a couple of commands and echoes everything else — a clean
skeleton to build real features onto.

## Commands

| Command | Reply |
|---|---|
| `/ping` | `pong` |
| `/help` | Lists the commands |
| anything else | Echoed back verbatim |

## Setup

**1. Create a Meta app and WhatsApp product**

- Go to [developers.facebook.com](https://developers.facebook.com/apps) and
  create an app, then add the **WhatsApp** product.
- Under **WhatsApp → API Setup** you'll get a temporary access token and a
  test phone number ID. For production, generate a permanent token instead
  (System User in Business Settings) — the default one expires in 24 hours.

**2. Install**

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in the values below
```

| Variable | Meaning |
|---|---|
| `WHATSAPP_ACCESS_TOKEN` | Bearer token from the Meta app |
| `WHATSAPP_PHONE_NUMBER_ID` | The sending number's ID (API Setup page) |
| `WHATSAPP_VERIFY_TOKEN` | Any string you choose — re-entered in the Meta dashboard to prove you control the webhook |
| `WHATSAPP_APP_SECRET` | App secret, used to verify incoming webhook signatures. Optional but strongly recommended — without it, anyone who finds your webhook URL can POST fake messages to the bot |
| `PORT` | Local port (default `8080`) |

**3. Run**

```bash
python run.py
```

**4. Expose it and register the webhook**

Meta needs to reach your webhook over HTTPS. For local development, tunnel
it (e.g. `ngrok http 8080`), then in the Meta dashboard under
**WhatsApp → Configuration**:

- Callback URL: `https://<your-tunnel>/webhook`
- Verify token: the same string as `WHATSAPP_VERIFY_TOKEN`
- Subscribe to the `messages` webhook field

Meta calls `GET /webhook` once to confirm you control the URL, then sends
incoming messages as `POST /webhook`.

**5. Message the test number** from WhatsApp and the bot replies.

## Development

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```

Layout:

```
run.py                  entrypoint
whatsapp_bot/
  config.py              every environment variable
  app.py                 Flask routes: webhook verification + incoming messages
  client.py               sends replies via the Cloud API
  commands.py              message text -> reply text (no HTTP/WhatsApp concerns)
  security.py              X-Hub-Signature-256 verification
  logging_setup.py
tests/
```

`commands.py` is intentionally pure — plain string in, plain string out —
so new commands can be unit tested without touching Flask or the network.

## Deploying

Any host that can run a long-lived Flask/WSGI process and gets you an HTTPS
URL works (Railway, Fly.io, Render, a VPS behind a reverse proxy, etc.). Run
behind a real WSGI server in production, e.g.:

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:$PORT run:app
```

Set `WHATSAPP_APP_SECRET` in production — without it the webhook accepts
unsigned requests from anyone who finds the URL.
