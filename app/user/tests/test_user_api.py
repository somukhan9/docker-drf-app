from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')

def create_user(**param):
    return get_user_model().objects.create_user(**param)


class PublicUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test create user API (Public)"""
        payload = {
            'email': 'test@test.com',
            'password': '123456',
            'name': 'Test Name'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEquals(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_already_exists(self):
        """Test user already exists"""
        payload = {
            'email': 'test@test.com',
            'password': '123456',
            'name': 'Test Name'
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEquals(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that password must be more than 5 characters"""
        payload = {
            'email': 'test@test.com',
            'password': '1234',
            'name': 'Test Name'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEquals(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(email=payload['email']).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that token is created for user"""
        payload = {
            'email': 'test@test.com',
            'password': '123456',
            'name': 'Test Name'
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEquals(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Test that token is not created when invalid credentials are given"""
        payload = {
            'email': 'test@test.com',
            'password': '123456',
            'name': 'Test Name'
        }
        wrong_payload = {
            'email': 'test1@test.com',
            'password': '12345',
            'name': 'Test Name'
        }

        create_user(**payload)
        res = self.client.post(TOKEN_URL, wrong_payload)

        self.assertNotIn('token', res.data)
        self.assertEquals(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Test that token is not create when user doesn't exists"""
        payload = {
            'email': 'test1@test.com',
            'password': '12345',
            'name': 'Test Name'
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEquals(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """Test that token is not created when field is missing"""
        payload = {'email': 'one', 'password': ''}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEquals(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test that authentication require authentication"""
        res = self.client.get(ME_URL)

        self.assertEquals(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication"""

    def setUp(self):
        payload = {'email':'example@example.com', 'password':'123456', 'name':'Example Name'}
        self.user = create_user(**payload)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_user_profile_success(self):
        """Test retrieving profile for logged in users"""
        res = self.client.get(ME_URL)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEquals(res.data, {'email': self.user.email, 'name': self.user.name})

    def test_post_me_not_allowed(self):
        """Test post not allowed on the me url"""
        res = self.client.post(ME_URL, {})

        self.assertEquals(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating user profile for authenticated user"""
        payload = {'name': 'new name', 'password': 'password'}
        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()

        self.assertEquals(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEquals(res.status_code, status.HTTP_200_OK)
