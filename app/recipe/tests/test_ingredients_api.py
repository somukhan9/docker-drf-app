from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    """Test the publicly available Ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving Ingredients"""
        res = self.client.get(INGREDIENT_URL)

        self.assertEquals(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test private Ingredients API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='sam@sam.com',
            password='123456',
            name='Sam'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving Ingredients"""
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Salt')

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')

        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEquals(res.data, serializer.data)

    def test_retrieve_ingredients_limited_to_user(self):
        """Test retrieving Ingredients for authenticated user"""
        user2 = get_user_model().objects.create_user(
            email='other@other.com',
            password='123456',
            name='Other'
        )
        Ingredient.objects.create(user=user2, name='Vinegar')
        ingredient = Ingredient.objects.create(user=self.user, name='Cucumber')

        res = self.client.get(INGREDIENT_URL)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEquals(len(res.data), 1)
        self.assertEquals(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        """Test creating a new Ingredient"""
        payload = {'name': 'Cucumber'}

        res = self.client.post(INGREDIENT_URL, payload)
        exists = Ingredient.objects.filter(name=payload['name']).exists()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Test creating a new Ingredient with invalid payload"""
        payload = {'name': ''}

        res = self.client.post(INGREDIENT_URL, payload)

        self.assertEquals(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipes(self):
        """Test filtering Ingredients by those assigned to recipes"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Powder Rice')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Raw Meet')
        ingredient3 = Ingredient.objects.create(user=self.user, name='Salt')

        recipe1 = Recipe.objects.create(user=self.user, title='Loaf', time_minutes=20, price=15)
        recipe2 = Recipe.objects.create(user=self.user, title='Chicken Masala', time_minutes=40, price=35)

        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        serializer3 = IngredientSerializer(ingredient3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_retrieve_ingredients_assigned_unique(self):
        """Test filtering Ingredients by assigned returns unique items"""
        ingredient = Ingredient.objects.create(user=self.user, name='Powder Rice')

        recipe1 = Recipe.objects.create(user=self.user, title='Loaf', time_minutes=20, price=15)
        recipe2 = Recipe.objects.create(user=self.user, title='Chicken Masala', time_minutes=50, price=150)

        recipe1.ingredients.add(ingredient)
        recipe2.ingredients.add(ingredient)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
