from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager

#removed ingredient, custom_ingredient, and recipe_ingredient tables — replaced with Grocery and ManyToMany in Recipe

class AppUser(AbstractUser):
    # AbstractUser provides: username, password, email, first_name, last_name
    age = models.IntegerField(null=True, blank=True)
    objects = UserManager()
 
    def __str__(self):
        return self.username
 
 
class RecipeFilter(models.Model):
    name = models.CharField(max_length=100)
 
    def __str__(self):
        return self.name
 
 
class Grocery(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),   # user has this ingredient
        ('missing',   'Missing'),     # added automatically when using "To Make"
    ]
 
    name        = models.CharField(max_length=100, default='')
    custom_name = models.CharField(max_length=100, null=True, blank=True)
 
    # status → 'available' by default when user manually adds
    #          'missing'   when auto-added via "To Make" button
    status      = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available'
    )
 
    # for_recipe → optional note linking a missing ingredient back to a recipe
    # e.g. "missing for: Spicy Fried Rice"
    # null/blank because available groceries don't need this
    for_recipe  = models.CharField(max_length=200, null=True, blank=True)
 
    user        = models.ForeignKey(
        'pages.AppUser',
        on_delete=models.CASCADE,
        related_name='groceries'
    )
 
    def __str__(self):
        return f"{self.name} ({self.status})"
 
 
class Recipe(models.Model):
    name         = models.CharField(max_length=100)
    # ingredients → ManyToMany to Grocery table (grocery_id is the FK)
    ingredients  = models.ManyToManyField(
        Grocery,
        blank=True,
        related_name='recipes'
    )
    cooking_time = models.IntegerField()
    appliance    = models.CharField(max_length=100)
    instructions = models.TextField()
    image_url    = models.URLField(max_length=500, null=True, blank=True)
    filters      = models.ManyToManyField(RecipeFilter, blank=True)
    # user → AppUser who created this recipe
    user         = models.ForeignKey(
        'pages.AppUser',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
 
    def __str__(self):
        return self.name
 
 
class FavouriteRecipe(models.Model):
    user   = models.ForeignKey(
        'pages.AppUser',
        on_delete=models.CASCADE,
        related_name='favourite_recipes'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favourited_by'
    )
 
    class Meta:
        unique_together = ('user', 'recipe')
 
    def __str__(self):
        return f"{self.user.username} favourited {self.recipe.name}"
 
 
class Comment(models.Model):
    user       = models.ForeignKey('pages.AppUser', on_delete=models.CASCADE)
    recipe     = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    commentary = models.TextField()
 
    def __str__(self):
        return f"Comment by {self.user.username} on {self.recipe.name}"