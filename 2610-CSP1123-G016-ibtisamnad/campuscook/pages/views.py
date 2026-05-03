from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import AppUserCreationForm, RecipeForm
import json

from .models import Grocery, AppUser, Recipe, SavedRecipe


# ── Home ──────────────────────────────────────────────────────────────────────
def home(request):
    return render(request, "pages/home.html")


# ── About ─────────────────────────────────────────────────────────────────────
def about(request):
    return render(request, "pages/about.html")


# ── Grocery ───────────────────────────────────────────────────────────────────
def grocery(request):
    user = request.user if request.user.is_authenticated else AppUser.objects.first()

    if request.method == "POST":
        # the text input the ingredient in grocery.html
        name = request.POST.get('name', '').strip()
        custom_name = request.POST.get('custom_name', '').strip()
        quantity = request.POST.get('quantity', '1').strip()
        try:
            quantity = int(quantity)
        except ValueError:
            quantity = 1

        if name:
            Grocery.objects.create(
                user=user,
                name=name,
                custom_name=custom_name or None,
                quantity=quantity if quantity > 0 else 1,
                status='available'
            )
        return redirect('grocery')

    # new changes groceries, now all Grocery rows belonging to the user
    available = Grocery.objects.filter(user=user, status='available')
    missing = Grocery.objects.filter(user=user, status='missing')
    return render(request, 'pages/grocery.html', {
        'available': available,
        'missing': missing,
    })


def remove_item(request, id):
    # id → PK of Grocery row to delete
    Grocery.objects.filter(id=id).delete()
    return redirect('grocery')


# ── Recipe list ───────────────────────────────────────────────────────────────
def recipe_list(request):
    recipes = Recipe.objects.all()
    search  = request.GET.get('search', '')

    if search:
        recipes = recipes.filter(name__icontains=search)
    paginator = Paginator(recipes, 6)
    recipes   = paginator.get_page(request.GET.get('page'))

    if request.user.is_authenticated:
        saved_ids = set(
            SavedRecipe.objects.filter(user=request.user)
            .values_list('recipe_id', flat=True)
        )
    else:
        saved_ids = set()
 
    return render(request, 'pages/recipe_list.html', {
        'recipes':   recipes,
        'saved_ids': list(saved_ids),
    })

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

    return render(request, 'pages/recipe_filter.html', {'recipes': recipes})


# ── Recipe detail ─────────────────────────────────────────────────────────────
def recipe_detail(request, id):
    recipe = get_object_or_404(Recipe, id=id)
    is_saved = (
        request.user.is_authenticated and
        SavedRecipe.objects.filter(user=request.user, recipe=recipe).exists()
    )
    # now no need check.html, the missing ingredients logic already transfer here ─────────────────────────────────────────────────────────────
    user   = request.user if request.user.is_authenticated else AppUser.objects.first()
    recipe_ingredients = recipe.ingredients.all()
    my_grocery_names = {
        name.strip().lower()
        for name in Grocery.objects.filter(user=user, status='available')
        .values_list('name', flat=True)
        if name
    }
    missing_ingredients = [
        ingredient
        for ingredient in recipe_ingredients
        if ingredient.name.strip().lower() not in my_grocery_names
    ]

    return render(request, 'pages/recipe_detail.html', {
        'recipe': recipe,
        'missing_ingredients': missing_ingredients,
        'recipes': Recipe.objects.all(),
        'is_saved': is_saved,
    })

