# WhatsApp Bot

A minimal webhook bot for the [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api).
Replies to a couple of commands and echoes everything else — a clean
skeleton to build real features onto.

## Commands

| Command | Reply |
|---|---|
| `/ping` | `pong` |
| `/help` | Lists the commands |
| `/broadcast <message>` | **Admins only.** Sends `<message>` to everyone in the recipient list |
| anything else | Echoed back verbatim |

### Broadcasting to a list of people

`/broadcast` is gated two ways:

- **Who can trigger it** — `WHATSAPP_ADMIN_NUMBERS` (comma-separated, E.164,
  no leading `+`). Anyone else who sends `/broadcast` gets "You're not
  authorized to broadcast."
- **Who receives it** — `recipients.txt` (path configurable via
  `WHATSAPP_RECIPIENTS_FILE`), one phone number per line, `#` comments and
  blank lines ignored. Copy `recipients.example.txt` to get started.
  `recipients.txt` is gitignored — it's personal data, don't commit it.

An admin messages the bot with `/broadcast <message>` and it fans that
message out to everyone in the file, then replies with a summary
(`Broadcast sent to 4/5. Failed: <number>` if any failed).

**Read this before using it on real numbers:**

- WhatsApp Cloud API has no access to your phone's contacts — there is no
  API for "message everyone I know." The recipient list is whatever you put
  in `recipients.txt`, and only people who actually agreed to hear from this
  bot should be on it.
- Outside a 24-hour window since someone last messaged the bot, WhatsApp
  only allows sending pre-approved **message templates**, not free-form
  text — an unsolicited `/broadcast` to someone who hasn't messaged in
  recently will fail (or worse, get the number flagged for spam). This
  bot sends free-form text, so in practice `/broadcast` reliably reaches
  only people who've messaged the bot within the last 24 hours, or you'll
  need to register a template with Meta for the rest.

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
| `WHATSAPP_ADMIN_NUMBERS` | Comma-separated phone numbers (E.164, no `+`) allowed to run `/broadcast`. Empty means nobody can |
| `WHATSAPP_RECIPIENTS_FILE` | Path to the broadcast recipient list (default `recipients.txt`) |
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
  broadcast.py             fans a message out to a recipient list
  recipients.py            loads the recipient list from a text file
  security.py              X-Hub-Signature-256 verification
  logging_setup.py
recipients.example.txt   copy to recipients.txt and fill in real numbers
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
