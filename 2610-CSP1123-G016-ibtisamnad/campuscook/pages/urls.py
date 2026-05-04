from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ── Main pages ────────────────────────────────────────────────────────────
    path("",       views.home,  name="home"),
    path("about/", views.about, name="about"),

    # ── Grocery ───────────────────────────────────────────────────────────────
    path("grocery/",          views.grocery,     name="grocery"),
    path("remove/<int:id>/",  views.remove_item, name="remove_item"),

    # ── Check recipe ──────────────────────────────────────────────────────────
    path("check/<int:recipe_id>/", views.check_recipe, name="check_recipe"),

    # ── Recipe pages ──────────────────────────────────────────────────────────
    path("recipes/",                 views.recipe_list,   name="recipe_list"),
    path("recipes-detail/<int:id>/", views.recipe_detail, name="recipe_detail"),
    path("filter/",                  views.recipe_filter, name="recipe_filter"),

    # ── Add recipe — requires login ───────────────────────────────────────────
    path("recipes/add/", views.add_recipe, name="add_recipe"),

    # ── To Make — checks ingredients, adds missing to Grocery table ───────────
    path("api/to-make/<int:recipe_id>/", views.to_make, name="to_make"),

    # ── Favourite recipes (HTML page) ─────────────────────────────────────────
    path("saved/", views.favourite_recipes, name="saved_recipes"),

    # ── Favourite API ─────────────────────────────────────────────────────────
    path("api/toggle-favourite/<int:recipe_id>/", views.toggle_favourite, name="toggle_favourite"),
    path("api/favourites/",                       views.favourite_recipe_list, name="favourite_recipe_list"),

    # ── Ingredient check/add APIs ─────────────────────────────────────────────
    path("api/check-ingredients/<int:recipe_id>/",      views.check_ingredients,        name="check_ingredients"),
    path("api/add-ingredients/<int:recipe_id>/",        views.add_ingredients_to_grocery, name="add_ingredients_to_grocery"),

    # ── Auth ──────────────────────────────────────────────────────────────────
    path("signup/", views.signup_view, name="signup"),

    path("accounts/login/",
         auth_views.LoginView.as_view(template_name="pages/login.html"),
         name="login"),

    path("accounts/logout/", views.logout_view, name="logout"),

    path("profile/", views.profile, name="profile"),
]