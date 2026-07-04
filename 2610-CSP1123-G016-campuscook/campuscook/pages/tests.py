from django.test import TestCase
from django.urls import reverse

from .models import AppUser, Grocery, Ingredient, Recipe, WantToTry


class WantToTryCleanupTests(TestCase):
    def setUp(self):
        self.user = AppUser.objects.create_user(
            username='cookuser',
            email='cook@example.com',
            password='testpass123',
        )
        self.other_recipe = Recipe.objects.create(
            user=self.user,
            name='Other Recipe',
            cooking_time=10,
            appliance='Pan',
            instructions='Cook quickly.',
        )
        self.recipe = Recipe.objects.create(
            user=self.user,
            name='Spicy Pasta',
            cooking_time=15,
            appliance='Stove',
            instructions='Cook everything together.',
        )
        self.recipe.ingredients.add(
            Ingredient.objects.create(name='Chicken'),
            Ingredient.objects.create(name='Pasta'),
        )
        WantToTry.objects.create(user=self.user, recipe=self.recipe)
        self.client.force_login(self.user)

    def test_removing_want_to_try_clears_recipe_labels_from_kept_groceries(self):
        available_item = Grocery.objects.create(
            user=self.user,
            name='Chicken',
            status='available',
            for_recipe='Spicy Pasta, Other Recipe',
        )
        purchased_item = Grocery.objects.create(
            user=self.user,
            name='Sauce',
            status='purchased',
            for_recipe='Spicy Pasta',
        )

        response = self.client.delete(reverse('toggle_want_to_try', args=[self.recipe.id]))

        self.assertEqual(response.status_code, 200)
        available_item.refresh_from_db()
        purchased_item.refresh_from_db()
        self.assertEqual(available_item.for_recipe, 'Other Recipe')
        self.assertEqual(purchased_item.for_recipe, '')
        self.assertFalse(WantToTry.objects.filter(user=self.user, recipe=self.recipe).exists())

    def test_removing_want_to_try_deletes_missing_items_for_that_recipe(self):
        Grocery.objects.create(
            user=self.user,
            name='Pasta',
            status='missing',
            for_recipe='Spicy Pasta',
        )

        response = self.client.delete(reverse('toggle_want_to_try', args=[self.recipe.id]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Grocery.objects.filter(
                user=self.user,
                name='Pasta',
                status='missing',
            ).exists()
        )

    def test_removing_want_to_try_keeps_missing_item_needed_by_other_recipe(self):
        missing_item = Grocery.objects.create(
            user=self.user,
            name='Pasta',
            status='missing',
            for_recipe='Spicy Pasta, Other Recipe',
        )

        response = self.client.delete(reverse('toggle_want_to_try', args=[self.recipe.id]))

        self.assertEqual(response.status_code, 200)
        missing_item.refresh_from_db()
        self.assertEqual(missing_item.for_recipe, 'Other Recipe')