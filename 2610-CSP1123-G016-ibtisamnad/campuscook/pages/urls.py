from django.urls import path
from . import views

urlpatterns = [
    # ── Main pages ───────────────────────────────────────────────────────────
    path("",         views.home,          name="home"),
    path("about/",   views.about,         name="about"),

    # ── Grocery ──────────────────────────────────────────────────────────────
    path("grocery/",           views.grocery,     name="grocery"),
    path("remove/<int:id>/",   views.remove_item, name="remove_item"),

    # ── Check recipe (can I cook this?) ──────────────────────────────────────
    path("check/",                    views.check,        name="check"),
    path("check/<int:recipe_id>/",    views.check_recipe, name="check_recipe"),

    # ── Recipe pages ─────────────────────────────────────────────────────────
    path("recipes/",                  views.recipe_list,   name="recipe_list"),
    path("recipes-detail/<int:id>/",  views.recipe_detail, name="recipe_detail"),
    path("filter/",                   views.recipe_filter, name="recipe_filter"),

    # ── Saved recipes (HTML page) ─────────────────────────────────────────────
    path("saved/",   views.saved_recipes, name="saved_recipes"),

    # ── Saved recipes API ─────────────────────────────────────────────────────
    # GET  /api/saved-recipes/              → returns all saved recipes as JSON
    # POST /api/saved-recipes/              → saves a recipe (from save button)
    path("api/saved-recipes/",                          views.save_recipe,       name="save_recipe"),
    path("api/saved-recipes/list/",                     views.saved_recipe_list, name="saved_recipe_list"),
    path("api/saved-recipes/<int:saved_recipe_id>/",    views.unsave_recipe,     name="unsave_recipe"),
]