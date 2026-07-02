from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager

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


class Ingredient(models.Model):
    """Global ingredient list shared by all users and recipes"""
    name = models.CharField(max_length=100, unique=True)
 
    def __str__(self):
        return self.name
 
 
class Grocery(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),   # user has this ingredient
        ('missing',   'Missing'),     # added automatically when using "To Make"
        ('purchased', 'Purchased'),   # marked as purchased after clicking Got it
    ]
 
    name        = models.CharField(max_length=100, default='')
    custom_name = models.CharField(max_length=100, null=True, blank=True)
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
 
    # quantity → optional quantity of the ingredient (e.g. "2 cups", "3 tsp")
    quantity    = models.CharField(max_length=100, null=True, blank=True)
 
    user        = models.ForeignKey(
        'pages.AppUser',
        on_delete=models.CASCADE,
        related_name='groceries'
    )
 
    def __str__(self):
        quantity_label = f"{self.quantity}x " if self.quantity and self.quantity != 1 else ""
        return f"{quantity_label}{self.name} ({self.status})"
 
 
class Recipe(models.Model):
    BUDGET_CHOICES = [
        ('low',    'Below RM5'),
        ('medium', 'RM5 – RM15'),
        ('high',   'Above RM15'),
    ]

    MEAL_TYPE_CHOICES = [
    ('breakfast', 'Breakfast'),
    ('lunch',     'Lunch'),
    ('dinner',    'Dinner'),
    ('snack',     'Snack'),
    ('dessert',   'Dessert'),
    ('drinks',    'Drinks'),
    ('other',     'Other'),
    ]
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES, default='other')

    name         = models.CharField(max_length=100)
    # ingredients → ManyToMany to Ingredient table (separate from Grocery)
    ingredients  = models.ManyToManyField(
        Ingredient,
        blank=True,
        related_name='recipes'
    )
    cooking_time = models.IntegerField()
    appliance    = models.CharField(max_length=100)
    instructions = models.TextField()
    image        = models.ImageField(upload_to='recipe_images/', null=True, blank=True)
    # is_halal → whether this recipe is halal (default True)
    is_halal     = models.BooleanField(default=True)
    # budget → estimated cost bracket
    budget       = models.CharField(
        max_length=10, choices=BUDGET_CHOICES, default='low'
    )
    filters      = models.ManyToManyField(RecipeFilter, blank=True)
    # user → AppUser who created this recipe
    user         = models.ForeignKey(
        'pages.AppUser',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
 
    def __str__(self):
        return self.name
    
    @property
    def avg_rating(self):
        ratings = self.ratings.all()
        if not ratings.exists():
            return None
        return round(sum(r.stars for r in ratings) / ratings.count(), 1)
 
 
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
    created_at = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return f"Comment by {self.user.username} on {self.recipe.name}"
    
    class Meta:
        ordering = ['-created_at']

class Feedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    user       = models.ForeignKey(
        'pages.AppUser',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='feedback_entries'
    )
    name       = models.CharField(max_length=100)
    email      = models.EmailField(blank=True)
    rating     = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    message    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback from {self.name} ({self.created_at:%Y-%m-%d})"

class Rating(models.Model):
    STAR_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    user   = models.ForeignKey(
        'pages.AppUser',
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    stars  = models.IntegerField(choices=STAR_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'recipe')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} rated {self.recipe.name} {self.stars}⭐"
    
    @property
    def avg_rating(self):
        ratings = self.ratings.all()
        if not ratings.exists():
            return None
        return round(sum(r.stars for r in ratings) / ratings.count(), 1)

class WantToTry(models.Model):
    """Recipes the user has marked with 'To Make' — their cooking bucket list."""
    user   = models.ForeignKey(
        'pages.AppUser',
        on_delete=models.CASCADE,
        related_name='want_to_try',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='wanted_by',
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} wants to try {self.recipe.name}"