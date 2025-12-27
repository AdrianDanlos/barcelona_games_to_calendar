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
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Barcelona FC team ID (can vary by API)
# Using football-data.org: Barcelona team ID is 81 (La Liga)
BARCELONA_TEAM_ID = 81

# Configuration
CALENDAR_NAME = os.getenv('CALENDAR_NAME') or 'Barcelona FC Games'
FOOTBALL_API_KEY = os.getenv('FOOTBALL_API_KEY', '')
FOOTBALL_API_BASE = os.getenv('FOOTBALL_API_BASE', 'https://api.football-data.org/v4')


class FootballAPIClient:
    """Client for fetching football fixtures"""
    
    def __init__(self, api_key: str = '', api_base: str = FOOTBALL_API_BASE):
        self.api_key = api_key
        self.api_base = api_base
        self.headers = {}
        if api_key:
            self.headers['X-Auth-Token'] = api_key
    
    def get_barcelona_fixtures(self, limit: int = 50) -> List[Dict]:
        """
        Fetch Barcelona fixtures from the API
        Returns a list of fixture dictionaries
        """
        try:
            # Try to get Barcelona fixtures
            # Using football-data.org API format
            url = f"{self.api_base}/teams/{BARCELONA_TEAM_ID}/matches"
            params = {'limit': limit}
            
            logger.info(f"Fetching fixtures from {url}")
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get('matches', [])
                logger.info(f"Successfully fetched {len(fixtures)} fixtures")
                return fixtures
            elif response.status_code == 403:
                logger.warning("API returned 403. Trying without auth headers for free tier...")
                # Try without auth for free tier (limited requests)
                response_no_auth = requests.get(url, params=params, timeout=10)
                logger.info(f"Response status (no auth): {response_no_auth.status_code}")
                if response_no_auth.status_code == 200:
                    data = response_no_auth.json()
                    logger.info(f"API response keys: {list(data.keys())}")
                    fixtures = data.get('matches', [])
                    if fixtures:
                        logger.info(f"Fetched {len(fixtures)} fixtures (free tier)")
                        return fixtures
                    else:
                        logger.warning(f"API returned 200 but no fixtures. Response structure: {list(data.keys())}")
                        logger.warning(f"Response sample: {str(data)[:300]}")
                        # Check if there are other fields
                        if 'results' in data:
                            fixtures = data.get('results', [])
                            if fixtures:
                                logger.info(f"Found fixtures in 'results' field: {len(fixtures)}")
                                return fixtures
                elif response_no_auth.status_code == 429:
                    logger.error("Rate limit exceeded. Please wait before trying again.")
                else:
                    logger.error(f"API request failed with status {response_no_auth.status_code}")
                    logger.error(f"Response: {response_no_auth.text[:300]}")
            elif response.status_code == 429:
                logger.error("Rate limit exceeded (429). Please wait before trying again.")
            else:
                logger.error(f"API request failed with status {response.status_code}: {response.text[:500]}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching fixtures: {str(e)}", exc_info=True)
            return []


