from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from .models import AppUser
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

# ── EDIT THIS if you rename any model ──────────────────────────────────────
# models.py has: SavedRecipe (no underscore) — make sure this matches exactly
from .models import Grocery, AppUser, Ingredient, Recipe, SavedRecipe


# ── base (not needed as a view, base.html is just a template parent) ───────
def home(request):
    return render(request, "pages/home.html")


def about(request):
    return render(request, "pages/about.html")


# ── Check recipe — shows all recipes, then shows missing ingredients ────────
def check(request):
    # Recipe.objects.all() → pulls every row from Recipe table
    recipes = Recipe.objects.all()
    return render(request, "pages/check.html", {
        'recipes': recipes
    })


def check_recipe(request, recipe_id):
    user = AppUser.objects.first()  # temporary: replace with request.user later

    # recipe_id → PK from Recipe table, passed in URL e.g. /check/3/
    recipe = get_object_or_404(Recipe, id=recipe_id)
    recipe_ingredients = recipe.ingredients.all()  # ManyToMany → Ingredient table

    # my_groceries → all Ingredient rows linked to this user's Grocery entries
    my_groceries = Ingredient.objects.filter(grocery__user=user)

    # missing → recipe ingredients NOT in user's grocery list
    missing = recipe_ingredients.exclude(id__in=my_groceries)

    return render(request, 'pages/check.html', {
        'recipe': recipe,
        'missing': missing,
        'recipes': Recipe.objects.all(),  # still needed to show the recipe list on same page
    })


# ── Grocery list ────────────────────────────────────────────────────────────
def grocery(request):
    user = AppUser.objects.first()  # temporary: replace with request.user later

    if request.method == "POST":

        # Add preset ingredient — ingredient_id comes from the dropdown in grocery.html
        if 'ingredient_id' in request.POST:
            ing_id = request.POST.get('ingredient_id')
            ingredient = get_object_or_404(Ingredient, id=ing_id)
            Grocery.objects.create(user=user, ingredient=ingredient)

        # Add custom ingredient — custom_name comes from the text input
        elif 'custom_name' in request.POST:
            name = request.POST.get('custom_name', '').strip()
            if name:
                Grocery.objects.create(user=user, custom_name=name)

        return redirect('grocery')

    # GET — show the grocery list and all available preset ingredients
    groceries = Grocery.objects.filter(user=user)
    ingredients = Ingredient.objects.all()  # pulls all rows from Ingredient table

    return render(request, 'pages/grocery.html', {
        'groceries': groceries,
        'ingredients': ingredients,
    })


def remove_item(request, id):
    # id → PK of the Grocery row to delete (not the Ingredient PK)
    Grocery.objects.filter(id=id).delete()
    return redirect('grocery')


# ── Recipe list ─────────────────────────────────────────────────────────────
def recipe_list(request):
    recipes = Recipe.objects.all()

    # search → filters Recipe table by name (model field is 'name', not 'title')
    search = request.GET.get('search', '')
    if search:
        recipes = recipes.filter(name__icontains=search)  # ← 'name' matches models.py

    paginator = Paginator(recipes, 6)
    page_number = request.GET.get('page')
    recipes = paginator.get_page(page_number)

    # ── template is in pages/ folder ────────────────────────────────────────
    return render(request, 'pages/recipe_list.html', {'recipes': recipes})


# ── Recipe filter ────────────────────────────────────────────────────────────
def recipe_filter(request):
    recipes = Recipe.objects.all()

    # search
    search = request.GET.get('search', '')
    if search:
        recipes = recipes.filter(name__icontains=search)  # ← 'name' matches models.py

    # appliances — 'appliance' field exists in Recipe model
    appliances = request.GET.getlist('appliance')
    if appliances:
        recipes = recipes.filter(appliance__in=appliances)

    # cooking time — 'cooking_time' field in Recipe model (IntegerField)
    time = request.GET.get('time', '')
    if time == 'quick':
        recipes = recipes.filter(cooking_time__lt=15)
    elif time == 'medium':
        recipes = recipes.filter(cooking_time__gte=15, cooking_time__lte=30)
    elif time == 'long':
        recipes = recipes.filter(cooking_time__gt=30)

    # ── NOTE: category, budget, is_halal filters are commented out ───────────
    # These fields don't exist in your current models.py yet.
    # Add them to the Recipe model first, run migrations, then uncomment below.
    #
    # categories = request.GET.getlist('category')
    # if categories:
    #     recipes = recipes.filter(category__in=categories)
    #
    # budgets = request.GET.getlist('budget')
    # if budgets:
    #     recipes = recipes.filter(budget__in=budgets)
    #
    # halal = request.GET.get('halal', '')
    # if halal == 'true':
    #     recipes = recipes.filter(is_halal=True)
    # elif halal == 'false':
    #     recipes = recipes.filter(is_halal=False)

    return render(request, 'pages/recipe_filter.html', {'recipes': recipes})


