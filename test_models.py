import unittest
from models import User, Round, Course


class TestUserModel(unittest.TestCase):
    def setUp(self):
        # Create test user
        self.user = User(username='test_user', email='test@example.com')

    def test_user_creation(self):
        self.assertIsInstance(self.user, User)
        self.assertEqual(self.user.username, 'test_user')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('test_password'))

    # Add more test cases for other user-related functionalities like password hashing, authentication, etc.


class TestRoundModel(unittest.TestCase):
    def setUp(self):
        # Create test round
        self.round = Round(date_played='2024-04-20', golfer_id=1, course_id=1)

    def test_round_creation(self):
        self.assertIsInstance(self.round, Round)
        self.assertEqual(self.round.date_played, '2024-04-20')
        self.assertEqual(self.round.golfer_id, 1)
        self.assertEqual(self.round.course_id, 1)

    # Add more test cases for other round-related functionalities like calculating scores, updating statistics, etc.


class TestCourseModel(unittest.TestCase):
    def setUp(self):
        # Create test course
        self.course = Course(name='Test Course', location='Test Location')

    def test_course_creation(self):
        self.assertIsInstance(self.course, Course)
        self.assertEqual(self.course.name, 'Test Course')
        self.assertEqual(self.course.location, 'Test Location')

    # Add more test cases for other course-related functionalities like adding tees, calculating handicaps, etc.


if __name__ == '__main__':
    unittest.main()