class GoogleCalendarService:
    """Service for managing Google Calendar events"""
    
    def __init__(self, credentials_file: str = 'credentials.json', 
                 token_file: str = 'token.json',
                 service_account_file: Optional[str] = None):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service_account_file = service_account_file or os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
        self.service = None
        self._authenticate()
    
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
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run (only for OAuth, not service account)
                if self.token_file:
                    with open(self.token_file, 'w') as token:
                        token.write(creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=creds)
        logger.info("Successfully authenticated with Google Calendar API")
    
    def _load_service_account_email(self):
        """Load service account email from credentials file"""
        try:
            if self.service_account_file and os.path.exists(self.service_account_file):
                with open(self.service_account_file, 'r') as f:
                    creds_data = json.load(f)
                    self.service_account_email = creds_data.get('client_email', '')
                    logger.info(f"Service account email: {self.service_account_email}")
        except Exception as e:
            logger.debug(f"Could not load service account email: {e}")
    
    def get_or_create_calendar(self, calendar_name: str) -> str:
        """Get existing calendar ID or create a new calendar"""
        try:
            # List existing calendars
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            
            logger.info(f"Searching for calendar: '{calendar_name}'")
            logger.info(f"Found {len(calendars)} calendar(s) accessible to service account")
            
            # Log all calendar names for debugging
            if calendars:
                logger.info("Available calendars:")
                for cal in calendars:
                    access_role = cal.get('accessRole', 'unknown')
                    cal_name = cal.get('summary', 'N/A')
                    logger.info(f"  - '{cal_name}' (Role: {access_role}, ID: {cal.get('id', 'N/A')[:30]}...)")
            
            # Check if calendar already exists
            # Prefer calendars where service account is NOT the owner (meaning it's a shared calendar from the user)
            matching_calendars = [cal for cal in calendars if cal.get('summary') == calendar_name]
            
            if matching_calendars:
                # Prefer shared calendars (not owned by service account)
                shared_calendars = [cal for cal in matching_calendars if cal.get('accessRole') != 'owner']
                if shared_calendars:
                    calendar_entry = shared_calendars[0]
                    calendar_id = calendar_entry['id']
                    calendar_access = calendar_entry.get('accessRole', 'unknown')
                    logger.info(f"✓ Found shared calendar: '{calendar_name}' (ID: {calendar_id[:50]}...)")
                    logger.info(f"  Calendar access role: {calendar_access}")
                    logger.info(f"  Calendar timezone: {calendar_entry.get('timeZone', 'unknown')}")
                    return calendar_id
                else:
                    # All matching calendars are owned by service account
                    # Delete the service-account-owned calendar and create a new one
                    calendar_entry = matching_calendars[0]
                    old_calendar_id = calendar_entry['id']
                    logger.warning(f"⚠ Found calendar '{calendar_name}' but service account is the OWNER!")
                    logger.warning(f"⚠ Deleting old service-account-owned calendar and creating a new one...")
                    try:
                        # Delete the old calendar
                        self.service.calendars().delete(calendarId=old_calendar_id).execute()
                        logger.info(f"✓ Deleted old calendar: {old_calendar_id[:50]}...")
                    except HttpError as e:
                        logger.warning(f"Could not delete old calendar: {e}")
                        # Continue anyway - we'll create a new calendar with a different approach
                    
                    # Fall through to create a new calendar
                    # Note: We can't create a calendar and have the user own it via API
                    # The user needs to create it and share it
                    email = self.service_account_email or 'your-service-account-email@project.iam.gserviceaccount.com'
                    logger.error(f"❌ Calendar '{calendar_name}' is owned by service account.")
                    logger.error(f"❌")
                    logger.error(f"❌ SOLUTION:")
                    logger.error(f"❌ 1. Create a NEW calendar in Google Calendar (name it: '{calendar_name}')")
                    logger.error(f"❌ 2. Share it with this email: {email}")
                    logger.error(f"❌ 3. Give 'Make changes to events' permission")
                    logger.error(f"❌ 4. Update CALENDAR_NAME secret in GitHub to match exactly")
                    logger.error(f"❌ 5. Run this workflow again")
                    logger.error(f"❌")
                    logger.error(f"❌ The old calendar will be deleted automatically next run.")
                    raise ValueError(f"Calendar '{calendar_name}' is owned by service account. Please create and share a calendar manually.")
            
            # Calendar not found - create new one
            logger.warning(f"Calendar '{calendar_name}' not found in service account's accessible calendars.")
            logger.warning("This usually means the calendar hasn't been shared with the service account.")
            logger.info(f"Creating new calendar '{calendar_name}' (owned by service account - you may not see it)")
            calendar = {
                'summary': calendar_name,
                'description': 'Barcelona FC football matches automatically synced',
                'timeZone': 'Europe/Madrid'
            }
            created_calendar = self.service.calendars().insert(body=calendar).execute()
            calendar_id = created_calendar['id']
            logger.warning(f"⚠ Created new calendar '{calendar_name}' with ID: {calendar_id}")
            logger.warning("⚠ NOTE: If you don't see events, make sure to share your calendar with the service account email!")
            return calendar_id
            
        except HttpError as error:
            logger.error(f"Error managing calendar: {error}")
            raise
    
    def event_exists(self, calendar_id: str, event_title: str, event_start: datetime) -> bool:
        """Check if an event already exists in the calendar"""
        try:
            time_min = event_start.isoformat()
            time_max = (event_start.replace(hour=23, minute=59, second=59)).isoformat()
            
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            for event in events:
                if event.get('summary') == event_title:
                    return True
            return False
        except HttpError as error:
            logger.error(f"Error checking existing events: {error}")
            return False
    
    def add_event(self, calendar_id: str, title: str, start_time: datetime, 
                  description: str = '', location: str = '') -> Optional[str]:
        """Add an event to the calendar"""
        try:
            # Check if event already exists
            if self.event_exists(calendar_id, title, start_time):
                logger.info(f"Event already exists: {title}")
                return None
            
            # Create event
            event = {
                'summary': title,
                'description': description,
                'location': location,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'Europe/Madrid',
                },
                'end': {
                    'dateTime': (start_time.replace(hour=start_time.hour + 2)).isoformat(),
                    'timeZone': 'Europe/Madrid',
                },
            }
            
            event = self.service.events().insert(calendarId=calendar_id, body=event).execute()
            event_link = event.get('htmlLink', 'N/A')
            logger.info(f"✓ Added event: {title} on {start_time.strftime('%Y-%m-%d %H:%M')} UTC")
            logger.debug(f"  Event link: {event_link}")
            return event.get('id')
            
        except HttpError as error:
            logger.error(f"Error adding event: {error}")
            return None


