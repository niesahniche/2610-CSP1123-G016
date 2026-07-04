from django.urls import path
from . import views

urlpatterns = [
    # ── Main pages ────────────────────────────────────────────────────────────
    path("",       views.home,  name="home"),
    path("about/", views.about, name="about"),

    # ── Grocery ───────────────────────────────────────────────────────────────
    path("grocery/",          views.grocery,     name="grocery"),
    path("grocery/purchased/<int:id>/", views.purchase_item, name="purchase_item"),
    path("grocery/transfer-purchased/", views.transfer_purchased_to_available, name="transfer_purchased_to_available"),
    path("grocery/complete-recipe/", views.complete_recipe, name="complete_recipe"),
    path("remove/<int:id>/",  views.remove_item, name="remove_item"),
    
    # Ingredient search API — for autocomplete in grocery and add_recipe
    path("api/ingredients/", views.ingredient_search, name="ingredient_search"),
    path("api/to-make/<int:recipe_id>/", views.to_make, name="to_make"),

    # ── Recipe pages ──────────────────────────────────────────────────────────
    path("recipes/",                 views.recipe_list,   name="recipe_list"),
    path("recipes-detail/<int:id>/", views.recipe_detail, name="recipe_detail"),
    path("filter/",                  views.recipe_filter, name="recipe_filter"),

    # ── Add and delete recipe — requires login ───────────────────────────────────────────
    path("recipes/add/", views.add_recipe, name="add_recipe"),
    path("api/delete-recipe/<int:recipe_id>/", views.delete_recipe, name="delete_recipe"),

    # ── To Make — checks ingredients, adds missing to Grocery table ───────────
    path("api/to-make/<int:recipe_id>/", views.to_make, name="to_make"),

    # ── Favourite recipes (HTML page) ─────────────────────────────────────────
    path("saved/", views.favourite_recipes, name="saved_recipes"),

    # ── Favourite API ─────────────────────────────────────────────────────────
    path("api/toggle-favourite/<int:recipe_id>/", views.toggle_favourite, name="toggle_favourite"),
    path("api/favourites/",                       views.favourite_recipe_list, name="favourite_recipe_list"),
    path("api/toggle-want-to-try/<int:recipe_id>/", views.toggle_want_to_try, name="toggle_want_to_try"),
    path("want-to-try/", views.want_to_try_page, name="want_to_try"),

    # ── Ingredient check/add APIs ─────────────────────────────────────────────
    path("api/check-ingredients/<int:recipe_id>/",      views.check_ingredients,        name="check_ingredients"),
    path("api/add-ingredients/<int:recipe_id>/",        views.add_ingredients_to_grocery, name="add_ingredients_to_grocery"),

    # ── Comments API ──────────────────────────────────────────────────────────
    path("api/comments/<int:recipe_id>/",      views.get_comments,  name="get_comments"),
    path("api/add-comment/<int:recipe_id>/",   views.add_comment,   name="add_comment"),

    # ── Profile ───────────────────────────────────────────────────────────
    path('profile/update/', views.profile_update, name='profile_update'),

    # ── Ratings API ───────────────────────────────────────────────────────────
    path("api/rate/<int:recipe_id>/",          views.rate_recipe,         name="rate_recipe"),
    path("api/ratings/<int:recipe_id>/",       views.get_recipe_ratings,  name="get_recipe_ratings"),

    # Recommended recipes (used at bottom of detail page)
    path("api/recommended/<int:recipe_id>/", views.recommended_recipes, name="recommended_recipes"),

    # ── Auth ──────────────────────────────────────────────────────────────────
    path("signup/", views.signup_view, name="signup"),

    path("accounts/login/", views.login_view, name="login"),
    path("accounts/verify-2fa/", views.verify_2fa, name="verify_2fa"),
    path("accounts/resend-2fa/", views.resend_2fa, name="resend_2fa"),

    path("accounts/logout/", views.logout_view, name="logout"),

    path("profile/", views.profile, name="profile"),

    # ── Feedback ──────────────────────────────────────────────────────────────
    path("feedback/", views.feedback_view, name="feedback"),
]