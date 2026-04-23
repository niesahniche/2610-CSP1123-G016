from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import *

admin.site.register(Ingredient)
admin.site.register(AppUser)
admin.site.register(RecipeFilter)
admin.site.register(Recipe)
admin.site.register(Grocery)
admin.site.register(SavedRecipe)
admin.site.register(Comment)