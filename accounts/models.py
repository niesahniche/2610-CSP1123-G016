from django.db import models


class Recipe(models.Model):
    name         = models.CharField(max_length=200)
    cooking_time = models.IntegerField()
    appliance    = models.CharField(max_length=100)
    instructions = models.TextField()

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name   = models.CharField(max_length=200)
    recipe = models.ManyToManyField(Recipe, related_name='ingredients')

    def __str__(self):
        return self.name


class SavedRecipe(models.Model):
    from django.contrib.auth.models import User
    user   = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f"{self.user.username} → {self.recipe.name}"

# Create your models here.