# ── Recipe detail ────────────────────────────────────────────────────────────
def recipe_detail(request, id):
    # id → PK of Recipe table, passed in URL e.g. /recipes-detail/3/
    recipe = get_object_or_404(Recipe, id=id)
    return render(request, 'pages/recipe_detail.html', {'recipe': recipe})


# ── Saved recipes page (HTML view) ───────────────────────────────────────────
def saved_recipes(request):
    return render(request, 'pages/saved_recipes.html')


# ── Saved recipes API — GET all saved recipes ────────────────────────────────
@require_http_methods(['GET'])
def saved_recipe_list(request):
    # When user auth is ready, filter by: SavedRecipe.objects.filter(user=request.user)
    saved = SavedRecipe.objects.select_related('recipe').all()
    data = [
        {
            "saved_recipes_id": s.id,        # PK of SavedRecipe table → used to unsave
            "recipe_id":        s.recipe.id, # FK to Recipe table
            "title":            s.recipe.name, # recipe name from Recipe table
        }
        for s in saved
    ]
    return JsonResponse(data, safe=False)


# ── Saved recipes API — POST to save a recipe ────────────────────────────────
@csrf_exempt
@require_http_methods(['POST'])
def save_recipe(request):
    body = json.loads(request.body)

    # recipe_id comes from the save button's data-recipe-id in HTML
    recipe = get_object_or_404(Recipe, pk=body['recipe_id'])

    # get_or_create prevents saving the same recipe twice
    # When user auth ready, add: user=request.user
    user = AppUser.objects.first()  # temporary: replace with request.user later
    saved, created = SavedRecipe.objects.get_or_create(recipe=recipe, user=user)

    return JsonResponse({
        'saved':            True,
        'created':          created,       # False if already saved
        'saved_recipes_id': saved.id,      # PK of SavedRecipe row
        'recipe_id':        recipe.id,
    }, status=201 if created else 200)


# ── Saved recipes API — DELETE to unsave a recipe ────────────────────────────
@csrf_exempt
@require_http_methods(['DELETE'])
def unsave_recipe(request, saved_recipe_id):
    # saved_recipe_id → PK of SavedRecipe row (NOT the recipe PK)
    # This deletes the saved entry only, NOT the recipe itself
    obj = get_object_or_404(SavedRecipe, pk=saved_recipe_id)
    obj.delete()
    return JsonResponse({"deleted": True})


def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # saves into AppUser
            login(request, user)  # logs them in immediately
            return redirect("home")  # replace with your homepage URL name
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})
    """
    Signup view: accepts new user details from the form.
    Since there's no real DB yet, it checks against HARDCODED_USERS
    using email + password1, then logs the matched user in.
    """
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        email     = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "").strip()
        password2 = request.POST.get("password2", "").strip()

        # Basic validation
        if not email or not password1:
            messages.error(request, "Email and password are required.")
            return render(request, "signup.html")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "signup.html")

        # Check if user already exists
        if AppUser.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return render(request, "signup.html")

        # Create the new user
        user = AppUser.objects.create_user(
            username=email.split("@")[0],
            email=email,
            password=password1
        )
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, f"Welcome, {user.first_name}! You're now signed in.")
        return redirect("home")
    return render(request, "signup.html")


def login_view(request):
    """
    Login view: accepts email (entered in the username field) + password.
    Checks against hardcoded users, then logs in via Django's auth system.
    """
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        email    = request.POST.get("username", "").strip()   # field is named 'username' in the form
        password = request.POST.get("password", "").strip()

        # Use Django's built-in authentication
        user = authenticate(request, username=email, password=password)

        if user:
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect("home")
        else:
                messages.error(request, "Account setup incomplete. Please contact support.")

    return render(request, "login.html")


def logout_view(request):
    """Logs out via POST only (protects against accidental/CSRF logouts)."""
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been logged out successfully.")
        return redirect("login")
    # GET requests just go home
    return redirect("home")


@login_required
def home(request):
    return render(request, "home.html")


@login_required
def profile(request):
    """
    Profile view — renders user info from request.user.
    request.user is populated automatically by Django's auth middleware.
    """
    return render(request, "user_profile.html", {"user": request.user})
