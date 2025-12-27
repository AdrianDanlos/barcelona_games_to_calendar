# How to Check if Your Calendar is Properly Shared

## Quick Check:

1. **Open Google Calendar**: https://calendar.google.com/

2. **Find your "Adrian Danlos" calendar** in the left sidebar

3. **Click the three dots (⋮)** next to "Adrian Danlos"

4. **Click "Settings and sharing"**

5. **Scroll down to "Share with specific people"**

6. **Look for your service account email** in the list:
   - It should look like: `something@your-project.iam.gserviceaccount.com`
   - The permission should be: **"Make changes to events"** (or "Editor")

## If the service account is NOT in the list:

1. Click **"+ Add people"**
2. Paste your service account email
3. Select **"Make changes to events"** from the dropdown
4. Click **"Send"** or **"Add"**

## If the service account IS in the list:

Great! Your calendar is shared. Now:

1. **Delete the service-account-owned calendar** (optional but recommended):
   - Click "Add" when prompted by that calendar link
   - Once it appears, click the three dots next to it
   - Click "Settings and sharing"
   - Scroll down and click "Delete calendar"
   - Confirm deletion

2. **Run the workflow again** - it should now use your shared calendar!

