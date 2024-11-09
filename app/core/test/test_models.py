from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from core import models

User = get_user_model()


def sample_user(email='sam@sam.com', password='123456', name='Sam'):
    return User.objects.create(email=email, password=password, name=name)


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
            User.objects.create_user(email=None, password="password")

    def test_create_super_user(self):
        user = User.objects.create_superuser(email="test@test.com", password="password")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tags_str(self):
        """Test the tag string representation"""
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Vegan'
        )

        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        """Test the ingredient string representations"""
        ingredient = models.Ingredient.objects.create(
            user=sample_user(),
            name='Cucumber'
        )

        self.assertEquals(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        """Test the recipe string representations"""
        recipe = models.Recipe.objects.create(
            user=sample_user(),
            title='Steak and mushroom sauce',
            time_minutes=5,
            price=5.00
        )

        self.assertEquals(str(recipe), recipe.title)

    @patch('uuid.uuid4')
    def test_recipe_file_name(self, mock_uuid):
        """Test that image is saved in the correct location"""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'myimage.jpg')

        exp_path = f'uploads/recipe/{uuid}.jpg'
        self.assertEqual(file_path, exp_path)
