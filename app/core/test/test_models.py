from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class ModelTests(TestCase):
    def test_user_create_email(self):
        email = "test@test.com"
        password = "password"

        user = User.objects.create_user(email=email, password=password)
        self.assertEquals(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_user_normalize_email(self):
        email = "test@TEST.com"
        password = "password"

        user = User.objects.create_user(email=email, password=password)

        self.assertEquals(user.email, email.lower())

    def test_create_user_invalid_email(self):
        with self.assertRaises(ValueError):
            user = User.objects.create_user(email=None, password="password")

    def test_create_super_user(self):
        user = User.objects.create_superuser(email="test@test.com", password="password")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
