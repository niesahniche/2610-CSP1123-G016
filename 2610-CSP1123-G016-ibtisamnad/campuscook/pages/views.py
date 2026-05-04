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

from .models import Grocery, AppUser, Recipe, FavouriteRecipe


# ── Home ──────────────────────────────────────────────────────────────────────
def home(request):
    return render(request, "pages/home.html")


# ── About ─────────────────────────────────────────────────────────────────────
def about(request):
    return render(request, "pages/about.html")


# ── Check recipe ──────────────────────────────────────────────────────────────
def check_recipe(request, recipe_id):
    user   = request.user if request.user.is_authenticated else AppUser.objects.first()
    recipe = get_object_or_404(Recipe, id=recipe_id)

    # recipe_ingredients → Grocery items linked to this recipe via ManyToMany
    recipe_ingredients = recipe.ingredients.all()

    # my_groceries → Grocery items owned by this user
    my_available = Grocery.objects.filter(user=user, status='available')

    # available → recipe ingredients the user already has in their grocery list
    available = recipe_ingredients.filter(id__in=my_available.values_list('id', flat=True))
    
    # missing → recipe ingredients NOT in user's grocery list
    missing = recipe_ingredients.exclude(id__in=my_available.values_list('id', flat=True))

    return render(request, 'pages/check.html', {
        'recipe':  recipe,
        'missing': missing,
        'available': available,
        'recipes': Recipe.objects.all(),
    })


# ── Grocery ───────────────────────────────────────────────────────────────────
def grocery(request):
    user = request.user if request.user.is_authenticated else AppUser.objects.first()

    if request.method == "POST":
        # name comes from the text input in grocery.html
        name = request.POST.get('name', '').strip()
        custom_name = request.POST.get('custom_name', '').strip()
        if name:
            Grocery.objects.create(user=user, name=name, custom_name=custom_name or None, status='available')
        return redirect('grocery')

    # groceries → all Grocery rows belonging to this user
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
        fav_ids = set(
            FavouriteRecipe.objects.filter(user=request.user)
            .values_list('recipe_id', flat=True)
        )
    else:
        fav_ids = set()
 
    return render(request, 'pages/recipe_list.html', {
        'recipes':   recipes,
        'fav_ids': list(fav_ids),
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
    is_fav = (
        request.user.is_authenticated and
        FavouriteRecipe.objects.filter(user=request.user, recipe=recipe).exists()
    )
    return render(request, 'pages/recipe_detail.html', {
        'recipe':   recipe,
        'is_saved': is_fav,
    })

# ── Add recipe ────────────────────────────────────────────────────────────────
@login_required
def add_recipe(request):
    user = request.user

    if request.method == 'POST':
        form = RecipeForm(request.POST)

        # set the ingredients queryset to this user's groceries
        form.fields['ingredients'].queryset = Grocery.objects.filter(user=user, status='available')

        #custom ingredients coding here sammm hehe!

        if form.is_valid():
            # create the Recipe row but don't save to DB yet (commit=False)
            # so we can set the user FK first
            recipe = form.save(commit=False)
            recipe.user = user  # FK → AppUser who created this recipe
            recipe.save()

            # save ManyToMany (ingredients) — must be done AFTER recipe.save()
            form.save_m2m()

            #another custom ingredients logic

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

# ── Favourite recipes page ────────────────────────────────────────────────────────
def favourite_recipes(request):
    return render(request, 'pages/favourite_recipes.html')

@require_http_methods(['GET'])
def favourite_recipe_list(request):
    user = request.user if request.user.is_authenticated else AppUser.objects.first()
    favs = FavouriteRecipe.objects.select_related('recipe').filter(user=user)
    data = [
        {
            'fav_id':    f.id,
            'recipe_id': f.recipe.id,
            'title':     f.recipe.name,
            'image_url': f.recipe.image_url or '',
        }
        for f in favs
    ]
    return JsonResponse(data, safe=False)

# ── Favourite list API — returns JSON list of user's favourites ───────────────
@require_http_methods(['GET'])
def favourite_recipe_list(request):
    user = request.user if request.user.is_authenticated else AppUser.objects.first()
    favs = FavouriteRecipe.objects.select_related('recipe').filter(user=user)
    data = [
        {
            'fav_id':    f.id,
            'recipe_id': f.recipe.id,
            'title':     f.recipe.name,
            'image_url': f.recipe.image_url or '',
        }
        for f in favs
    ]
    return JsonResponse(data, safe=False)

# ── Favourite API — toggle (POST = favourite, DELETE = unfavourite) ───────────
@csrf_exempt
@require_http_methods(['POST', 'DELETE'])
def toggle_favourite(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    user   = request.user if request.user.is_authenticated else AppUser.objects.first()
 
    if request.method == 'POST':
        fav, created = FavouriteRecipe.objects.get_or_create(user=user, recipe=recipe)
        return JsonResponse({
            'favourited': True,
            'created':    created,
            'fav_id':     fav.id,
        }, status=201 if created else 200)
 
    # DELETE — unfavourite
    FavouriteRecipe.objects.filter(user=user, recipe=recipe).delete()
    return JsonResponse({'favourited': False})
 
 
# ── Ingredient check API — Step 1: returns available/missing lists ────────────
# Called from recipe detail page when user clicks "Check Ingredients"
# Does NOT add anything to grocery yet — just returns the data for Step 1
@csrf_exempt
@require_http_methods(['POST'])
def check_ingredients(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    user   = request.user if request.user.is_authenticated else AppUser.objects.first()
 
    recipe_ingredients = recipe.ingredients.all()
    my_available = Grocery.objects.filter(user=user, status='available')
 
    available = [g.name for g in recipe_ingredients
                 if my_available.filter(id=g.id).exists()]
    missing   = [g.name for g in recipe_ingredients
                 if not my_available.filter(id=g.id).exists()]
 
    return JsonResponse({
        'recipe':    recipe.name,
        'recipe_id': recipe.id,
        'available': available,
        'missing':   missing,
        'can_cook':  len(missing) == 0,
    })
 
 
# ── Ingredient add API — Step 2: adds all to grocery after user confirms ──────
# Called when user clicks "Add to Grocery List" after seeing Step 1 results
# Adds available items (status='available') and missing items (status='missing')
@csrf_exempt
@require_http_methods(['POST'])
def add_ingredients_to_grocery(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    user   = request.user if request.user.is_authenticated else AppUser.objects.first()
 
    recipe_ingredients = recipe.ingredients.all()
    my_available = Grocery.objects.filter(user=user, status='available')
    added_available = []
    added_missing   = []
 
    for ing in recipe_ingredients:
        has_it = my_available.filter(id=ing.id).exists()
 
        if has_it:
            # user already has this — mark as available (it's already there,
            # but we confirm it's linked to this recipe for reference)
            added_available.append(ing.name)
        else:
            # user doesn't have this — add as missing with recipe note
            already = Grocery.objects.filter(
                user=user, name=ing.name,
                status='missing', for_recipe=recipe.name
            ).exists()
            if not already:
                Grocery.objects.create(
                    user=user, name=ing.name,
                    status='missing', for_recipe=recipe.name
                )
            added_missing.append(ing.name)
 
    return JsonResponse({
        'recipe':           recipe.name,
        'added_available':  added_available,
        'added_missing':    added_missing,
        'can_cook':         len(added_missing) == 0,
    })

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
    favourites = FavouriteRecipe.objects.select_related('recipe').filter(user=request.user)
    print("FAVOURITES",  list(favourites))  # Debug print to check the queryset contents
    return render(request, 'pages/user_profile.html', {
        'user':              request.user,
        'favourites': favourites,
    })