from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AppUser, FavouriteRecipe, Recipe, Grocery, Comment, RecipeFilter

# ── AppUser ───────────────────────────────────────────────────────────────────
@admin.register(AppUser)
class AppUserAdmin(UserAdmin):
    # Adds the 'age' field to the admin user edit form
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Info', {'fields': ('age',)}),
    )
 
 
# ── Recipe ────────────────────────────────────────────────────────────────────
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display  = ('name', 'cooking_time', 'appliance', 'user')
    search_fields = ('name', 'appliance')
    list_filter   = ('appliance',)
 
    # ── Allow any logged-in staff user to add/edit recipes ───────────────────
    # To let a normal user access admin to add recipes:
    # 1. Go to /admin → Users → select the user
    # 2. Check "Staff status" → Save
    # They can then log in to /admin and add recipes
    # (they won't see other admin sections unless you grant permissions)
 
    def save_model(self, request, obj, form, change):
        # automatically set the recipe's user to whoever is adding it in admin
        if not obj.pk:
            obj.user = request.user
        super().save_model(request, obj, form, change)
 
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # superusers see all recipes
        # staff users only see their own recipes in admin
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
 
 
# ── Grocery ───────────────────────────────────────────────────────────────────
@admin.register(Grocery)
class GroceryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'custom_name', 'user')
    search_fields = ('name', 'custom_name')
 
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
 
 
# ── FavouriteRecipe ───────────────────────────────────────────────────────────────
@admin.register(FavouriteRecipe)
class FavouriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
 
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
 
 
# ── Comment ───────────────────────────────────────────────────────────────────
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'commentary')
 
 
# ── RecipeFilter ──────────────────────────────────────────────────────────────
@admin.register(RecipeFilter)
class RecipeFilterAdmin(admin.ModelAdmin):
    list_display = ('name',)