from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from .forms import AppUserCreationForm, RecipeForm
import json

from .models import Ingredient, Grocery, AppUser, Recipe, FavouriteRecipe, Rating


# ── Home ──────────────────────────────────────────────────────────────────────
def home(request):
    return render(request, "pages/home.html")

# ── About ─────────────────────────────────────────────────────────────────────
def about(request):
    return render(request, "pages/about.html")

# ── Ingredient search API ─────────────────────────────────────────────────────
# GET /api/ingredients/?q=chicken
# Returns matching Ingredient rows as JSON for autocomplete in grocery/add_recipe
@require_http_methods(['GET'])
def ingredient_search(request):
    q = request.GET.get('q', '').strip()
    if q:
        ingredients = Ingredient.objects.filter(name__icontains=q).order_by('name')[:20]
    else:
        ingredients = Ingredient.objects.all().order_by('name')[:50]
    data = [{'id': i.id, 'name': i.name} for i in ingredients]
    return JsonResponse(data, safe=False)

# ── Grocery ───────────────────────────────────────────────────────────────────
def grocery(request):
    user = request.user if request.user.is_authenticated else AppUser.objects.first()

    if request.method == "POST":
        action = request.POST.get('action', '')
        
        # Add from existing ingredients dropdown
        if action == 'add_from_dropdown':
            ingredient_id = request.POST.get('ingredient_id', '').strip()
            custom_name = request.POST.get('custom_name', '').strip()
            quantity = request.POST.get('quantity', '').strip() or '1'
            
            if ingredient_id:
                try:
                    ingredient = Ingredient.objects.get(id=ingredient_id)
                    existing = Grocery.objects.filter(
                        user=user,
                        name=ingredient.name,
                        status='available'
                    ).first()
                    
                    if existing:
                        existing.quantity = quantity
                        existing.save(update_fields=['quantity'])
                        messages.success(request, f'{ingredient.name} quantity updated to {quantity}.')
                    else:
                        Grocery.objects.create(
                            user=user,
                            name=ingredient.name,
                            custom_name=custom_name or None,
                            quantity=quantity,
                            status='available'
                        )
                        messages.success(request, f'Added {ingredient.name} to your grocery list!')
                except Ingredient.DoesNotExist:
                    messages.error(request, 'Ingredient not found.')
        
        # Add new ingredients (comma-separated)
        elif action == 'add_new_ingredients':
            new_ingredients_str = request.POST.get('new_ingredients', '').strip()
            
            if new_ingredients_str:
                ingredient_names = [name.strip() for name in new_ingredients_str.split(',') if name.strip()]
                added_count = 0
                
                for name in ingredient_names:
                    # Create Ingredient if it doesn't exist
                    ingredient, created = Ingredient.objects.get_or_create(name=name)
                    
                    # Check if already exists for user
                    existing = Grocery.objects.filter(
                        user=user,
                        name=name,
                        status='available'
                    ).exists()
                    
                    if not existing:
                        Grocery.objects.create(
                            user=user,
                            name=name,
                            status='available',
                            quantity='1'
                        )
                        added_count += 1
                
                if added_count > 0:
                    messages.success(request, f'Added {added_count} ingredient(s) to your grocery list!')
                else:
                    messages.info(request, 'These ingredients were already in your grocery list.')
        
        return redirect('grocery')

    # Get all available ingredients for dropdown
    all_ingredients = Ingredient.objects.all().order_by('name')
    
    # Get user's grocery items
    available = Grocery.objects.filter(user=user, status='available')
    missing = Grocery.objects.filter(user=user, status='missing')
    purchased = Grocery.objects.filter(user=user, status='purchased')
    
    return render(request, 'pages/grocery.html', {
        'all_ingredients': all_ingredients,
        'available': available,
        'missing': missing,
        'purchased': purchased,
        'missing_count': missing.count() + purchased.count(),
    })


