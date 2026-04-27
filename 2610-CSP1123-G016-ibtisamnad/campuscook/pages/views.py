from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
import json

from .models import Grocery, AppUser, Ingredient, Recipe, SavedRecipe


# ── Home — public, no login required ─────────────────────────────────────────
def home(request):
    return render(request, "pages/home.html")


# ── About ─────────────────────────────────────────────────────────────────────
def about(request):
    return render(request, "pages/about.html")


# ── Check recipe ──────────────────────────────────────────────────────────────
def check(request):
    recipes = Recipe.objects.all()
    return render(request, "pages/check.html", {'recipes': recipes})


def check_recipe(request, recipe_id):
    user = request.user if request.user.is_authenticated else AppUser.objects.first()
    recipe = get_object_or_404(Recipe, id=recipe_id)
    recipe_ingredients = recipe.ingredients.all()
    my_groceries = Ingredient.objects.filter(grocery__user=user)
    missing = recipe_ingredients.exclude(id__in=my_groceries)
    return render(request, 'pages/check.html', {
        'recipe':  recipe,
        'missing': missing,
        'recipes': Recipe.objects.all(),
    })


# ── Grocery ───────────────────────────────────────────────────────────────────
def grocery(request):
    user = request.user if request.user.is_authenticated else AppUser.objects.first()

    if request.method == "POST":
        if 'ingredient_id' in request.POST:
            ingredient = get_object_or_404(Ingredient, id=request.POST.get('ingredient_id'))
            Grocery.objects.create(user=user, ingredient=ingredient)
        elif 'custom_name' in request.POST:
            name = request.POST.get('custom_name', '').strip()
            if name:
                Grocery.objects.create(user=user, custom_name=name)
        return redirect('grocery')

    return render(request, 'pages/grocery.html', {
        'groceries':   Grocery.objects.filter(user=user),
        'ingredients': Ingredient.objects.all(),
    })


def remove_item(request, id):
    Grocery.objects.filter(id=id).delete()
    return redirect('grocery')


# ── Recipe list ───────────────────────────────────────────────────────────────
def recipe_list(request):
    recipes = Recipe.objects.all()
    search = request.GET.get('search', '')
    if search:
        recipes = recipes.filter(name__icontains=search)
    paginator = Paginator(recipes, 6)
    recipes   = paginator.get_page(request.GET.get('page'))
    return render(request, 'pages/recipe_list.html', {'recipes': recipes})


# ── Recipe filter ─────────────────────────────────────────────────────────────
def recipe_filter(request):
    recipes = Recipe.objects.all()

    search = request.GET.get('search', '')
    if search:
        recipes = recipes.filter(name__icontains=search)

    appliances = request.GET.getlist('appliance')
    if appliances:
        recipes = recipes.filter(appliance__in=appliances)

    time = request.GET.get('time', '')
    if time == 'quick':
        recipes = recipes.filter(cooking_time__lt=15)
    elif time == 'medium':
        recipes = recipes.filter(cooking_time__gte=15, cooking_time__lte=30)
    elif time == 'long':
        recipes = recipes.filter(cooking_time__gt=30)

    # ── add category/budget/halal filters here once added to models.py ───────

    return render(request, 'pages/recipe_filter.html', {'recipes': recipes})


# ── Recipe detail ─────────────────────────────────────────────────────────────
def recipe_detail(request, id):
    recipe = get_object_or_404(Recipe, id=id)
    return render(request, 'pages/recipe_detail.html', {'recipe': recipe})


# ── Saved recipes page (HTML shell) ──────────────────────────────────────────
def saved_recipes(request):
    return render(request, 'pages/saved_recipes.html')


# ── Saved recipes API — GET ───────────────────────────────────────────────────
@require_http_methods(['GET'])
def saved_recipe_list(request):
    # Filter by logged-in user; fall back to all for testing
    if request.user.is_authenticated:
        saved = SavedRecipe.objects.select_related('recipe').filter(user=request.user)
    else:
        saved = SavedRecipe.objects.select_related('recipe').all()

    data = [
        {
            "saved_recipes_id": s.id,
            "recipe_id":        s.recipe.id,
            "title":            s.recipe.name,
        }
        for s in saved
    ]
    return JsonResponse(data, safe=False)


# ── Saved recipes API — POST ──────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(['POST'])
def save_recipe(request):
    body   = json.loads(request.body)
    recipe = get_object_or_404(Recipe, pk=body['recipe_id'])
    user   = request.user if request.user.is_authenticated else AppUser.objects.first()
    saved, created = SavedRecipe.objects.get_or_create(recipe=recipe, user=user)
    return JsonResponse({
        'saved':            True,
        'created':          created,
        'saved_recipes_id': saved.id,
        'recipe_id':        recipe.id,
    }, status=201 if created else 200)


# ── Saved recipes API — DELETE ────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(['DELETE'])
def unsave_recipe(request, saved_recipe_id):
    obj = get_object_or_404(SavedRecipe, pk=saved_recipe_id)
    obj.delete()
    return JsonResponse({"deleted": True})


# ── Signup ────────────────────────────────────────────────────────────────────
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # Creates AppUser row in database using AbstractUser's UserCreationForm
            user = form.save()
            # Log user in immediately after signing up
            login(request, user)
            messages.success(request, f"Welcome, {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = UserCreationForm()

    # form is passed to signup.html so {{ form.errors }} and field values work
    return render(request, 'pages/signup.html', {'form': form})


# ── Logout ────────────────────────────────────────────────────────────────────
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect('login')
    return redirect('home')


# ── Profile — requires login ──────────────────────────────────────────────────
@login_required
def profile(request):
    # saved_recipes → SavedRecipe rows for this user, joined with Recipe table
    # passed to user_profile.html as {{ saved_recipes }} for the recipe grid
    saved = SavedRecipe.objects.select_related('recipe').filter(user=request.user)
    return render(request, 'pages/user_profile.html', {
        'user':          request.user,
        'saved_recipes': saved,
    })