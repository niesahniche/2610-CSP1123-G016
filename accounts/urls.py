from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ── Main pages ──────────────────────────────────────────
    path("",        views.home,    name="home"),
    path("about/",  views.about,   name="about"),
    path("signup/", views.signup,  name="signup"),
    path("login/",  views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile, name="profile"),

    # ── Grocery ─────────────────────────────────────────────
    path("grocery/",         views.grocery,     name="grocery"),
    path("remove/<int:id>/", views.remove_item, name="remove_item"),

    # ── Check recipe ────────────────────────────────────────
    path("check/",                 views.check,        name="check"),
    path("check/<int:recipe_id>/", views.check_recipe, name="check_recipe"),

    # ── Recipe pages ────────────────────────────────────────
    path("recipes/",                  views.recipe_list,   name="recipe_list"),
    path("recipes-detail/<int:id>/",  views.recipe_detail, name="recipe_detail"),
    path("filter/",                   views.recipe_filter, name="recipe_filter"),

    # ── Saved recipes ────────────────────────────────────────
    path("saved/",                           views.saved_recipes,    name="saved_recipes"),
    path("api/saved-recipes/",               views.save_recipe,      name="save_recipe"),
    path("api/saved-recipes/list/",          views.saved_recipe_list, name="saved_recipe_list"),
    path("api/saved-recipes/<int:saved_recipe_id>/", views.unsave_recipe, name="unsave_recipe"),
]