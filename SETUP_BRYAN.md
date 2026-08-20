# Your Schedule Bot Setup Guide ☕

This is your personalized setup — everything below is tailored to your choices.

## **What you're getting**

✅ **Personality**: all lowercase, casual, dad jokes + lame puns, full of love  
✅ **Multiple users**: you + girlfriend, separate calendars  
✅ **AI chat**: just text naturally, no buttons needed (but buttons are there too)  
✅ **Countdowns**: trips, exams, key dates show how many days away  
✅ **Stats**: see how many things you're juggling  
✅ **Customizable digest**: 7am is default, but you can set `/setdigesttime 8 30` for 8:30am  
✅ **Multiple timezones**: you in SG, girlfriend in Bombay — each gets reminders in local time  
✅ **Apple Calendar sync**: all events sync 2 ur iCloud calendar automatically  
✅ **Cost**: $0–2/month (Railway free tier + optional paid, no API costs)  

---

## **Step 1: Get your Telegram bot token (5 min)**

In Telegram, search for `@BotFather`.

Message: `/newbot`

It asks:
1. Bot name: type anything (e.g. "My Schedule Bot")
2. Username: must end with `_bot` (e.g. `my_schedule_bot`)

You get back:
```
Use this token to access the HTTP API:
123456789:ABCdefGHIjklmnOPQRstuvWXYZabcdefg
```

**Save this token.** You'll need it in a few minutes.

---

## **Step 2: Get an Anthropic API key (2 min, for AI chat)**

Go to https://console.anthropic.com

1. Sign up or sign in
2. Click "Create API Key"
3. Copy the key (starts with `sk-ant-`)
4. Save it somewhere safe

**Cost:** About $1 per month for normal daily use. First $5 free for 3 months.

---

## **Step 3: Set up Railway.app (free hosting, 10 min)**

Railway is the easiest way to run your bot. It's free to start, costs $0–5/month.

### **3a. Sign up to Railway**

Go to https://railway.app

Click "Sign up with GitHub" (or email).

Give it permission to access GitHub.

### **3b. Connect your code**

1. Fork this code to GitHub (or use the direct Railway option):
   - Go to GitHub → create a new repo called `schedule-bot`
   - Upload the unzipped `schedule_bot` folder
   - OR: Use Railway's direct GitHub import

2. In Railway dashboard, click "New Project"

3. Select "Deploy from GitHub repo"

4. Pick your `schedule-bot` repo

5. Click "Deploy"

Railway automatically runs the bot. You don't need to do anything else.

### **3c. Set environment variables on Railway**

Railway needs your secrets. In your Railway project:

1. Click "Variables"
2. Add these:
   ```
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklmnOPQRstuvWXYZabcdefg
   ANTHROPIC_API_KEY=sk-ant-...
   LOCAL_TIMEZONE=Asia/Singapore
   ```
3. Leave the Google Calendar ones blank for now

4. Click "Save"

Railway redeploys automatically.

---

## **Step 4: (Optional) Set up Apple Calendar sync (2 min)**

If you want events to show in your Apple Calendar (iCloud), super easy!

### **4a. Connect from Telegram**

In Telegram, message your bot:

```
/connectcalendar
```

The bot will ask you two things:

**First question:** "what's ur icloud email?"
- Type the email u use 4 ur Apple account (e.g., `bryan@icloud.com`)

**Second question:** "what's ur icloud password?"
- Type your password
- **⚠️ If u have 2FA enabled on ur Apple ID**, use an app-specific password instead:
  - Go to: https://appleid.apple.com/account/manage
  - Sign in with ur Apple ID
  - Click "Security" (left sidebar)
  - Under "App-specific passwords," click "Generate password"
  - Pick "Other App (specify)" and type "Schedule Bot" or anything
  - Copy the password it gives u (16 characters)
  - Use THAT password instead of ur actual Apple ID password

### **4b. Done!**

Bot responds: "apple calendar connected ✅"

