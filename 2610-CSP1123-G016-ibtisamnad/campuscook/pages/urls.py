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

    # ── Recipe pages ──────────────────────────────────────────────────────────
    path("recipes/",                 views.recipe_list,   name="recipe_list"),
    path("recipes-detail/<int:id>/", views.recipe_detail, name="recipe_detail"),
    path("filter/",                  views.recipe_filter, name="recipe_filter"),

    # ── Add recipe — requires login ───────────────────────────────────────────
    path("recipes/add/", views.add_recipe, name="add_recipe"),

    # ── To Make — checks ingredients, adds missing to Grocery table ───────────
    path("api/to-make/<int:recipe_id>/", views.to_make, name="to_make"),

    # ── Saved recipes (HTML page) ─────────────────────────────────────────────
    path("saved/", views.saved_recipes, name="saved_recipes"),

    # ── Saved recipes API ─────────────────────────────────────────────────────
    # POST   /api/saved-recipes/          → save_recipe view (saves a recipe)
    # GET    /api/saved-recipes/list/     → saved_recipe_list view (returns JSON)
    # DELETE /api/saved-recipes/<id>/     → unsave_recipe view (removes saved)
    path("api/saved-recipes/",                       views.save_recipe,       name="save_recipe"),
    path("api/saved-recipes/list/",                  views.saved_recipe_list, name="saved_recipe_list"),
    path("api/saved-recipes/<int:saved_recipe_id>/", views.unsave_recipe,     name="unsave_recipe"),

    # ── Auth ──────────────────────────────────────────────────────────────────
    # Signup — custom view so we can use our AppUser model
    path("signup/", views.signup_view, name="signup"),

    # Login — Django's built-in LoginView, uses pages/login.html
    # After login, redirects to 'home' (set LOGIN_REDIRECT_URL in settings.py)
    path("accounts/login/",
         auth_views.LoginView.as_view(template_name="pages/login.html"),
         name="login"),

    # Logout — custom view (POST only for security)
    path("accounts/logout/", views.logout_view, name="logout"),

    # Profile — requires login (@login_required in views.py)
    path("profile/", views.profile, name="profile"),
]