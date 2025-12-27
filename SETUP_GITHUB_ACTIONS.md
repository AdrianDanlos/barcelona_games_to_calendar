# Quick Setup Guide for GitHub Actions

Since you're running this on GitHub Actions, **you don't need to install anything locally** or run the script on your computer. Everything happens in the cloud!

## Step-by-Step Setup

### Step 1: Push Your Code to GitHub

1. Create a new repository on GitHub (or use an existing one)
2. Push this code to your repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Barcelona calendar sync"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

### Step 2: Set Up Google Cloud Project

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create a new project** (or select an existing one):
   - Click the project dropdown at the top
   - Click "New Project"
   - Give it a name (e.g., "barcelona-calendar-sync")
   - Click "Create"

3. **Enable Google Calendar API**:
   - In the left menu, go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click on it, then click "Enable"

4. **Create a Service Account**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - **Name**: `barcelona-calendar-sync` (or any name)
   - Click "Create and Continue"
   - Skip role assignment (click "Continue")
   - Click "Done"
   - Click on the newly created service account (it will open a new page)

5. **Create a Service Account Key**:
   - In the service account page, go to the "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose **JSON** format
   - Click "Create" (this will download a JSON file - **save this file!**)
   - **Important**: Copy the service account email (looks like `xxx@xxx.iam.gserviceaccount.com`) - you'll need it in the next step

6. **Share Your Google Calendar with the Service Account**:
   - Open [Google Calendar](https://calendar.google.com/)
   - Click the gear icon (⚙️) > "Settings"
   - In the left sidebar, under "Settings for my calendars", find or create a calendar
     - If creating new: Click "+" next to "Other calendars" > "Create new calendar"
     - Name it "Barcelona FC Games" (or your preferred name)
   - Click on the calendar name to open its settings
   - Scroll down to "Share with specific people"
   - Click "Add people"
   - Paste the **service account email** (from step 5)
   - Select permission: **"Make changes to events"**
   - Click "Send"

### Step 3: Add GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** (top menu)
3. In the left sidebar, click **Secrets and variables** > **Actions**
4. Click **New repository secret**

   **Add these 3 secrets:**

   **Secret 1: `GOOGLE_SERVICE_ACCOUNT_JSON`** ⚠️ **REQUIRED**
   - **Name**: `GOOGLE_SERVICE_ACCOUNT_JSON`
   - **Value**: Open the JSON file you downloaded in Step 2.5
   - Copy the **entire contents** of the file (it should start with `{` and end with `}`)
   - Paste it into the "Secret" field
   - Click "Add secret"

   **Secret 2: `FOOTBALL_API_KEY`** (Optional)
   - **Name**: `FOOTBALL_API_KEY`
   - **Value**: Leave empty OR get a free API key from https://www.football-data.org/
   - If you leave it empty, the script will use the free tier (limited to 10 requests/minute)
   - Click "Add secret"

   **Secret 3: `CALENDAR_NAME`** (Optional)
   - **Name**: `CALENDAR_NAME`
   - **Value**: The name of the calendar you shared with the service account (default: "Barcelona FC Games")
   - If you leave it empty, it defaults to "Barcelona FC Games"
   - Click "Add secret"

### Step 4: Test the Workflow

1. Go to your GitHub repository
2. Click the **Actions** tab (top menu)
3. You should see "Sync Barcelona Calendar" workflow
4. Click "Run workflow" button (on the right side)
5. Click the green "Run workflow" button
6. The workflow will start running - click on it to see the logs
7. Check your Google Calendar - you should see Barcelona matches added!

### Step 5: Verify It's Scheduled

The workflow is already configured to run automatically:
- **When**: 1st day of every month at 9 AM UTC
- **You don't need to do anything** - it will run automatically!

To verify the schedule:
1. Go to Actions tab
2. Click on "Sync Barcelona Calendar" workflow
3. You'll see "This workflow has a schedule trigger" if it's set up correctly

## Summary

✅ **No local installation needed** - everything runs on GitHub  
✅ **No local script execution needed** - uses service account (not OAuth)  
✅ **Setup once** - runs automatically every month  
✅ **Manual trigger available** - you can run it anytime from GitHub Actions UI

## Troubleshooting

**Workflow fails with "Permission denied" or "Calendar not found":**
- Make sure you shared your calendar with the service account email
- The calendar name in `CALENDAR_NAME` secret must match exactly (case-sensitive)

**No fixtures found:**
- Check the workflow logs for error messages
- The football API might be temporarily unavailable
- If using free tier, there's a rate limit (10 requests/minute)

**Events not showing in calendar:**
- Verify the calendar is shared with the service account
- Check that the service account has "Make changes to events" permission
- Look at the workflow logs to see if events were added successfully

## That's It! 🎉

Once set up, the script will automatically:
1. Run on the 1st of every month
2. Fetch Barcelona fixtures
3. Add them to your Google Calendar
4. Skip duplicates (won't add the same match twice)

You can also manually trigger it anytime from the GitHub Actions UI!