Now:
- Every event u add syncs 2 ur iCloud calendar automatically 📅
- It shows up on ur iPhone/Mac Calendar app
- Ur girlfriend can do the same with her iCloud account
- No browser login needed, super simple eh

---

## **Step 5: Test your bot (2 min)**

Open Telegram, search for your bot (e.g. `my_schedule_bot`), and message it:

```
/start
```

You get a greeting. Try:

```
exam on sep 15 at 2pm, remind me a day before
```

Bot responds:
```
got it — exam on fri 15 sep 2026, 2:00 pm ✅
```

Nice! Now try:

```
/stats
```

You see your events counted up.

Try:

```
/joke
```

Random dad joke 😂

---

## **Costs**

- **Railway.app:** $0/month (free tier) — if u go over, like $5/month max
- **Anthropic (AI chat):** ~$1/month 4 normal daily use
- **Apple Calendar:** $0 (free, uses ur iCloud account)
- **Total:** basically free, or $1-5/month max

No hidden fees, u only pay 4 what u use.

---

## **Step 6: Customize your settings (optional)**

### **Daily digest time**

Default is 7am. To change it:

```
/setdigesttime 8 30
```

Now you get your digest at 8:30am.

(If girlfriend has different timezone preference, she can set her own time too.)

### **Timezone**

If you travel, update your timezone:

```
/timezone Asia/Kolkata
```

(Girlfriend can do `/timezone Asia/Kolkata` when she's in Bombay.)

### **All settings**

- `/list` — all upcoming events
- `/today` — today's stuff
- `/shift` — your work shift (if set up via `/setshift`)
- `/countdown` — trips/exams/key dates with days remaining
- `/stats` — how busy you are
- `/joke` — random dad joke
- `/setdigesttime <hour> [min]` — when to get your daily digest
- `/timezone <tz>` — your timezone
- `/connectcalendar` — link Google Calendar
- `/help` — full command list

---

## **For your girlfriend**

She messages the same bot. Each of you has:
- Your own events
- Your own Google Calendar (if connected)
- Your own digest time
- Your own timezone

**No setup needed** — she just messages `/start` and goes.

---

## **How to use it (examples)**

### **Adding events (natural language)**

```
"midterm exam on sep 20 at 2pm, remind me 1 day and 1 hour before"
```

Bot figures out the category (exam), date, time, and reminders.

### **Adding events (buttons)**

```
/add
```

Follow the wizard. Great if you want to be precise.

### **Setting your work shift**

```
/setshift
```

Give it a start date and what shift that day is (morning/afternoon/off).

Bot now knows your entire 6-day rotation forever.

### **Deleting stuff**

```
/delete 5
```

(Get the ID from `/list`)

Or just say:
```
"cancel my dentist appointment"
```

### **Checking countdowns**

```
/countdown
```

See how many days until your trip, exam, or important date.

### **Checking stats**

```
/stats
```

See how many classes, exams, dates, trips, etc. you have pending.

---

## **Railway admin (if needed)**

To check your bot's logs or restart it:

1. Go to https://railway.app
2. Click your project
3. Click "Logs" tab to see what's happening
4. Click "Redeploy" to restart

(Usually you don't need to do this — it just works.)

---

## **Troubleshooting**

**Bot isn't responding**
→ Check Railway logs. Usually just needs 10 sec to start.

**Reminders not firing at the right time**
→ Check `/timezone`. Make sure it matches where you are.

**Google Calendar isn't syncing**
→ Run `/calendarstatus`. If not connected, try `/connectcalendar` again.

**AI is misunderstanding me**
→ Try rephrasing, or use `/add` buttons instead. Both work.

---

## **That's it!**

Your bot is now running 24/7 on Railway. It'll:
- Remember all your events
- Send reminders at the right times
- Sync to Google Calendar
- Text you dad jokes every morning
- Track your schedule with personality

Enjoy! 🚀

---

**Questions?** Go back to the main README.md for technical details.
