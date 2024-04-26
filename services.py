
from flask import current_app
import requests
from datetime import datetime, timedelta
from models import Golfer, Course, db
import pytz


global_api_token = None
token_expiry = None


def get_admin_token():
    global global_api_token, token_expiry  # Declare the variables as global
    current_time = datetime.utcnow().replace(tzinfo=pytz.utc)

    # Check if the current token is valid
    if global_api_token and token_expiry and token_expiry > current_time:
        current_app.logger.info("Using cached token")
        return global_api_token

    # Fetch a new token if necessary
    current_app.logger.info("Fetching new token")
    response = requests.post(
        'https://api2.ghin.com/api/v1/golfer_login.json',
        headers={"Content-Type": "application/json"},
        json={
            "token": "dummy token",
            "user": {
                "password": current_app.config['GHIN_ADMIN_PASSWORD'],
                "email_or_ghin": current_app.config['GHIN_ADMIN_USER'],
                "remember_me": True
            }
        }
    )

    if response.status_code == 200:
        global_api_token = response.json().get('golfer_user').get('golfer_user_token')
        if global_api_token:
            token_expiry = current_time + \
                timedelta(hours=24)  # Set new expiry time
            current_app.logger.info(
                "New token fetched successfully", global_api_token)
            return global_api_token
        else:
            current_app.logger.error("Token not found in response")

    else:
        current_app.logger.error(
            'Failed to get admin token: HTTP status code {}'.format(response.status_code))
        current_app.logger.debug('Response details: {}'.format(response.text))

    return None


def fetch_golfer_handicap(ghin_id, last_name, state):
    """Fetch the current handicap for a golfer using the GHIN API."""

    try:
        token = get_admin_token()  # Ensure a valid token is available
        if not token:
            raise ValueError("Authentication token is missing or invalid")

        response = requests.get('https://api2.ghin.com/api/v1/golfers/search.json',
                                headers={
                                    "Authorization": f"Bearer {token}",
                                    "Content-Type": "application/json"},
                                params={
                                    "per_page": "50",
                                    "page": "1",
                                    "ghin_id": ghin_id,
                                    "last_name": last_name,
                                    "state": state
                                }
                                )
        response.raise_for_status()  # Raises an exception for HTTP errors
        golfer_data = response.json()
        # current_app.logger.debug(f"API response: {golfer_data}")

        golfers = golfer_data.get('golfers', [])
        if golfers:
            for golfer in golfers:
                current_app.logger.debug(
                    f"Checking golfer: GHIN ID {golfer.get('ghin')}, Name {golfer.get('last_name')}, State {golfer.get('state')}")
                if str(golfer.get('ghin')) == str(ghin_id):
                    # Ensure matching GHIN IDs
                    current_app.logger.info(f"Match found: {golfer}")
                    return golfer.get('handicap_index')
        return None

    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f'HTTP error occurred: {e}')
        return None
    except Exception as e:
        current_app.logger.error(f'An unexpected error occurred: {e}')
        return None


def search_courses(query):
    """Search for golf courses using the GHIN API."""
    try:
        token = get_admin_token()  # Ensure a valid token is available
        if not token:
            raise ValueError("Authentication token is missing or invalid")

        headers = {
            "Authorization": f"Bearer {token}",
            "content-type": "application/json"
        }
        params = {
            "name": query
        }
        api_url = f"https://api2.ghin.com/api/v1/courses/search.json"

        current_app.logger.debug(
            f"Requesting URL: {api_url} with headers: {headers} and params: {params}")
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()  # Will raise an exception for HTTP errors

        current_app.logger.debug(f'Response Data; {response.text}')
        return response.json().get('courses', [])  # Safely extract courses

    except requests.exceptions.HTTPError as e:
        current_app.logger.error(
            f'HTTP error occurred: {e.response.status_code} - {e.response.text}')
        return None
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f'Request exception occurred: {e}')
        return None
    except ValueError as e:
        current_app.logger.error(f'Error: {e}')
        return None
    except Exception as e:
        current_app.logger.error(f'An unexpected error occurred: {e}')
        return None


def save_course_data(course_data):
    for course_info in course_data:
        # Check if course already exists to avoid duplicates
        existing_course = Course.query.filter_by(
            course_id=course_info['CourseID']).first()
        if not existing_course:
            new_course = Course(
                __tablename__='courses',
                course_id=course_info['CourseID'],
                name=course_info['CourseName'],
                status=course_info['CourseStatus'],
                latitude=course_info['GeoLocationLatitude'],
                longitude=course_info['GeoLocationLongitude'],
                facility_id=course_info['FacilityID'],
                facility_name=course_info['FacilityName'],
                full_name=course_info['FullName'],
                address=course_info['Address1'],
                city=course_info['City'],
                state=course_info['State'],
                zip_code=course_info['Zip'],
                country=course_info['Country'],
                phone=course_info['Telephone'],
                email=course_info['Email'],
                updated_on=datetime.strptime(
                    course_info['UpdatedOn'], "%Y-%m-%d")
            )
            db.session.add(new_course)
            db.session.commit()


def fetch_course_details(course_id):
    """ Fetch course details using the admin token. """

    token = get_admin_token()  # Ensure a valid token is available
    if not token:
        raise ValueError("Authentication token is missing or invalid")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "content-type": "application/json"
        }

        response = requests.get(
            f"https://api2.ghin.com/api/v1/courses/{course_id}.json", headers=headers)
        response.raise_for_status()

        data = response.json()

        course_details = {
            "Facility": data.get('Facility', {}),
            "Season": data.get('Season', {}),
            "TeeSets": data.get('TeeSets', []),
            "CourseStatus": data.get('CourseStatus', 'Status Unknown'),
            "CourseCity": data.get('CourseCity', 'City not available'),
            "CourseState": data.get('CourseState', 'State not available')
        }
        current_app.logger.debug(course_details)
        return course_details
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


# def fetch_playing_handicaps(golfer_id, course_id, tee_id, played_at):
#     """Fetch playing handicaps from the GHIN API."""
#     try:
#         token = get_admin_token()  # Ensure a valid token is available
#         if not token:
#             raise ValueError("Authentication token is missing or invalid")

#         headers = {
#             "Authorization": f"Bearer {token}",
#             "content-type": "application/json"
#         }
#         data = {
#             "golfer_id": golfer_id,
#             "course_id": course_id,
#             "tee_id": tee_id,
#             "played_at": played_at.strftime("%Y-%m-%d")
#         }
#         response = requests.post(
#             'https://api2.ghin.com/api/v1/playing_handicaps.json',
#             headers=headers,
#             json=data
#         )
#         if response.status_code == 200:
#             return response.json()  # Returns the playing handicaps data
#         else:
#             current_app.logger.error(
#                 f"Failed to fetch playing handicaps: {response.text}")
#             return None
#     else:
#         current_app.logger.error(
#             'Failed to authenticate with GHIN API for playing handicaps')
#         return None
