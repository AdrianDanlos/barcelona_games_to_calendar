# Troubleshooting: Events Not Showing in Calendar

## Problem: Events are added but not visible in your calendar

If the logs show events were added successfully but you don't see them, the service account is likely adding events to a calendar it created (that you can't see), rather than your actual calendar.

### How to Fix:

**The service account created its own calendar. You need to share YOUR calendar with the service account.**

#### Step 1: Find Your Service Account Email

1. Open the service account JSON file you downloaded from Google Cloud Console
2. Find the `"client_email"` field
3. Copy the email address (looks like: `barcelona-calendar-sync@your-project.iam.gserviceaccount.com`)

#### Step 2: Share Your Calendar with the Service Account

1. Open [Google Calendar](https://calendar.google.com/)
2. In the left sidebar, find **"Adrian Danlos"** calendar
3. Click the **three dots (⋮)** next to the calendar name
4. Click **"Settings and sharing"**
5. Scroll down to **"Share with specific people"**
6. Click **"+ Add people"**
7. Paste the service account email (from Step 1)
8. Set the permission to **"Make changes to events"**
9. Click **"Send"** (or "Add" if it doesn't send an email)

#### Step 3: Verify Calendar Sharing

After sharing, you can verify:
- The service account email should appear in the "Share with specific people" list
- The permission should be "Make changes to events"

#### Step 4: Run the Workflow Again

1. Go to GitHub Actions
2. Run the workflow again
3. Check the logs - it should now say it found your calendar (not create a new one)

#### Step 5: Check Your Calendar

- Navigate to January 2026 in Google Calendar
- You should now see the Barcelona matches

### How to Verify Which Calendar Events Are In

If you want to see the calendar the service account created (to confirm events are there):

1. The service account created a calendar with ID starting with `0be16418b0567de2a588...`
2. You can access it directly using this URL format:
   `https://calendar.google.com/calendar/embed?src=0be16418b0567de2a588558465cb91731c3719eb1ec96d29b763b1615e7d706b@group.calendar.google.com`
3. But this calendar belongs to the service account, not you

**Better solution**: Share your calendar with the service account (steps above) so events go to YOUR calendar that you use every day.