# ── Add recipe ────────────────────────────────────────────────────────────────
@login_required
def add_recipe(request):
    user = request.user
    custom_ingredients_value = ''

    if request.method == 'POST':
        form = RecipeForm(request.POST)
        custom_ingredients_value = request.POST.get('custom_ingredients', '')

        # set the ingredients queryset to this user's groceries
        form.fields['ingredients'].queryset = Grocery.objects.filter(user=user, status='available')

        if form.is_valid():
            # create the Recipe row but don't save to DB yet (commit=False)
            # so we can set the user FK first
            recipe = form.save(commit=False)
            recipe.user = user  # FK → AppUser who created this recipe
            recipe.save()

            # save ManyToMany (ingredients) — must be done AFTER recipe.save()
            form.save_m2m()

            # custom_ingredients (comma separated string). now can display in recipe_detail
            custom_names = []
            custom_names_seen = set()
            for name in custom_ingredients_value.split(','):
                name = name.strip()
                normalized_name = name.lower()
                if name and normalized_name not in custom_names_seen:
                    custom_names.append(name)
                    custom_names_seen.add(normalized_name)

            for name in custom_names:
                grocery = Grocery.objects.filter(
                    user=user,
                    status='available',
                    name__iexact=name
                ).first()
                # if the custom ingredient doesn't already exist as an available grocery, create it
                if grocery is None:
                    grocery = Grocery.objects.create(
                        user=user,
                        name=name,
                        quantity=1,
                        status='available'
                    )

                recipe.ingredients.add(grocery)

            messages.success(request, f'"{recipe.name}" has been added!')

            # redirect to the new recipe's detail page
            return redirect('recipe_detail', id=recipe.id)
        else:
            messages.error(request, 'Please fix the errors below.')

    else:
        form = RecipeForm()
        form.fields['ingredients'].queryset = Grocery.objects.filter(user=user, status='available')

    # groceries → passed to template for the checkbox list
    groceries = Grocery.objects.filter(user=user, status='available')

    return render(request, 'pages/add_recipe.html', {
        'form':      form,
        'groceries': groceries,
        'custom_ingredients_value': custom_ingredients_value,
    })

# ── To Make API ───────────────────────────────────────────────────────────────
# Called when user clicks "To Make" on a saved recipe card.
# Checks which recipe ingredients the user already has (status='available')
# vs which are missing, then auto-adds missing ones to the Grocery table
# with status='missing' and a note linking back to the recipe name.
@csrf_exempt
@require_http_methods(['POST'])
def to_make(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    user   = request.user if request.user.is_authenticated else AppUser.objects.first()
 
    recipe_ingredients = recipe.ingredients.all()
 
    # available → recipe ingredients the user already has in their grocery list
    my_available = Grocery.objects.filter(user=user, status='available')
    available    = recipe_ingredients.filter(id__in=my_available.values_list('id', flat=True))
 
    # missing → recipe ingredients NOT in user's available grocery list
    missing = recipe_ingredients.exclude(id__in=my_available.values_list('id', flat=True))
 
    # auto-add missing ingredients to Grocery table with status='missing'
    # skip if already added as missing for this recipe to avoid duplicates
    added = []
    for ing in missing:
        already_missing = Grocery.objects.filter(
            user=user,
            name=ing.name,
            status='missing',
            for_recipe=recipe.name
        ).exists()
        if not already_missing:
            Grocery.objects.create(
                user=user,
                name=ing.name,
                status='missing',
                for_recipe=recipe.name,  # note links missing item to recipe
            )
            added.append(ing.name)
 
    return JsonResponse({
        'can_cook':  missing.count() == 0,
        'available': [g.name for g in available],
        'missing':   [g.name for g in missing],
        'added':     added,
        'recipe':    recipe.name,
    })

# ── Saved recipes page ────────────────────────────────────────────────────────
def saved_recipes(request):
    return render(request, 'pages/saved_recipes.html')


# ── Saved recipes API — GET ───────────────────────────────────────────────────
@require_http_methods(['GET'])
def saved_recipe_list(request):
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
        form = AppUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = AppUserCreationForm()
    return render(request, 'pages/signup.html', {'form': form})


# ── Logout ────────────────────────────────────────────────────────────────────
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect('login')
    return redirect('home')


# ── Profile ───────────────────────────────────────────────────────────────────
@login_required
def profile(request):
    saved = SavedRecipe.objects.select_related('recipe').filter(user=request.user)
    return render(request, 'pages/user_profile.html', {
        'user':          request.user,
        'saved_recipes': saved,
    })
