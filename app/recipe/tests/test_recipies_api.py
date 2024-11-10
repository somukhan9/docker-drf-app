import os.path
import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from core.test.test_models import sample_user
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_recipe(user, **param):
    payload = {
        'title': 'Sample Recipe',
        'time_minutes': 10,
        'price': 5.00,
    }
    payload.update(param)
    return Recipe.objects.create(user=user, **payload)


def sample_tag(user, name='Comfort Fruit'):
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Vinegar'):
    return Ingredient.objects.create(user=user, name=name)


class PublicRecipesApiTests(TestCase):
    """Public recipes API for unauthenticated users"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving recipes"""
        res = self.client.get(RECIPE_URL)

        self.assertEquals(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipesApiTests(TestCase):
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

        res = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.all()
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

        res = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEquals(len(res.data), 1)
        self.assertEquals(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test retrieving recipe details"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEquals(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {'title': 'Cheese Burger', 'time_minutes': 10, 'price': 5.00}
        # recipe = sample_recipe(user=self.user, **payload)
        # recipe.tags.add(sample_tag(user=self.user, name='Fast Food'))

        res = self.client.post(RECIPE_URL, payload)

        # print(res.data)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEquals(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating recipe with tags"""
        tag1 = sample_tag(user=self.user, name='Bread')
        tag2 = sample_tag(user=self.user, name='Cheese')
        payload = {
            'title': 'Cheese Burger',
            'time_minutes': 10,
            'price': 5.00,
            'tags': [tag1.id, tag2.id],
        }
        res = self.client.post(RECIPE_URL, payload)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(tags), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating recipe with ingredients"""
        ingredient1 = sample_ingredient(user=self.user, name='Bread')
        ingredient2 = sample_ingredient(user=self.user, name='Cheese')
        payload = {
            'title': 'Cheese Burger',
            'time_minutes': 10,
            'ingredients': [ingredient1.id, ingredient2.id],
            'price': 5.00
        }
        res = self.client.post(RECIPE_URL, payload)
        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(ingredients), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_create_recipe_with_tags_and_ingredients(self):
        """Test creating recipe with tags and ingredients"""
        tag1 = sample_tag(user=self.user, name='Bread')
        tag2 = sample_tag(user=self.user, name='Cheese')

        ingredient1 = sample_ingredient(user=self.user, name='Bread')
        ingredient2 = sample_ingredient(user=self.user, name='Cheese')

        payload = {
            'title': 'Cheese Burger',
            'time_minutes': 10,
            'ingredients': [ingredient1.id, ingredient2.id],
            'tags': [tag1.id, tag2.id],
            'price': 5.00
        }

        res = self.client.post(RECIPE_URL, payload)
        recipe = Recipe.objects.get(id=res.data['id'])

        tags = recipe.tags.all()
        ingredients = recipe.ingredients.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(tags), 2)
        self.assertEqual(len(ingredients), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_recipe_update_partial(self):
        """Test updating recipe"""
        tag = sample_tag(user=self.user, name='Bread')
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(tag)

        new_tag = sample_tag(user=self.user, name='Cheese')
        payload = {
            'title': 'Cheese Burger',
            'tags': [new_tag.id]
        }

        res = self.client.patch(detail_url(recipe.id), payload)
        recipe.refresh_from_db()

        tags = recipe.tags.all()
        ingredients = recipe.ingredients.all()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(tags), 1)
        self.assertEqual(len(ingredients), 0)
        self.assertEqual(recipe.title, payload['title'])
        self.assertIn(new_tag, tags)

    def test_recipe_update_full(self):
        """Test updating recipe"""
        tag = sample_tag(user=self.user, name='Bread')
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(tag)

        new_tag = sample_tag(user=self.user, name='Cheese')
        payload = {
            'title': 'Cheese Burger',
            'time_minutes': 10,
            'tags': [new_tag.id],
            'price': 30
        }
        res = self.client.put(detail_url(recipe.id), payload)

        recipe.refresh_from_db()

        tags = recipe.tags.all()
        ingredients = recipe.ingredients.all()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(len(tags), len(payload['tags']))
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        self.assertIn(new_tag, tags)


class RecipeImageUploadTests(TestCase):
    """Test Recipe Upload Image"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(email='sam@sam.com', password='123456', name='Sam')
        self.client.force_authenticate(user=self.user)
        self.recipe = sample_recipe(user=self.user)
        # print(self.recipe)

    def tearDown(self):
        self.recipe.image.delete()

    def test_image_upload_to_recipe(self):
        """Test image upload to recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')

        self.recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_image_upload_bad_request(self):
        """Test image upload to recipe"""
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'notimage'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class RecipeFilteringApiTests(TestCase):
    """Test Recipe Filtering by tags and ingredients"""

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(user=self.user)

    def test_filter_recipe_by_tags(self):
        """Test filtering by tags"""
        recipe1 = sample_recipe(user=self.user, title='Cheese Burger')
        recipe2 = sample_recipe(user=self.user, title='Beef Steak')
        tag1 = sample_tag(user=self.user, name='Vegan')
        tag2 = sample_tag(user=self.user, name='Persian')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        recipe3 = sample_recipe(user=self.user, title='Salad')

        res = self.client.get(RECIPE_URL, {'tags': f'{tag1.id}, {tag2.id}'})

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_recipe_by_ingredients(self):
        """Test filtering by ingredients"""
        recipe1 = sample_recipe(user=self.user, title='Cheese Burger')
        recipe2 = sample_recipe(user=self.user, title='Beef Steak')
        ingredient1 = sample_ingredient(user=self.user, name='Loaf')
        ingredient2 = sample_ingredient(user=self.user, name='Beef')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        recipe3 = sample_recipe(user=self.user, title='Salad')

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        res = self.client.get(RECIPE_URL, {'ingredients': f'{ingredient1.id}, {ingredient2.id}'})

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)
