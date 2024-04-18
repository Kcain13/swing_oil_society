import unittest
from app import app


class TestApp(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome to the Golf App", response.data)

    def test_login_page(self):
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Login", response.data)

    def test_search_courses_page(self):
        response = self.app.get('/search_courses')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Search Courses", response.data)

    def test_profile_page(self):
        response = self.app.get('/profile')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Your Profile", response.data)

    def test_view_course_page(self):
        response = self.app.get('/view_course/1')
        self.assertEqual(response.status_code, 200)
        # Adjust the expected response based on your application

    def test_invalid_page(self):
        response = self.app.get('/invalid_url')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Page Not Found", response.data)

    def test_login_with_credentials(self):
        response = self.app.post('/login', data=dict(
            username='test_user',
            password='test_password'
        ), follow_redirects=True)
        self.assertIn(b"Welcome, test_user", response.data)

    def test_logout(self):
        response = self.app.get('/logout', follow_redirects=True)
        self.assertIn(b"Logged out successfully", response.data)

    # Add more test cases for other routes and scenarios as needed


if __name__ == '__main__':
    unittest.main()
