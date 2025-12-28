# Barcelona FC Calendar Sync

Automatically syncs Barcelona football matches to your Google Calendar. Runs on GitHub Actions or locally.

## Features

- ✅ Fetches Barcelona FC fixtures from football-data.org API
- ✅ Adds matches to Google Calendar automatically
- ✅ Prevents duplicate events
- ✅ Runs every 15 days to catch schedule updates
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
- **`CALENDAR_NAME`** (Required): Calendar name for Barcelona matches
- **`FOOTBALL_API_KEY`** (Required): Get your API key from https://www.football-data.org/client/register

### 3. Run It

The workflow runs automatically every 15 days (1st and 16th of each month), or trigger manually:
- Go to Actions tab > "Sync Barcelona Calendar" > Run workflow

**Note**: The calendar is created automatically and shared with your email. No manual calendar creation needed!

## Data Coverage

**Currently Supported:**
- ✅ La Liga matches
- ✅ UEFA Champions League matches

**Not Included (but could be added in the future):**
- ❌ Copa del Rey
- ❌ Supercopa de España
- ❌ Other cup competitions

These competitions could be fetched in the future by scraping the [official FC Barcelona schedule page](https://www.fcbarcelona.com/en/football/first-team/schedule).

## Alternative Data Sources

If you encounter issues with the football-data.org API provider, an alternative option is [football.json](https://github.com/openfootball/football.json), which provides La Liga data in JSON format. However, this only covers La Liga matches, not Champions League or other competitions.

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
