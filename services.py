import requests
from flask import current_app, session
import datetime
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables

GHIN_ADMIN_USER = os.getenv('GHIN_ADMIN_USER')
GHIN_ADMIN_PASSWORD = os.getenv('GHIN_ADMIN_PASSWORD')

if not GHIN_ADMIN_USER or not GHIN_ADMIN_PASSWORD:
    raise Exception("GHIN API credentials are not set")


def get_admin_token():
    """ Retrieve the admin token from the GHIN API or use cached one from the session. """
    if 'ghin_token' in session and 'token_expiry' in session:
        if session['token_expiry'] > datetime.utcnow():
            return session['ghin_token'], session['token_expiry']

    response = requests.post(
        'https://api2.ghin.com/api/v1/golfer_login.json',
        headers={"content-type": "application/json"},
        json={
            "user": {
                "password": GHIN_ADMIN_PASSWORD,
                "email_or_ghin": GHIN_ADMIN_USER,
                "remember_me": False
            }
        }
    )
    if response.status_code == 200:
        token = response.json().get('access_token')
        expiry = datetime.utcnow() + datetime.timedelta(hours=24)
        session['ghin_token'] = token
        session['token_expiry'] = expiry
        print("${token}")
        return token, expiry

    return None, None


def fetch_course_details(course_id):
    """ Fetch course details using the admin token. """
    token, _ = get_admin_token()  # Ensure a valid token is available
    if token:
        headers = {
            "Authorization": f"Bearer {token}",
            "content-type": "application/json"
        }
        response = requests.get(
            f"https://api2.ghin.com/api/v1/courses/{course_id}/details.json", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            current_app.logger.error('Failed to fetch course details')
            return None
    else:
        current_app.logger.error('Failed to authenticate with GHIN API')
        return None


def search_courses(query):
    """Search for golf courses using the GHIN API."""
    token, _ = get_admin_token()  # Ensure a valid token is available
    if token:
        headers = {
            "Authorization": f"Bearer {token}",
            "content-type": "application/json"
        }
        api_url = f"https://api2.ghin.com/api/v1/courses/search.json?query={query}"
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            return response.json().get('courses', [])
        else:
            current_app.logger.error(
                f'Failed to fetch courses: {response.text}')
            return None
    else:
        current_app.logger.error(
            'Failed to authenticate with GHIN API for course search')
        return None


def fetch_golfer_handicap(golfer_id):
    """Fetch the current handicap for a golfer using the GHIN API."""
    token, _ = get_admin_token()
    if token:
        headers = {
            "Authorization": f"Bearer {token}",
            "content-type": "application/json"
        }
        api_url = f"https://api2.ghin.com/api/v1/golfers.json?golfer_id={golfer_id}"
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            golfer_data = response.json()
            return golfer_data.get('HandicapIndex')
        else:
            current_app.logger.error(
                'Failed to fetch golfer handicap data: ' + str(response.content))
            return None
    else:
        current_app.logger.error(
            'Failed to authenticate with GHIN API for golfer details')
        return None


def fetch_playing_handicaps(golfer_id, course_id, tee_id, played_at):
    """Fetch playing handicaps from the GHIN API."""
    token, _ = get_admin_token()  # Reuse the admin token fetching mechanism
    if token:
        headers = {
            "Authorization": f"Bearer {token}",
            "content-type": "application/json"
        }
        data = {
            "golfer_id": golfer_id,
            "course_id": course_id,
            "tee_id": tee_id,
            "played_at": played_at.strftime("%Y-%m-%d")
        }
        response = requests.post(
            'https://api2.ghin.com/api/v1/playing_handicaps.json',
            headers=headers,
            json=data
        )
        if response.status_code == 200:
            return response.json()  # Returns the playing handicaps data
        else:
            current_app.logger.error(
                f"Failed to fetch playing handicaps: {response.text}")
            return None
    else:
        current_app.logger.error(
            'Failed to authenticate with GHIN API for playing handicaps')
        return None
