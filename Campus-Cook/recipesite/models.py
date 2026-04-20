from django.db import models

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100)
    age = models.IntegerField()
    password = models.CharField(max_length=100)

class RecipeFilters(models.Model):
    recipe_filters_id = models.AutoField(primary_key=True)
    recipe_filters_name = models.CharField(max_length=100)

class RecipeDetails(models.Model):
    recipe_id = models.AutoField(primary_key=True)
    recipe_name = models.CharField(max_length=100)
    recipe_filters = models.ForeignKey(RecipeFilters, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Groceries(models.Model):
    ingredients_id = models.AutoField(primary_key=True)
    ingredients_name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)   # FK here

class SavedRecipe(models.Model):
    saved_recipe_id = models.AutoField(primary_key=True)
    saved_recipe_name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)   # FK here

class Comments(models.Model):
    comment_id = models.AutoField(primary_key=True)
    commentary = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)   # FK here

