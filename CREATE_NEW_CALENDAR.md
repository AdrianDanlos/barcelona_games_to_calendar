# Create a New Calendar for Barcelona Games

## Step 1: Create a New Calendar

1. Go to [Google Calendar](https://calendar.google.com/)
2. On the left sidebar, click the **"+"** next to "Other calendars"
3. Click **"Create new calendar"**
4. Fill in:
   - **Name**: `Barcelona FC Games` (or any name you prefer)
   - **Description**: (optional) "Barcelona football matches"
   - **Time zone**: Choose your timezone (e.g., Europe/Madrid)
5. Click **"Create calendar"**

## Step 2: Share with Service Account

1. After creating, click on the calendar name in the left sidebar
2. Click the three dots (⋮) next to the calendar name
3. Click **"Settings and sharing"**
4. Scroll down to **"Share with specific people"**
5. Click **"+ Add people"**
6. Paste your service account email:
   - `barcelona-calendar-sync@barcelona-calendar-sync-482516.iam.gserviceaccount.com`
7. Select permission: **"Make changes to events"**
8. Click **"Send"** or **"Add"**

## Step 3: Update GitHub Secret

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Find the `CALENDAR_NAME` secret
4. Click it and click **"Update"**
5. Change the value to the exact name of your new calendar:
   - Example: `Barcelona FC Games`
   - **Important**: Must match exactly (case-sensitive)
6. Click **"Update secret"**

## Step 4: Run the Workflow

1. Go to GitHub Actions
2. Run the workflow manually
3. Check the logs - it should now find your new shared calendar!

## Why This Works Better

- No conflicts with existing calendars
- Clean separation - all Barcelona games in one place
- Easy to identify and manage
- You can still add it to your main calendar view if you want

