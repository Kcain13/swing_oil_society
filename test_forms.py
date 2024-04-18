import unittest
from app.forms import LoginForm, RegistrationForm


class TestLoginForm(unittest.TestCase):
    def test_valid_login_form(self):
        form = LoginForm(username='test_user', password='test_password')
        self.assertTrue(form.validate())

    def test_invalid_login_form_missing_username(self):
        form = LoginForm(username='', password='test_password')
        self.assertFalse(form.validate())
        self.assertIn('This field is required.', form.username.errors)

    def test_invalid_login_form_missing_password(self):
        form = LoginForm(username='test_user', password='')
        self.assertFalse(form.validate())
        self.assertIn('This field is required.', form.password.errors)

    # Add more test cases for other scenarios like incorrect data format, etc.


class TestRegistrationForm(unittest.TestCase):
    def test_valid_registration_form(self):
        form = RegistrationForm(
            username='new_user', email='test@example.com', password='test_password')
        self.assertTrue(form.validate())

    def test_invalid_registration_form_missing_username(self):
        form = RegistrationForm(
            username='', email='test@example.com', password='test_password')
        self.assertFalse(form.validate())
        self.assertIn('This field is required.', form.username.errors)

    def test_invalid_registration_form_missing_email(self):
        form = RegistrationForm(username='new_user',
                                email='', password='test_password')
        self.assertFalse(form.validate())
        self.assertIn('This field is required.', form.email.errors)

    def test_invalid_registration_form_invalid_email_format(self):
        form = RegistrationForm(
            username='new_user', email='invalid_email', password='test_password')
        self.assertFalse(form.validate())
        self.assertIn('Invalid email address.', form.email.errors)

    # Add more test cases for other scenarios like password validation, unique username/email, etc.


if __name__ == '__main__':
    unittest.main()