def parse_fixture_datetime(fixture: Dict) -> Optional[datetime]:
    """Parse fixture datetime from API response"""
    try:
        # Handle different API formats
        if 'utcDate' in fixture:
            dt_str = fixture['utcDate']
            # Parse ISO format: 2024-01-15T20:00:00Z
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt
        elif 'date' in fixture and 'utcDate' not in fixture:
            # Fallback format
            date_str = fixture['date']
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt
    except (KeyError, ValueError) as e:
        logger.warning(f"Could not parse datetime from fixture: {e}")
    return None


def format_fixture_title(fixture: Dict) -> str:
    """Format fixture title for calendar event"""
    try:
        home_team = fixture.get('homeTeam', {}).get('name', 'TBD')
        away_team = fixture.get('awayTeam', {}).get('name', 'TBD')
        competition = fixture.get('competition', {}).get('name', '')
        
        # Determine if Barcelona is home or away
        if 'Barcelona' in home_team or 'Barcelona' in away_team:
            if 'Barcelona' in home_team:
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
        competition = fixture.get('competition', {}).get('name', '')
        matchday = fixture.get('matchday')
        
        desc = f"Barcelona FC Match"
        if competition:
            desc += f"\nCompetition: {competition}"
        if matchday:
            desc += f"\nMatchday: {matchday}"
        
        return desc
    except Exception:
        return "Barcelona FC Match"


def sync_barcelona_fixtures():
    """Main function to sync Barcelona fixtures to Google Calendar"""
    logger.info("Starting Barcelona calendar sync...")
    
    # Initialize services
    football_client = FootballAPIClient(api_key=FOOTBALL_API_KEY)
    
    # Get service account file from environment if available (for GitHub Actions)
    service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
    calendar_service = GoogleCalendarService(service_account_file=service_account_file)
    
    # Get or create calendar
    calendar_id = calendar_service.get_or_create_calendar(CALENDAR_NAME)
    
    # Fetch fixtures
    fixtures = football_client.get_barcelona_fixtures(limit=50)
    
    if not fixtures:
        logger.warning("No fixtures found. Check API key and connection.")
        return
    
    logger.info(f"Processing {len(fixtures)} fixture(s)...")
    
    # Process and add fixtures to calendar
    added_count = 0
    past_count = 0
    invalid_date_count = 0
    
    current_time = datetime.now(timezone.utc)
    logger.info(f"Current time (UTC): {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    for fixture in fixtures:
        # Only process future matches
        match_date = parse_fixture_datetime(fixture)
        if not match_date:
            invalid_date_count += 1
            logger.debug(f"Skipping fixture with invalid date: {fixture.get('homeTeam', {}).get('name', '?')} vs {fixture.get('awayTeam', {}).get('name', '?')}")
            continue
        
        # Only add future matches
        if match_date < current_time:
            past_count += 1
            logger.debug(f"Skipping past match: {format_fixture_title(fixture)} on {match_date.strftime('%Y-%m-%d %H:%M')}")
            continue
        
        title = format_fixture_title(fixture)
        description = format_fixture_description(fixture)
        
        # Get venue if available
        venue = fixture.get('venue', '')
        location = venue if venue else ''
        
        event_id = calendar_service.add_event(
            calendar_id=calendar_id,
            title=title,
            start_time=match_date,
            description=description,
            location=location
        )
        
        if event_id:
            added_count += 1
        else:
            # Event already exists or failed to add
            pass
    
    logger.info("=" * 60)
    logger.info(f"Sync Summary:")
    logger.info(f"  - Total fixtures fetched: {len(fixtures)}")
    logger.info(f"  - Events added: {added_count}")
    logger.info(f"  - Past matches skipped: {past_count}")
    logger.info(f"  - Invalid date skipped: {invalid_date_count}")
    skipped_total = len(fixtures) - added_count
    existing_skipped = skipped_total - past_count - invalid_date_count
    if existing_skipped > 0:
        logger.info(f"  - Already existing skipped: {existing_skipped}")
    logger.info("=" * 60)
    
    if added_count == 0 and past_count > 0:
        logger.warning("⚠ No events added because all matches are in the past!")
        logger.info("This is normal if it's late in the season. New fixtures will appear when they're scheduled.")
    elif added_count == 0:
        logger.warning("⚠ No events were added. Check the logs above for details.")


if __name__ == '__main__':
    sync_barcelona_fixtures()

