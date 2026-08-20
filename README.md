# Schedule Bot

A self-hosted Telegram bot for a messy real-life schedule: biweekly classes,
exams, assignments, dates, trips, work appointments, key work dates, a
rotating 2-on/2-on/2-off shift cycle, and a 6-week 8-5 block every 6 months.

You can drive it two ways, interchangeably:
- **Buttons**: `/add`, `/setshift`, etc.
- **Plain English**: just type — "exam on 5 Sep 2pm, remind me a day and an
  hour before" or "what's my shift tomorrow?"

Local data lives in `schedule_bot.db` (SQLite). Google Calendar sync and
natural-language chat are both optional — the bot is fully useful without
either.

## 1. Get a Telegram bot token

1. In Telegram, message **@BotFather**.
2. `/newbot`, follow the prompts, copy the token it gives you.

## 2. Install

```bash
cd schedule_bot
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and paste in your token:

```
TELEGRAM_BOT_TOKEN=123456:ABC-your-real-token
```

**Set your system timezone** (matters for every reminder and calendar time):

```bash
sudo timedatectl set-timezone Asia/Singapore
```

## 3. (Optional) Natural-language chat

1. Get an API key at https://console.anthropic.com
2. Add to `.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
   `ANTHROPIC_MODEL` defaults to `claude-haiku-4-5-20251001` — fast and
   cheap, plenty capable for parsing "remind me about X on Y". Bump it to
   `claude-sonnet-5` in `.env` only if you notice it mis-reading trickier
   phrasing.

Without this, the bot still works fully via `/add`, `/setshift`, etc. — it
just won't understand free text.

## 4. (Optional) Google Calendar sync

1. Go to https://console.cloud.google.com → create a project (or use an
   existing one).
2. **APIs & Services → Library** → enable the **Google Calendar API**.
3. **APIs & Services → OAuth consent screen** → External → fill in the
   basics (app name, your email) → save. You can leave it in "Testing"
   mode and add your own Google account under **Test users**.
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   → Application type: **TVs and Limited Input devices**. This gives you a
   Client ID and Client Secret without needing a redirect URL (the bot uses
   Google's device-code flow, so no browser is needed on the VPS).
5. Add both to `.env`:
   ```
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   LOCAL_TIMEZONE=Asia/Singapore
   ```
6. After starting the bot (step 5), run `/connectcalendar` in Telegram —
   it'll give you a short code and a URL to enter it at.

## 5. Run

```bash
python bot.py
```

Message your bot `/start` on Telegram. Keep the process running (see
"Keeping it running" below) so reminders keep firing.

## Commands

| Command | What it does |
|---|---|
| `/add` | Add an event via guided buttons |
| `/list` | Upcoming events, next 30 days |
| `/today` | Today's shift + today's events |
| `/delete <id>` | Remove an event (id from `/list`) |
| `/categories` | Count of active events per category |
| `/setshift` | Set up your 2-morning/2-afternoon/2-off rotation |
| `/shift` | Your shift for the next 7 days |
| `/connectcalendar` | Link your Google Calendar |
| `/disconnectcalendar` | Unlink it |
| `/calendarstatus` | Check whether it's connected |
| `/cancel` | Bail out of any in-progress command |

Or just type normally — the same actions all work as free text if
`ANTHROPIC_API_KEY` is set.

## How your specific patterns map on

- **Biweekly classes** → `/add`, category *Class*, "Every 2 weeks", pick the
  day(s). Or: "CS101 every other Monday at 2pm".
- **Exams / assignments / dates / trips / work appointments / key work
  dates** → matching category, one-off by default or set a recurrence.
- **Rotating 2-morning/2-afternoon/2-off shift** → `/setshift` once with a
  start date and what shift that day is. The bot computes every day after
  from the 6-day pattern. `/shift` and `/today` show it; if Calendar is
  connected, it's pushed there too as 6 recurring all-day series.
- **6 weeks of 8-5, every 6 months** → `/add`, pick "6-week block, every 6
  months" as the recurrence.
- **Reminder timing** → six presets (at time / 15 min / 1 hr / 1 day / 3
  days / 1 week before), or tap "Custom timing..." and type anything like
  `3 hours`, `90 min`, `2 weeks`. Natural language handles arbitrary
  phrasing directly ("remind me 90 minutes before").

## Keeping it running

Simplest — a persistent terminal session:

```bash
tmux new -s schedulebot
python bot.py
# Ctrl+B then D to detach; `tmux attach -t schedulebot` to check on it
```

More robust — a systemd service so it survives reboots:

```ini
# /etc/systemd/system/schedulebot.service
[Unit]
Description=Telegram Schedule Bot
After=network.target

[Service]
WorkingDirectory=/path/to/schedule_bot
ExecStart=/path/to/schedule_bot/venv/bin/python bot.py
Restart=always
User=youruser

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now schedulebot
```

## Notes / limitations

- Reminders, the daily 7am digest, and Calendar times all use the server's
  local clock/timezone — set it correctly (step 2) or times will be off.
- The reminder loop checks every minute and also catches up on anything
  missed in the last 2 hours (e.g. a bot restart), so a brief outage won't
  silently swallow a reminder.
- No `/edit` yet — delete and re-add if something changes.
- Re-running `/setshift` cleans up the old Google Calendar series first, so
  you won't get duplicates.
- Natural language falls back to asking a follow-up question (via Telegram)
  rather than guessing when something's missing or ambiguous — but it's an
  LLM, so sanity-check anything unusual it creates via `/list`.
- Single SQLite file — back up `schedule_bot.db` if you care about history.