def purchase_item(request, id):
    grocery_item = get_object_or_404(Grocery, id=id)
    grocery_item.status = 'purchased'
    grocery_item.save(update_fields=['status'])
    return redirect('grocery')


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
            # search by ingredient name — filters recipes that contain a matching ingredient
    ingredient_search_q = request.GET.get('ingredient', '')
    if ingredient_search_q:
        recipes = recipes.filter(
            ingredients__name__icontains=ingredient_search_q
        ).distinct()
    paginator = Paginator(recipes, 6)
    recipes_page = paginator.get_page(request.GET.get('page'))

    if request.user.is_authenticated:
        fav_ids = set(
            FavouriteRecipe.objects.filter(user=request.user)
            .values_list('recipe_id', flat=True)
        )
    else:
        fav_ids = set()
    
    # Add rating and creator info to each recipe
    recipes_with_info = []
    for recipe in recipes_page:
        avg_rating = recipe.ratings.all().aggregate(Avg('stars'))['stars__avg'] or 0
        avg_rating = round(avg_rating, 1)
        total_ratings = recipe.ratings.count()
        recipes_with_info.append({
            'recipe': recipe,
            'avg_rating': avg_rating,
            'total_ratings': total_ratings,
            'creator': recipe.user.username,
        })
 
    return render(request, 'pages/recipe_list.html', {
        'recipes':   recipes_with_info,
        'page':      recipes_page,
        'fav_ids':   list(fav_ids),
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

    # halal filter — Recipe.is_halal (BooleanField)
    halal = request.GET.get('halal', '')
    if halal == 'true':
        recipes = recipes.filter(is_halal=True)
    elif halal == 'false':
        recipes = recipes.filter(is_halal=False)
 
    # budget filter — Recipe.budget (CharField with choices)
    budgets = request.GET.getlist('budget')
    if budgets:
        recipes = recipes.filter(budget__in=budgets)

    return render(request, 'pages/recipe_filter.html', {'recipes': recipes})


# ── Recipe detail ─────────────────────────────────────────────────────────────
def recipe_detail(request, id):
    recipe = get_object_or_404(Recipe, id=id)
    is_fav = (
        request.user.is_authenticated and
        FavouriteRecipe.objects.filter(user=request.user, recipe=recipe).exists()
    )
    
    # Get ratings for this recipe
    ratings = recipe.ratings.all()
    avg_rating = ratings.aggregate(Avg('stars'))['stars__avg'] or 0
    avg_rating = round(avg_rating, 1)
    total_ratings = ratings.count()
    
    # Check if current user has already rated
    user_rating = None
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(user=request.user, recipe=recipe).first()

    rating_choices = [1, 2, 3, 4, 5]

    return render(request, 'pages/recipe_detail.html', {
        'recipe':          recipe,
        'is_saved':        is_fav,
        'avg_rating':      avg_rating,
        'total_ratings':   total_ratings,
        'user_rating':     user_rating,
        'rating_choices':  rating_choices,
    })

# ── Add recipe ────────────────────────────────────────────────────────────────
@login_required
def add_recipe(request):
    user = request.user

    if request.method == 'POST':
        form = RecipeForm(request.POST)

        if form.is_valid():
            # create the Recipe row but don't save to DB yet (commit=False)
            recipe = form.save(commit=False)
            recipe.user = user
            recipe.save()

            # save ManyToMany (ingredients)
            form.save_m2m()

            # Handle new ingredients typed in add_recipe.html.
            # Each name is saved globally, then linked to this recipe.
            new_ingredients_str = request.POST.get('new_ingredients', '').strip()
            new_ingredients = []
            if new_ingredients_str:
                for name in new_ingredients_str.split(','):
                    name = name.strip()
                    if name:
                        ing, _ = Ingredient.objects.get_or_create(
                            name__iexact=name,
                            defaults={'name': name},
                        )
                        new_ingredients.append(ing)

            if new_ingredients:
                recipe.ingredients.add(*new_ingredients)
            messages.success(request, f'"{recipe.name}" has been added!')
            return redirect('recipe_detail', id=recipe.id)
        else:
            messages.error(request, 'Please fix the errors below.')

    else:
        form = RecipeForm()
        form.fields['ingredients'].queryset = Ingredient.objects.all()

    # Pass all ingredients to template
    all_ingredients = Ingredient.objects.all().order_by('name')

    return render(request, 'pages/add_recipe.html', {
        'form': form,
        'all_ingredients': all_ingredients,
    })

# ── To Make API ───────────────────────────────────────────────────────────────
# Called when user clicks "To Make" on a recipe card.
# Checks which recipe ingredients the user already has (available in grocery)
# vs which are missing, then auto-adds missing ones to the Grocery table
@csrf_exempt
@require_http_methods(['POST'])
def to_make(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    user   = request.user if request.user.is_authenticated else AppUser.objects.first()
 
    recipe_ingredients = recipe.ingredients.all()
 
    # Get ingredient names user has available in their grocery list
    my_available_names = set(
        Grocery.objects.filter(user=user, status='available')
        .values_list('name', flat=True)
    )
    
    # available → recipe ingredients the user already has in their grocery list
    available = recipe_ingredients.filter(name__in=my_available_names)
 
    # missing → recipe ingredients NOT in user's available grocery list
    missing = recipe_ingredients.exclude(name__in=my_available_names)
 
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
                for_recipe=recipe.name,
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
    
    # Get ingredient names user has available in their grocery list
    my_available = set(
        Grocery.objects.filter(user=user, status='available')
        .values_list('name', flat=True)
    )
    my_available_normalized = {name.strip().lower() for name in my_available if name}
 
    available = [
        ing.name for ing in recipe_ingredients
        if ing.name.strip().lower() in my_available_normalized
    ]
    missing = [
        ing.name for ing in recipe_ingredients
        if ing.name.strip().lower() not in my_available_normalized
    ]
 
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
    
    # Get ingredient names user has available in their grocery list
    my_available = set(
        Grocery.objects.filter(user=user, status='available')
        .values_list('name', flat=True)
    )
    my_available_normalized = {name.strip().lower() for name in my_available if name}
    
    added_available = []
    added_missing   = []
 
    for ing in recipe_ingredients:
        if ing.name.strip().lower() in my_available_normalized:
            # user already has this
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
    return render(request, 'pages/user_profile.html', {
        'user':              request.user,
        'favourites': favourites,
    })


# ── Rating API ────────────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(['POST'])
def rate_recipe(request, recipe_id):
    """Add or update a rating for a recipe"""
    recipe = get_object_or_404(Recipe, id=recipe_id)
    user = request.user if request.user.is_authenticated else AppUser.objects.first()
    
    try:
        data = json.loads(request.body)
        stars = int(data.get('stars', 0))
        
        if stars < 1 or stars > 5:
            return JsonResponse({'error': 'Stars must be between 1 and 5'}, status=400)
        
        # Create or update rating
        rating, created = Rating.objects.update_or_create(
            user=user,
            recipe=recipe,
            defaults={'stars': stars}
        )
        
        # Calculate new average
        avg_rating = recipe.ratings.all().aggregate(Avg('stars'))['stars__avg'] or 0
        avg_rating = round(avg_rating, 1)
        total_ratings = recipe.ratings.count()
        
        return JsonResponse({
            'success': True,
            'stars': stars,
            'avg_rating': avg_rating,
            'total_ratings': total_ratings,
            'created': created,
        }, status=201 if created else 200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(['GET'])
def get_recipe_ratings(request, recipe_id):
    """Get rating stats for a recipe"""
    recipe = get_object_or_404(Recipe, id=recipe_id)
    ratings = recipe.ratings.all()
    
    avg_rating = ratings.aggregate(Avg('stars'))['stars__avg'] or 0
    avg_rating = round(avg_rating, 1)
    total_ratings = ratings.count()
    
    # Get distribution of ratings
    distribution = {}
    for i in range(1, 6):
        distribution[i] = ratings.filter(stars=i).count()
    
    return JsonResponse({
        'avg_rating': avg_rating,
        'total_ratings': total_ratings,
        'distribution': distribution,
    })
