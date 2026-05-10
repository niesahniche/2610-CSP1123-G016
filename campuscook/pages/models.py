from django.db import models

# Create your models here.
class AppUser(models.Model):
    username = models.CharField(max_length=100, unique=True)
    age = models.IntegerField(null=True, blank=True)
    password = models.CharField(max_length=100)
    def __str__(self):
        return self.username
    
class RecipeFilter(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name
    
class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name
    
class Recipe(models.Model):
    name = models.CharField(max_length=100)
    ingredients = models.ManyToManyField(Ingredient)
    cooking_time = models.IntegerField()
    appliance = models.CharField(max_length=100)
    instructions = models.TextField()
    filters = models.ManyToManyField(RecipeFilter, blank=True, null=True)
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    def __str__(self):
        return self.name
    
class CustomIngredient(models.Model):
    name = models.CharField(max_length=100)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    def __str__(self):
        return self.name
    
class Grocery(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, null=True, blank=True)
    custom_name = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    def __str__(self):
        return self.ingredient.name if self.ingredient else self.custom_name

class SavedRecipe(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.user.username} saved {self.recipe.name}"

class Comment(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    commentary = models.TextField()
    def __str__(self):
        return f"Comment by {self.user.username} on {self.recipe.name}"