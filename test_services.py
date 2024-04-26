import unittest
from unittest.mock import patch, MagicMock
import requests
from flask import Flask
from services import get_admin_token, fetch_course_details, search_courses


class TestServiceFunctions(unittest.TestCase):
    def setUp(self):
        # Setup a Flask application context for the tests
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        # Remove application context after a test is done
        self.app_context.pop()

    @patch('services.requests.post')
    def test_get_admin_token(self, mock_post):
        # Mock the response from the GHIN API for login
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'access_token': 'fake_token'}
        mock_post.return_value = mock_response

        token, expiry = get_admin_token()
        self.assertEqual(token, 'fake_token')
        self.assertIsNotNone(expiry)

    @patch('services.get_admin_token', return_value=('fake_token', None))
    @patch('services.requests.get')
    def test_fetch_course_details(self, mock_get, mock_get_admin_token):
        # Mock the response from the GHIN API for fetching course details
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 123, 'name': 'Sample Course'}
        mock_get.return_value = mock_response

        course_details = fetch_course_details(123)
        self.assertIsNotNone(course_details)
        self.assertEqual(course_details['name'], 'Sample Course')

    @patch('services.get_admin_token', return_value=('fake_token', None))
    @patch('services.requests.get')
    def test_search_courses(self, mock_get, mock_get_admin_token):
        # Mock the response from the GHIN API for course search
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'courses': [{'id': 1, 'name': 'Golf Club'}]}
        mock_get.return_value = mock_response

        result = search_courses('Golf')
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Golf Club')


if __name__ == '__main__':
    unittest.main()
