# flake8: noqa: E501
"""
Barcelona FC Calendar Sync Service
Automatically adds Barcelona football games to Google Calendar
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Google Calendar API scopes
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Barcelona FC team ID (can vary by API)
# Using football-data.org: Barcelona team ID is 81 (La Liga)
BARCELONA_TEAM_ID = 81

# Calendar configuration
CALENDAR_TIMEZONE = "Europe/Madrid"
CALENDAR_DESCRIPTION = (
    "Barcelona FC football matches of La Liga and Champions League "
    "automatically synced (Copa del rey, Supercopa, etc... are not included)"
)

# Configuration
CALENDAR_NAME = os.getenv("CALENDAR_NAME", "")
if not CALENDAR_NAME:
    raise ValueError("CALENDAR_NAME environment variable is required.")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "")
if not FOOTBALL_API_KEY:
    raise ValueError(
        "FOOTBALL_API_KEY environment variable is required. "
        "Get your API key from https://www.football-data.org/client/register"
    )
FOOTBALL_API_BASE = os.getenv("FOOTBALL_API_BASE", "https://api.football-data.org/v4")
USER_EMAIL = os.getenv("USER_EMAIL", "")


class FootballAPIClient:
    """Client for fetching football fixtures"""

    def __init__(self, api_key: str = "", api_base: str = FOOTBALL_API_BASE):
        self.api_key = api_key
        self.api_base = api_base
        self.headers = {}
        if api_key:
            self.headers["X-Auth-Token"] = api_key

    def get_barcelona_fixtures(self, limit: int = 100) -> List[Dict]:
        """Fetch Barcelona fixtures from the API"""
        try:
            url = f"{self.api_base}/teams/{BARCELONA_TEAM_ID}/matches"
            params = {"limit": limit}
            response = requests.get(
                url, headers=self.headers, params=params, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                fixtures = data.get("matches", [])
                logger.info(f"Successfully fetched {len(fixtures)} fixtures")
                return fixtures

            # Handle error status codes
            error_messages = {
                401: "Invalid API key. Please check your FOOTBALL_API_KEY.",
                403: "API key does not have access. Check your API key permissions.",
                429: "Rate limit exceeded. Please wait before trying again.",
            }
            logger.error(
                error_messages.get(
                    response.status_code,
                    f"API request failed with status {response.status_code}: {response.text[:500]}",
                )
            )
            return []

        except Exception as e:
            logger.error(f"Error fetching fixtures: {str(e)}", exc_info=True)
            return []


class GoogleCalendarService:
    """Service for managing Google Calendar events"""

    def __init__(
        self,
        credentials_file: str = "credentials.json",
        token_file: str = "token.json",
        service_account_file: Optional[str] = None,
    ):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service_account_file = service_account_file or os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_FILE"
        )
        self.service_account_email = None
        self.service = None
        self._authenticate()
        self._load_service_account_email()

    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None

        # Try service account authentication first (for CI/CD)
        if self.service_account_file and os.path.exists(self.service_account_file):
            try:
                creds = service_account.Credentials.from_service_account_file(
                    self.service_account_file, scopes=SCOPES
                )
                logger.info("Using service account authentication")
            except Exception as e:
                logger.warning(f"Failed to load service account: {e}")

        # If no service account, try OAuth (for local use)
        if not creds:
            # Load existing token
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

            # If there are no (valid) credentials, request authorization
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        raise FileNotFoundError(
                            f"Credentials file '{self.credentials_file}' not found. "
                            "Please download it from Google Cloud Console. "
                            "For GitHub Actions, use GOOGLE_SERVICE_ACCOUNT_FILE environment variable."
                        )
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # Save credentials for next run (only for OAuth, not service account)
                if self.token_file:
                    with open(self.token_file, "w") as token:
                        token.write(creds.to_json())

        self.service = build("calendar", "v3", credentials=creds)
        logger.info("Successfully authenticated with Google Calendar API")

    def _load_service_account_email(self):
        """Load service account email from credentials file"""
        self.service_account_email = None
        if not (
            self.service_account_file and os.path.exists(self.service_account_file)
        ):
            return

        try:
            with open(self.service_account_file, "r") as f:
                creds_data = json.load(f)
                self.service_account_email = creds_data.get("client_email", "")
                if self.service_account_email:
                    logger.info(f"Service account email: {self.service_account_email}")
        except Exception as e:
            logger.debug(f"Could not load service account email: {e}")

    def _share_calendar_with_user(self, calendar_id: str, user_email: str) -> None:
        """Share calendar with user email if not already shared"""
        if not user_email:
            return

        try:
            acl_list = self.service.acl().list(calendarId=calendar_id).execute()
            shared_with_user = any(
                entry.get("scope", {}).get("value") == user_email
                for entry in acl_list.get("items", [])
            )
            if not shared_with_user:
                acl_rule = {
                    "scope": {"type": "user", "value": user_email},
                    "role": "owner",
                }
                self.service.acl().insert(
                    calendarId=calendar_id, body=acl_rule
                ).execute()
                logger.info(f"Shared calendar with: {user_email}")
        except Exception as e:
            logger.warning(f"Could not share calendar: {e}")

    def get_or_create_calendar(self, calendar_name: str) -> str:
        """Get existing calendar ID or create a new calendar"""
        try:
            # List existing calendars
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get("items", [])

            logger.info(f"Searching for calendar: '{calendar_name}'")
            matching_calendars = [
                cal for cal in calendars if cal.get("summary") == calendar_name
            ]

            if matching_calendars:
                shared_calendars = [
                    cal
                    for cal in matching_calendars
                    if cal.get("accessRole") != "owner"
                ]
                calendar_entry = (
                    shared_calendars[0] if shared_calendars else matching_calendars[0]
                )
                calendar_id = calendar_entry["id"]
                logger.info(f"Found calendar: '{calendar_name}'")
                self._share_calendar_with_user(calendar_id, USER_EMAIL)
                return calendar_id

            # Calendar not found - create it with service account and share with user
            logger.info(
                f"Calendar '{calendar_name}' not found. Creating new calendar..."
            )
            calendar = {
                "summary": calendar_name,
                "description": CALENDAR_DESCRIPTION,
                "timeZone": CALENDAR_TIMEZONE,
            }
            created_calendar = self.service.calendars().insert(body=calendar).execute()
            calendar_id = created_calendar["id"]
            logger.info(f"Created calendar: '{calendar_name}'")
            self._share_calendar_with_user(calendar_id, USER_EMAIL)
            return calendar_id

        except HttpError as error:
            logger.error(f"Error managing calendar: {error}")
            raise

    def find_existing_event(
        self, calendar_id: str, event_title: str, event_start: datetime
    ) -> Optional[Dict]:
        """Find existing event by title on the same date. Returns event dict or None."""
        try:
            # Search for events on the same day
            time_min = event_start.replace(hour=0, minute=0, second=0).isoformat()
            time_max = event_start.replace(hour=23, minute=59, second=59).isoformat()

            events_result = (
                self.service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            for event in events:
                if event.get("summary") == event_title:
                    return event
            return None
        except HttpError as error:
            logger.error(f"Error checking existing events: {error}")
            return None

    def add_or_update_event(
        self,
        calendar_id: str,
        title: str,
        start_time: datetime,
        description: str = "",
        location: str = "",
    ) -> Optional[str]:
        """Add or update (replace) an event in the calendar"""
        try:
            # Check if event already exists
            existing_event = self.find_existing_event(calendar_id, title, start_time)

            # Prepare event data
            end_time = start_time.replace(hour=start_time.hour + 2)
            event = {
                "summary": title,
                "description": description,
                "location": location,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": CALENDAR_TIMEZONE,
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": CALENDAR_TIMEZONE,
                },
            }

            if existing_event:
                # Update existing event (replace with new data)
                event_id = existing_event.get("id")
                updated_event = (
                    self.service.events()
                    .update(calendarId=calendar_id, eventId=event_id, body=event)
                    .execute()
                )
                logger.info(
                    f"✓ Updated event: {title} on {start_time.strftime('%Y-%m-%d %H:%M')} UTC"
                )
                return updated_event.get("id")
            else:
                # Create new event
                new_event = (
                    self.service.events()
                    .insert(calendarId=calendar_id, body=event)
                    .execute()
                )
                logger.info(
                    f"✓ Added event: {title} on {start_time.strftime('%Y-%m-%d %H:%M')} UTC"
                )
                return new_event.get("id")

        except HttpError as error:
            logger.error(f"Error adding/updating event: {error}")
            return None


def parse_fixture_datetime(fixture: Dict) -> Optional[datetime]:
    """Parse fixture datetime from API response"""
    date_str = fixture.get("utcDate") or fixture.get("date")
    if not date_str:
        return None

    try:
        # Parse ISO format: 2024-01-15T20:00:00Z
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError as e:
        logger.warning(f"Could not parse datetime from fixture: {e}")
        return None


def format_fixture_title(fixture: Dict) -> str:
    """Format fixture title for calendar event"""
    try:
        home_team = fixture.get("homeTeam", {}).get("name", "TBD")
        away_team = fixture.get("awayTeam", {}).get("name", "TBD")
        competition = fixture.get("competition", {}).get("name", "")

        # Determine if Barcelona is home or away
        if "Barcelona" in home_team or "Barcelona" in away_team:
            if "Barcelona" in home_team:
                title = f"Barcelona vs {away_team}"
            else:
                title = f"{home_team} vs Barcelona"
        else:
            title = f"{home_team} vs {away_team}"

        if competition:
            title += f" ({competition})"

        return title
    except Exception as e:
        logger.warning(f"Error formatting title: {e}")
        return "Barcelona Match"


def format_fixture_description(fixture: Dict) -> str:
    """Format fixture description for calendar event"""
    try:
        competition = fixture.get("competition", {}).get("name", "")
        matchday = fixture.get("matchday")
        parts = ["Barcelona FC Match"]
        if competition:
            parts.append(f"Competition: {competition}")
        if matchday:
            parts.append(f"Matchday: {matchday}")
        return "\n".join(parts)
    except Exception:
        return "Barcelona FC Match"


def sync_barcelona_fixtures():
    """Main function to sync Barcelona fixtures to Google Calendar"""
    logger.info("Starting Barcelona calendar sync...")

    # Initialize services
    football_client = FootballAPIClient(api_key=FOOTBALL_API_KEY)

    # Get service account file from environment if available (for GitHub Actions)
    service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    calendar_service = GoogleCalendarService(service_account_file=service_account_file)

    # Get or create calendar
    calendar_id = calendar_service.get_or_create_calendar(CALENDAR_NAME)

    fixtures = football_client.get_barcelona_fixtures(limit=100)

    if not fixtures:
        logger.warning("No fixtures found. Check API key and connection.")
        return

    logger.info(f"Processing {len(fixtures)} fixture(s)...")

    added_count = 0
    updated_count = 0
    past_count = 0
    invalid_date_count = 0
    current_time = datetime.now(timezone.utc)

    for fixture in fixtures:
        match_date = parse_fixture_datetime(fixture)
        if not match_date:
            invalid_date_count += 1
            continue

        if match_date < current_time:
            past_count += 1
            continue

        title = format_fixture_title(fixture)
        description = format_fixture_description(fixture)
        location = fixture.get("venue", "")

        # Check if event exists before calling add_or_update_event
        existing_event = calendar_service.find_existing_event(
            calendar_id, title, match_date
        )
        was_existing = existing_event is not None

        event_id = calendar_service.add_or_update_event(
            calendar_id=calendar_id,
            title=title,
            start_time=match_date,
            description=description,
            location=location,
        )

        if event_id:
            if was_existing:
                updated_count += 1
            else:
                added_count += 1

    logger.info("=" * 60)
    logger.info("Sync Summary:")
    logger.info(f"  - Total fixtures fetched: {len(fixtures)}")
    logger.info(f"  - Events added: {added_count}")
    logger.info(f"  - Events updated/replaced: {updated_count}")
    logger.info(f"  - Past matches skipped: {past_count}")
    logger.info(f"  - Invalid date skipped: {invalid_date_count}")
    logger.info("=" * 60)

    if added_count == 0 and past_count > 0:
        logger.warning("⚠ No events added because all matches are in the past!")
        logger.info(
            "This is normal if it's late in the season. New fixtures will appear when they're scheduled."
        )
    elif added_count == 0:
        logger.warning("⚠ No events were added. Check the logs above for details.")


if __name__ == "__main__":
    sync_barcelona_fixtures()
