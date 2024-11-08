from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe
from recipe.serializers import RecipeSerializer

RECIPIE_URL = reverse('recipe:recipe-list')


def sample_recipe(user, **param):
    payload = {
        'title': 'Sample Recipe',
        'time_minutes': 10,
        'price': 5.00,
    }
    payload.update(param)
    return Recipe.objects.create(user=user, **payload)


class PublicrecipesApiTests(TestCase):
    """Public recipes API for unauthenticated users"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving recipes"""
        res = self.client.get(RECIPIE_URL)

        self.assertEquals(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivaterecipesApiTests(TestCase):
    """Private recipes API for authenticated users"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='sam@sam.com',
            password='123456',
            name='Sam'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPIE_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEquals(res.data, serializer.data)

    def rest_retrieve_recipes_limited_to_user(self):
        """Test retrieving recipes for authenticated user"""
        user2 = get_user_model().objects.create_user(
            email='other@other.com',
            password='123465',
            name='Other'
        )
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPIE_URL)
        recipes = Recipe.objects.filter(user=self.user).order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEquals(len(res.data), 1)
        self.assertEquals(res.data, serializer.data)
