# Barcelona FC Calendar Sync Service

Automatically syncs Barcelona football matches to your Google Calendar. This service fetches upcoming fixtures from a football API and adds them as events to your Google Calendar.

**🚀 Running on GitHub Actions?** Check out [SETUP_GITHUB_ACTIONS.md](SETUP_GITHUB_ACTIONS.md) for a quick step-by-step guide (no local setup required!).

## Features

- ✅ Automatically fetches Barcelona FC fixtures
- ✅ Adds matches to Google Calendar
- ✅ Prevents duplicate events
- ✅ Supports multiple API providers
- ✅ Runs monthly to catch schedule updates
- ✅ Works locally and on GitHub Actions (cloud)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Google Calendar API Setup

**For Local Use (OAuth):**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google Calendar API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"
4. Create OAuth credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as the application type
   - Download the credentials JSON file
   - Rename it to `credentials.json` and place it in the project root

**For GitHub Actions (Service Account):**

See the "GitHub Actions" section below for service account setup instructions.

### 3. Football API Setup (Optional)

The service uses [football-data.org](https://www.football-data.org/) API which has a free tier:

- **Free tier**: 10 requests per minute (no API key needed)
- **Paid tier**: More requests, requires API key

If you want to use a paid tier or different API:

1. Sign up at [football-data.org](https://www.football-data.org/) (or your preferred API)
2. Get your API key
3. Create a `.env` file (see below)

### 4. Environment Variables (Optional)

Create a `.env` file in the project root:

```env
FOOTBALL_API_KEY=your_api_key_here
CALENDAR_NAME=Barcelona FC Games
FOOTBALL_API_BASE=https://api.football-data.org/v4
```

If you don't create a `.env` file, the service will use default values and the free tier.

## Usage

### Run Once

```bash
python barcelona_calendar_sync.py
```

On first run, a browser window will open for Google OAuth authentication. After authentication, a `token.json` file will be created for future runs.

### Schedule to Run Monthly

#### Option 1: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to "Monthly" on the 1st day
4. Action: "Start a program"
5. Program: `python` (or full path to Python executable)
6. Arguments: `C:\Users\Adrian\Desktop\barcelona_games_service\barcelona_calendar_sync.py`
7. Start in: `C:\Users\Adrian\Desktop\barcelona_games_service`

#### Option 2: Cron Job (Linux/Mac)

Add to crontab (`crontab -e`):

```bash
# Run on the 1st of every month at 9 AM
0 9 1 * * cd /path/to/barcelona_games_service && python barcelona_calendar_sync.py
```

#### Option 3: GitHub Actions (Cloud-based) ⭐ Recommended

The workflow file is already created at `.github/workflows/sync-calendar.yml`. Follow these steps:

**1. Create a Service Account (Required for GitHub Actions):**

Since GitHub Actions can't use interactive OAuth, you need to create a service account:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create one)
3. Enable the **Google Calendar API** (if not already enabled)
4. Go to "APIs & Services" > "Credentials"
5. Click "Create Credentials" > "Service Account"
6. Give it a name (e.g., "barcelona-calendar-sync")
7. Click "Create and Continue"
8. Skip role assignment (optional), click "Continue"
9. Click "Done"
10. Click on the newly created service account
11. Go to the "Keys" tab
12. Click "Add Key" > "Create new key"
13. Choose "JSON" format
14. Download the JSON file
15. **Important**: Share your Google Calendar with the service account:
    - Copy the service account email (looks like `xxx@xxx.iam.gserviceaccount.com`)
    - Open [Google Calendar](https://calendar.google.com/)
    - Go to Settings > Settings for my calendars
    - Select the calendar you want to use (or create a new one)
    - Under "Share with specific people", click "Add people"
    - Paste the service account email
    - Give it "Make changes to events" permission
    - Click "Send"

**2. Add GitHub Secrets:**

1. Go to your GitHub repository
2. Navigate to Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Add these secrets:

   - **Name**: `GOOGLE_SERVICE_ACCOUNT_JSON` ⚠️ **Required**
     - **Value**: Copy the **entire contents** of the service account JSON file you downloaded
     - **Important**: Paste the entire JSON object, starting with `{` and ending with `}`

   - **Name**: `FOOTBALL_API_KEY` (Optional)
     - **Value**: Your football API key (skip this secret to use the free tier)

   - **Name**: `CALENDAR_NAME` (Optional)
     - **Value**: Name of your calendar (if not set, defaults to "Barcelona FC Games")
     - **Note**: Make sure this calendar is shared with your service account email!

**3. Push to GitHub:**

The workflow will automatically run:
- On the 1st of every month at 9 AM UTC (scheduled)
- Manually via GitHub Actions UI (click "Run workflow")

**4. Manual Trigger (Optional):**

You can manually trigger the workflow anytime:
1. Go to your GitHub repository
2. Click on "Actions" tab
3. Select "Sync Barcelona Calendar" workflow
4. Click "Run workflow" button

## How It Works

1. **Fetches Fixtures**: Gets upcoming Barcelona matches from the football API
2. **Creates Calendar**: Creates a dedicated calendar named "Barcelona FC Games" (or your custom name)
3. **Adds Events**: Adds each upcoming match as a calendar event
4. **Prevents Duplicates**: Checks for existing events before adding new ones
5. **Updates Monthly**: Run monthly to catch schedule changes throughout the season

## Recommendations

- **Run Monthly**: Football schedules can change throughout the season due to rescheduling, so monthly runs ensure you always have the latest fixtures
- **Run at Season Start**: Run it once at the start of each season (August for La Liga) to get all fixtures for the year
- **Monitor Logs**: Check the console output to see how many events were added

## Troubleshooting

### "Credentials file not found"
- Make sure `credentials.json` is in the project root
- Download it from Google Cloud Console as described in setup

### "No fixtures found"
- Check your internet connection
- If using free tier, wait a minute between runs (rate limit: 10 requests/minute)
- Verify the API is accessible: `curl https://api.football-data.org/v4/teams/81/matches`

### Events not showing in calendar
- **For OAuth (local)**: Check that you granted calendar access during OAuth
- **For Service Account (GitHub Actions)**: Make sure you shared your calendar with the service account email and gave it "Make changes to events" permission
- Verify the calendar exists (check Google Calendar UI)
- Check logs for any error messages
- If using a service account, the calendar must be shared with it BEFORE running the script, or the script will create a new calendar owned by the service account

## License

MIT

