# Telegram Bot

A minimal webhook bot for the [Telegram Bot API](https://core.telegram.org/bots/api).
Greets people on `/start`, shows a menu of services as tappable inline
buttons, and echoes anything else — a clean skeleton to build real features
onto.

## What it does

Someone opens the chat and taps **Start**:

```
👋 Welcome!

I'm here to help you find what you need. Pick one of the services
below to learn more.

  [ 🔗 Get my links  ]  [ 💎 Memberships and plans ]
  [ ➕ Add a domain  ]  [ 🌐 My domain             ]
  [ 🎁 Refer and earn ]  [ 📢 Help channel         ]
  [ 🛟 Support       ]  [ 🧩 Placeholder 1        ]
  [ 🧩 Placeholder 2 ]  [ 🧩 Placeholder 3        ]
```

The three `🧩 Placeholder` entries are empty slots — rename or delete them
in `services.py` as you decide what goes there.

Tapping a button replaces that message with the service's details and a
**⬅️ Back to services** button, so browsing the menu never fills the chat
with copies of it.

### Commands

| Command | Reply |
|---|---|
| `/start` | Welcome message + the services menu |
| `/services` | The services menu again (`/menu` also works) |
| `/help` | Lists the commands |
| `/ping` | `pong` |
| `/whoami` | Your numeric Telegram ID — needed for `TELEGRAM_ADMIN_IDS` and the recipient list |
| `/broadcast <message>` | **Admins only.** Sends `<message>` to everyone in the recipient list |
| anything else | Echoed back verbatim |

## Editing the services

`telegram_bot/services.py` is the file to change. Each entry is one button:

```python
SERVICES: tuple[Service, ...] = (
    Service(
        id="links",
        label="🔗 Get my links",
        description="View the links on your account, copy them, and check how many clicks each one has.",
    ),
    ...
)
```

Add, remove, or reword entries and the menu, the buttons, and the detail
screens all follow. Two constraints: `id` goes into the button's
`callback_data`, which Telegram caps at 64 bytes (a test enforces this), and
`BUTTONS_PER_ROW` controls the layout.

**The descriptions are placeholders — replace them with your real copy.**

### Link buttons

Give a service a `url` and its button opens that link directly instead of
showing a detail screen:

```python
Service(
    id="help_channel",
    label="📢 Help channel",
    description="Announcements, guides, and updates.",
    url="https://t.me/your_channel",
)
```

`help_channel` and `support` are set up this way but with `url=""` — fill
those in and the buttons become links; leave them empty and they fall back
to showing the description. Telegram only accepts `https://` and `tg://`
URLs in a keyboard and rejects the whole keyboard otherwise, so a test
checks the scheme of anything you configure.

## The "Get my links" showcase

Tapping **🔗 Get my links** opens a three-level menu: categories → the sites
in a category → the site itself (a button that opens the URL). It's driven
entirely by `links.json`, so adding a site is a data edit, no code:

```json
{
  "title": "🔗 Your links",
  "categories": [
    {
      "id": "social",
      "name": "Social Media",
      "emoji": "👥",
      "links": [
        {"title": "My Instagram template", "url": "https://your-site.com"}
      ]
    }
  ]
}
```

- Each category needs a unique `id` (kept short — it rides in the button's
  callback data). Two categories can share a `name` and be told apart by
  `emoji`, like the US 🇺🇸 and UK 🇬🇧 "Banking" folders.
- Every link needs a `title` and a `url` (must be `https://` or `tg://` —
  Telegram rejects other schemes, so those are skipped with a log line).
- The counts next to each category (`Social Media (11)`) are computed from
  the list — nothing to keep in sync.
- The file is read at startup, so edits take effect on the next deploy or
  restart. A missing or malformed file just makes the menu empty and logs
  why; it never takes the bot down. The path is configurable via
  `TELEGRAM_LINKS_FILE` (default `links.json`).

The shipped `links.json` has the categories from the screenshot with one
placeholder link each — replace the titles and URLs with your real sites.

## Broadcasting to a list of people

`/broadcast` is gated two ways:

- **Who can trigger it** — `TELEGRAM_ADMIN_IDS` (comma-separated numeric
  user IDs). Anyone else who sends `/broadcast` gets "You're not authorized
  to broadcast."
- **Who receives it** — `recipients.txt` (path configurable via
  `TELEGRAM_RECIPIENTS_FILE`), one chat ID per line, `#` comments and blank
  lines ignored. Copy `recipients.example.txt` to get started.
  `recipients.txt` is gitignored — it's personal data, don't commit it.

An admin messages the bot with `/broadcast <message>` and it fans that
message out to everyone in the file, then replies with a summary
(`Broadcast sent to 4/5. Failed: <id>` if any failed).

**Read this before using it on real people:**

- A Telegram bot cannot start a conversation. It can only message someone
  who has already sent it `/start` (or a group it's been added to), and only
  until they block it. There is no API for "message everyone I know" — the
  recipient list is whatever you put in `recipients.txt`, and only people
  who actually agreed to hear from this bot should be on it.
- Ask each person to send `/whoami` and give you the number it reports.
- Telegram rate-limits bulk sending to roughly 30 messages/second overall
  and about 1/second per chat. `send_broadcast` sends serially with no
  delay, which is fine for small lists; for hundreds of recipients add a
  sleep or a queue.

## Setup

**1. Create the bot**

- Message [@BotFather](https://t.me/BotFather) on Telegram, send
  `/newbot`, and follow the prompts.
- It gives you a token like `123456789:AAH...`. That's `TELEGRAM_BOT_TOKEN`
  — it's a password for the bot, keep it out of git.
- Optional: `/setcommands` in BotFather, pasting the list below, makes the
  commands autocomplete in the client.

  ```
  start - Welcome message and services menu
  services - Show the services menu
  help - Show available commands
  ping - Check the bot is alive
  whoami - Show your Telegram ID
  ```

**2. Install**

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in the values below
```

| Variable | Meaning |
|---|---|
| `TELEGRAM_BOT_TOKEN` | The token BotFather gave you |
| `TELEGRAM_WEBHOOK_SECRET` | Any random string. Telegram echoes it back in the `X-Telegram-Bot-Api-Secret-Token` header on every update, and the app rejects updates without it. Optional but strongly recommended — without it, anyone who finds your webhook URL can POST fake updates to the bot |
| `TELEGRAM_WEBHOOK_URL` | Public HTTPS base URL of this app, no trailing `/webhook`. **On Railway, leave it blank** — `RAILWAY_PUBLIC_DOMAIN` is injected and used automatically |
| `TELEGRAM_AUTO_SET_WEBHOOK` | Register the webhook on startup (default `true`). Set `false` to manage it by hand with `set_webhook.py` |
| `TELEGRAM_ADMIN_IDS` | Comma-separated numeric user IDs allowed to run `/broadcast`. Empty means nobody can |
| `TELEGRAM_RECIPIENTS_FILE` | Path to the broadcast recipient list (default `recipients.txt`) |
| `TELEGRAM_RECIPIENTS` | Comma-separated chat IDs instead of a file — handy on hosts where pasting into a dashboard is easier than shipping a file. Wins over `TELEGRAM_RECIPIENTS_FILE` when set |
| `PORT` | Local port (default `8080`) |

**3. Run it somewhere Telegram can reach over HTTPS** — pick one:

### Option A: Railway (recommended — no tunnel needed)

Railway gives you a permanent public URL as soon as it deploys, so there's
no ngrok step and nothing to keep running on your own machine.

1. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → pick this repo. Railway detects the `Dockerfile` and builds it automatically.
2. **Settings → Networking → Generate Domain** to get a public URL like `telegram-bot-production.up.railway.app`. Do this *before* the next step — the app reads the domain at startup.
3. In the service's **Variables** tab, add:
   - `TELEGRAM_BOT_TOKEN` — paste the token from BotFather here, and nowhere else.
   - `TELEGRAM_WEBHOOK_SECRET` — any random string (e.g. `openssl rand -hex 16`).
   - `TELEGRAM_ADMIN_IDS` and `TELEGRAM_RECIPIENTS` too, if you want `/broadcast` working.

   Saving variables triggers a redeploy. On boot the app registers its own
   webhook with Telegram, so there's nothing else to run — the logs show
   `webhook registered at https://.../webhook`.
4. Open the bot in Telegram and tap **Start** — the welcome and the services
   buttons appear.

Every `git push` to `main` redeploys automatically, and each deploy
re-registers the webhook.

**If the bot stays silent**, check the deploy logs. The app says which piece
is missing rather than failing quietly:

| Log line | Fix |
|---|---|
| `TELEGRAM_BOT_TOKEN is not set` | Add the variable in step 3 |
| `no public URL known` | Generate the domain (step 2), then redeploy |
| `could not register the webhook on startup` | Usually a bad token — check for a stray space when pasting |
| `TELEGRAM_WEBHOOK_SECRET not set` on every update | Harmless but insecure; add the variable |

### Option B: Run it locally with a tunnel

```bash
python run.py             # starts on localhost:8080
ngrok http 8080           # in another terminal
```

Then register the webhook the same way as step 4 above, using the
`https://...ngrok-free.app` URL ngrok prints instead of a Railway domain.
Useful for quick iteration, but the tunnel dies when your machine sleeps or
ngrok restarts (the URL also changes on a free plan restart) — Railway is
the better choice for anything meant to stay up.

## Development

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```

Layout:

```
run.py                  entrypoint
set_webhook.py          registers (or deletes) the webhook by hand
telegram_bot/
  config.py              every environment variable
  webhook.py             registering the webhook, incl. on startup
  app.py                 Flask route: incoming updates -> replies
  client.py               sends messages/edits via the Bot API
  commands.py              message or button -> reply (no HTTP/Telegram concerns)
  services.py              the services catalog and its inline keyboards
  links.py                 the "Get my links" showcase, loaded from links.json
  broadcast.py             fans a message out to a recipient list
  recipients.py            loads the recipient list from a text file
  security.py              webhook secret-token check
  logging_setup.py
links.json               the showcase data: categories and their sites
recipients.example.txt   copy to recipients.txt and fill in real chat IDs
tests/
```

`commands.py` is intentionally pure — plain values in, a `Reply` out — so new
commands and buttons can be unit tested without touching Flask or the
network.

Curated text (the welcome, service details) is sent with `parse_mode=HTML`
and escaped when built; echoed user text is sent with no parse mode, so a
message containing `<` can't break the send.

## Deploying

The `Dockerfile` runs the app behind `gunicorn` and reads `PORT` at
container start, so it works on Railway as-is (see Option A above) and on
any other host that can build a Dockerfile and gets you an HTTPS URL
(Fly.io, Render, a VPS, etc.).

Set `TELEGRAM_WEBHOOK_SECRET` in production — without it the webhook accepts
unsigned requests from anyone who finds the URL, and the app logs a warning
on every update to say so.
