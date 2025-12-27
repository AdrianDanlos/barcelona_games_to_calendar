# Barcelona FC Calendar Sync

Automatically syncs Barcelona football matches to your Google Calendar. Runs on GitHub Actions or locally.

## Features

- ✅ Fetches Barcelona FC fixtures from football-data.org API
- ✅ Adds matches to Google Calendar automatically
- ✅ Prevents duplicate events
- ✅ Runs monthly to catch schedule updates
- ✅ Works on GitHub Actions (no local setup needed)

## Quick Setup (GitHub Actions)

### 1. Set Up Google Cloud

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable **Google Calendar API**: APIs & Services > Library > Search "Google Calendar API" > Enable
4. Create a Service Account:
   - APIs & Services > Credentials > Create Credentials > Service Account
   - Name it (e.g., "barcelona-calendar-sync")
   - Skip role assignment > Done
5. Create a Key:
   - Click the service account > Keys tab > Add Key > Create new key > JSON
   - Download the JSON file
   - Copy the service account email (looks like `xxx@xxx.iam.gserviceaccount.com`)

### 2. Add GitHub Secrets

Go to your repo: Settings > Secrets and variables > Actions > New repository secret

- **`GOOGLE_SERVICE_ACCOUNT_JSON`** (Required): Paste entire contents of the JSON file
- **`USER_EMAIL`** (Required): Your Google Calendar email (e.g., `your-email@gmail.com`)
- **`CALENDAR_NAME`** (Optional): Calendar name (defaults to "Barcelona FC Games")
- **`FOOTBALL_API_KEY`** (Optional): API key for paid tier (free tier works fine)

### 3. Run It

The workflow runs automatically on the 1st of each month, or trigger manually:
- Go to Actions tab > "Sync Barcelona Calendar" > Run workflow

**Note**: The calendar is created automatically and shared with your email. No manual calendar creation needed!

## How It Works

1. Fetches upcoming Barcelona fixtures from the API
2. Creates/uses a calendar in Google Calendar
3. Adds each match as a calendar event
4. Skips duplicates and past matches
5. Runs monthly to catch schedule updates

## Sharing Your Calendar with Others

Want to share the Barcelona matches calendar with friends or family?

**Option 1: Share Directly (Recommended)**
1. Open [Google Calendar](https://calendar.google.com/)
2. Find your Barcelona calendar in the left sidebar
3. Click the three dots (⋮) next to the calendar name
4. Click "Settings and sharing"
5. Under "Share with specific people", click "+ Add people"
6. Enter their email address
7. Choose permission level (usually "See all event details" is enough)
8. Click "Send"

**Option 2: Make Calendar Public**
1. In the calendar settings, scroll to "Access permissions"
2. Check "Make available to public"
3. Copy the public calendar URL
4. Share the URL - others can subscribe using "Add calendar" > "From URL"

**Note**: The calendar is automatically shared with the email in `USER_EMAIL`. Others will need you to share it with them as described above.

## Local Setup (Optional)

If you want to run locally instead of GitHub Actions:

```bash
pip install -r requirements.txt
```

Create `credentials.json` from Google Cloud Console (OAuth client ID for desktop app), then:

```bash
python barcelona_calendar_sync.py
```

## Troubleshooting

**No fixtures found**: Check API connection. Free tier has rate limits (10 requests/minute).

**Events not showing**: Make sure `USER_EMAIL` secret is set correctly. The calendar is automatically shared with that email.

**Workflow fails**: Check GitHub Actions logs for detailed error messages.

## License

MIT
