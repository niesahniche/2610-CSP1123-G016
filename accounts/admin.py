from django.contrib import admin
from .models import Recipe, Ingredient, SavedRecipe

admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(SavedRecipe)