from urllib import request
from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q #perform an OR query
from .forms import AppUserCreationForm, RecipeForm, FeedbackForm, EmailOrUsernameAuthenticationForm
import json
import random
import string
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import Ingredient, Grocery, AppUser, Recipe, FavouriteRecipe, Comment, Rating

def merge_recipe_labels(existing_label, new_label):
    labels = []
    if existing_label:
        labels.extend([label.strip() for label in existing_label.split(',') if label.strip()])
    if new_label:
        labels.append(new_label.strip())
    return ', '.join(dict.fromkeys(labels))


def aggregate_grocery_items(items):
    grouped = {}
    for item in items:
        key = (
            item.name.strip().lower() if item.name else '',
            (item.custom_name or '').strip().lower()
        )
        entry = grouped.get(key)
        if not entry:
            entry = {
                'id': item.id,
                'name': item.name,
                'custom_name': item.custom_name,
                'quantity': item.quantity,
                'for_recipe': [],
            }
            grouped[key] = entry
        if item.for_recipe:
            entry['for_recipe'].extend([
                label.strip() for label in item.for_recipe.split(',') if label.strip()
            ])
        if not entry['quantity'] and item.quantity:
            entry['quantity'] = item.quantity
    for entry in grouped.values():
        entry['for_recipe'] = ', '.join(dict.fromkeys(entry['for_recipe']))
    return list(grouped.values())

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
    available_qs = Grocery.objects.filter(user=user, status='available')
    missing = Grocery.objects.filter(user=user, status='missing')
    purchased = Grocery.objects.filter(user=user, status='purchased')

    available_names = {
        name.strip().lower()
        for name in available_qs.values_list('name', flat=True)
        if name
    }

    # Determine recipe completion only from groceries labelled with recipe names
    recipe_label_map = {}
    labelled_groceries = Grocery.objects.filter(user=user).exclude(for_recipe__isnull=True).exclude(for_recipe__exact='')
    for item in labelled_groceries:
        for label in [label.strip() for label in item.for_recipe.split(',') if label.strip()]:
            recipe_label_map.setdefault(label, set()).add(item.name.strip().lower())

    completed_recipes = [
        recipe_name
        for recipe_name, labelled_names in recipe_label_map.items()
        if labelled_names and labelled_names.issubset(available_names)
    ]

    available = aggregate_grocery_items(available_qs)
    
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

# ── Transfer Purchased Items to Inventory ───────────────────────────────────
@login_required
@require_http_methods(['POST'])
def transfer_purchased_to_available(request):
    """
    Finds all grocery items for the logged-in user that are marked as 'purchased',
    and updates their status to 'available' so they count toward your pantry inventory.
    """
    # Filter items belonging to the current user with a status of 'purchased'
    purchased_items = Grocery.objects.filter(user=request.user, status='purchased')
    
    count = purchased_items.count()
    if count > 0:
        # Bulk update the status field to 'available'
        purchased_items.update(status='available')
        messages.success(request, f"Successfully transferred {count} purchased item(s) to your available inventory!")
    else:
        messages.info(request, "No purchased items found to transfer.")

    return redirect('grocery')

# ── Recipe list ───────────────────────────────────────────────────────────────
def recipe_list(request):
    recipes = Recipe.objects.all()
    
    # 1. Gather all Text Searches
    search = request.GET.get('search', '').strip()
    if search:
        recipes = recipes.filter(
            Q(name__icontains=search) | Q(ingredients__name__icontains=search)
        ).distinct()
            
    # 2. Gather Ingredient Filters
    ingredient_search_q = request.GET.get('ingredient', '').strip()
    if ingredient_search_q:
        recipes = recipes.filter(
            ingredients__name__icontains=ingredient_search_q
        ).distinct()

    # 3. Gather Meal Type Checkboxes
    meal_types = request.GET.getlist('meal_type')
    if meal_types:
        recipes = recipes.filter(meal_type__in=meal_types)

    # 4. Gather Favourite IDs Set for Logged In User
    if request.user.is_authenticated:
        favourited_ids = set(
            FavouriteRecipe.objects.filter(user=request.user)
            .values_list('recipe_id', flat=True)
        )
    else:
        favourited_ids = set()

    # 5. Process Pagination Blocks Securely
    paginator = Paginator(recipes, 6)
    recipes_page = paginator.get_page(request.GET.get('page'))
    
    # 6. Aggregate metadata loop arrays
    recipes_with_info = []
    for recipe in recipes_page:
        avg_rating = recipe.ratings.all().aggregate(Avg('stars'))['stars__avg'] or 0
        avg_rating = round(avg_rating, 1)
        total_ratings = recipe.ratings.count()
        user_name = recipe.user.username if recipe.user else "Anonymous"
        
        is_favourited = recipe.id in favourited_ids
        
        recipes_with_info.append({
            'recipe': recipe,
            'id': recipe.id,
            'avg_rating': avg_rating,
            'total_ratings': total_ratings,
            'creator': user_name,
            'is_favourited': is_favourited,
        })

    # 7. Render Template with Data Maps
    return render(request, 'pages/recipe_list.html', {
        'recipes':       recipes_with_info, # Use this array to loop through cards in your template
        'page_obj':      recipes_page,      # Common naming convention for pagination elements
        'favourited_ids': favourited_ids,
    })

# ── Recipe filter ─────────────────────────────────────────────────────────────
def recipe_filter(request):
    recipes = Recipe.objects.all()

    search = request.GET.get('search', '')
    if search:
        recipes = recipes.filter(name__icontains=search)

    selected_appliances = request.GET.getlist('appliance')
    if selected_appliances:
        recipes = recipes.filter(appliance__in=selected_appliances)

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
    selected_budgets = request.GET.getlist('budget')
    if selected_budgets:
        recipes = recipes.filter(budget__in=selected_budgets)

    selected_meal_types = request.GET.getlist('meal_type')
    if selected_meal_types:
        recipes = recipes.filter(meal_type__in=selected_meal_types)

    # min_rating filter — filters recipes whose average rating >= selected value
    # avg is computed from Rating rows linked to each recipe
    min_rating = request.GET.get('min_rating', '')
    if min_rating:
        from django.db.models import Avg
        recipes = recipes.annotate(
            avg_stars=Avg('ratings__stars')
        ).filter(avg_stars__gte=float(min_rating))

    return render(request, 'pages/recipe_filter.html', {
        'recipes': recipes,
        'selected_appliances': request.GET.getlist('appliance'),
        'selected_budgets':    request.GET.getlist('budget'),
        'selected_meal_types': request.GET.getlist('meal_type'),})


# ── Recipe detail ─────────────────────────────────────────────────────────────
@login_required
def recipe_detail(request, id):
    recipe = get_object_or_404(Recipe, id=id)
    
    # Check if a favorite connection exists for the current user and this recipe
    is_favourited = FavouriteRecipe.objects.filter(user=request.user, recipe=recipe).exists()
    
    context = {
        "recipe": recipe,
        "is_favourited": is_favourited,  # Sends the true boolean state to your template
    }
    return render(request, "pages/recipe_detail.html", context)

def popular(request):
    recipes = (
        Recipe.objects.annotate(favourite_count=Count('favourited_by'))
        .filter(favourite_count__gt=0)
        .order_by('-favourite_count', 'name')[:10]
    )
    popular_recipes = list(recipes)
    top_three = popular_recipes[:3]
    remaining = popular_recipes[3:]
    max_favourites = popular_recipes[0].favourite_count if popular_recipes else 0

    return render(request, "pages/popular.html", {
        "top_three": top_three,
        "remaining": remaining,
        "max_favourites": max_favourites,
    })

# ── Add recipe ────────────────────────────────────────────────────────────────
@login_required
def add_recipe(request):
    user = request.user
    custom_ingredients_value = ''

    if request.method == 'POST':
        form = RecipeForm(request.POST)
        # handle custom new ingredients typed in the form
        # each gets added to global Ingredient table then linked to the recipe
        custom_raw    = request.POST.get('custom_ingredients', '').strip()
        new_ingredients = []
        if custom_raw:
            for name in custom_raw.split(','):
                name = name.strip()
                if name:
                    ing, _ = Ingredient.objects.get_or_create(
                        name__iexact=name, defaults={'name': name}
                    )
                    new_ingredients.append(ing)

        if form.is_valid():
            # create the Recipe row but don't save to DB yet (commit=False)
            recipe = form.save(commit=False)
            recipe.user = user
            recipe.save()

            # save ManyToMany (ingredients)
            form.save_m2m()

            # Handle new ingredients (comma-separated input)
            new_ingredients_str = request.POST.get('new_ingredients', '').strip()
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

# ── Delete recipe API ─────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(['DELETE'])
def delete_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    # only the recipe creator can delete it
    if request.user.is_authenticated and recipe.user == request.user:
        recipe.delete()
        return JsonResponse({'deleted': True})
    return JsonResponse({'error': 'Not allowed'}, status=403)

# ── Rate recipe API ───────────────────────────────────────────────────────────
# POST → creates or updates a Rating row
# Only users who did NOT create the recipe can rate it
@csrf_exempt
@require_http_methods(['POST'])
def rate_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    user   = request.user if request.user.is_authenticated else None

    if not user:
        return JsonResponse({'error': 'Login required'}, status=401)
    if recipe.user == user:
        return JsonResponse({'error': 'Cannot rate your own recipe'}, status=403)

    body  = json.loads(request.body)
    stars = int(body.get('stars', 0))
    if not 1 <= stars <= 5:
        return JsonResponse({'error': 'Stars must be 1–5'}, status=400)

    rating, created = Rating.objects.update_or_create(
        user=user, recipe=recipe,
        defaults={'stars': stars}
    )
    return JsonResponse({
        'stars':      stars,
        'avg_rating': recipe.avg_rating,
        'created':    created,
    })


# ── Recommended recipes API ───────────────────────────────────────────────────
# GET → returns up to 4 recipes matching same meal_type, is_halal, budget
# excludes the current recipe
@require_http_methods(['GET'])
def recommended_recipes(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)

    recommended = Recipe.objects.filter(
        meal_type=recipe.meal_type,
        is_halal=recipe.is_halal,
        budget=recipe.budget,
    ).exclude(id=recipe_id).order_by('?')[:4]  # random selection

    # if fewer than 4, loosen to just same meal_type
    if recommended.count() < 4:
        extras = Recipe.objects.filter(
            meal_type=recipe.meal_type,
        ).exclude(id=recipe_id).exclude(
            id__in=[r.id for r in recommended]
        ).order_by('?')[:4 - recommended.count()]
        recommended = list(recommended) + list(extras)

    data = [
        {
            'id':         r.id,
            'name':       r.name,
            'meal_type':  r.get_meal_type_display(),
            'budget':     r.get_budget_display(),
            'is_halal':   r.is_halal,
            'image_url':  r.image_url or '',
            'avg_rating': r.avg_rating,
            'cooking_time': r.cooking_time,
        }
        for r in recommended
    ]
    return JsonResponse(data, safe=False)

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
        n.lower() for n in
        Grocery.objects.filter(user=user, status='available')
        .values_list('name', flat=True)
    )
    
    # available → recipe ingredients the user already has in their grocery list
    available = [ing for ing in recipe_ingredients if ing.name.lower() in my_available_names]
 
    # missing → recipe ingredients NOT in user's available grocery list
    missing = [ing for ing in recipe_ingredients if ing.name.lower() not in my_available_names]
 
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
        n.lower() for n in
        Grocery.objects.filter(user=user, status='available')
        .values_list('name__lower', flat=True)
    )
 
    available = [ing.name for ing in recipe_ingredients 
                 if ing.name.lower() in my_available]
    missing   = [ing.name for ing in recipe_ingredients 
                 if ing.name.lower() not in my_available]
 
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
        n.lower() for n in
        Grocery.objects.filter(user=user, status='available')
        .values_list('name__lower', flat=True)
    )
    
    added_available = []
    added_missing   = []
 
    for ing in recipe_ingredients:
        if ing.name.lower() in my_available:
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

# ── 2FA helpers ───────────────────────────────────────────────────────────────

def _generate_2fa_code():
    """Return a random 6-digit numeric string."""
    return ''.join(random.choices(string.digits, k=6))


def _send_2fa_email(email, code):
    """Sends a 2FA code email from wearecampuscook@gmail.com using settings config."""
    subject = "Your CampusCook Verification Code"
    message = (
        f"Thank you for signing up with CampusCook!\n\n"
        f"Your 6-digit verification code is: {code}\n\n"
        f"This code will expire in 10 minutes. Please enter it on the confirmation page to activate your account."
    )
    
    # settings.EMAIL_HOST_USER ensures it matches 'wearecampuscook@gmail.com' securely
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )

def _mask_email(email):
    """Return a masked version of the email, e.g. j***@gmail.com"""
    if not email or '@' not in email:
        return email
    name, domain = email.split('@', 1)
    return f"{name[0]}***@{domain}"


# ── Login view (username-or-email + password, no 2FA) ────────────────────────
def login_view(request):
    """
    Replaces Django's built-in LoginView.
    Accepts either username or email in the 'username' field, plus password.
    No 2FA here — verification only happens once, at signup, to confirm the
    email address is real. Logging in afterwards is just credentials.
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = EmailOrUsernameAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.POST.get('next') or settings.LOGIN_REDIRECT_URL
            return redirect(next_url)
        # invalid credentials — fall through to re-render with errors
    else:
        form = EmailOrUsernameAuthenticationForm(request)

    return render(request, 'pages/login.html', {'form': form})


# ── Step 2: verify the emailed code ──────────────────────────────────────────
def verify_2fa(request):
    """
    Shows the code entry form (GET) and validates the submitted code (POST).
    Requires that login_view has already stored 2fa_user_id in the session.
    """
    # Guard: must have started 2FA flow
    if '2fa_user_id' not in request.session:
        return redirect('login')

    user_id = request.session['2fa_user_id']

    try:
        user = AppUser.objects.get(pk=user_id)
    except AppUser.DoesNotExist:
        return redirect('login')

    if request.method == 'POST':
        submitted_code = request.POST.get('code', '').strip()
        stored_code    = request.session.get('2fa_code', '')
        expires_str    = request.session.get('2fa_expires', '')

        # Check expiry
        expired = False
        if expires_str:
            from django.utils.dateparse import parse_datetime
            expires_at = parse_datetime(expires_str)
            if expires_at and timezone.now() > expires_at:
                expired = True

        if expired:
            messages.error(request, 'Your code has expired. Please log in again.')
            _clear_2fa_session(request)
            return redirect('login')

        if submitted_code == stored_code:
            # Success — log the user in and clean up session
            next_url = request.session.get('2fa_next') or settings.LOGIN_REDIRECT_URL
            _clear_2fa_session(request)
            login(request, user)
            return redirect(next_url)
        else:
            messages.error(request, 'Incorrect code. Please try again.')

    return render(request, 'pages/verify_2fa.html', {
        'masked_email': _mask_email(user.email),
    })


# ── Resend the 2FA code ───────────────────────────────────────────────────────
def resend_2fa(request):
    """Generates a fresh code and re-sends it, then redirects back to verify."""
    if '2fa_user_id' not in request.session:
        return redirect('login')

    user_id = request.session['2fa_user_id']
    try:
        user = AppUser.objects.get(pk=user_id)
    except AppUser.DoesNotExist:
        return redirect('login')

    code = _generate_2fa_code()
    request.session['2fa_code']    = code
    request.session['2fa_expires'] = (
        timezone.now() + timedelta(minutes=10)
    ).isoformat()

    try:
        _send_2fa_email(user.email, code)
        messages.success(request, 'A new code has been sent to your email.')
    except Exception:
        messages.error(request, 'Could not send email. Please try again.')

    return redirect('verify_2fa')


def _clear_2fa_session(request):
    """Remove all 2FA keys from the session."""
    for key in ('2fa_user_id', '2fa_code', '2fa_expires', '2fa_next'):
        request.session.pop(key, None)


# ── Signup ────────────────────────────────────────────────────────────────────
# ── Signup ────────────────────────────────────────────────────────────────────
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = AppUserCreationForm(request.POST)
        if form.is_valid():
            # 1. Save the new user safely to the database
            user = form.save(commit=False)
            user.email = request.POST.get('email', '').strip().lower()
            user.save()
            
            # 2. Generate a secure 6-digit verification code
            code = _generate_2fa_code()
            
            # 3. Store validation profiles inside the session data store
            request.session['2fa_user_id']  = user.pk
            request.session['2fa_code']     = code
            request.session['2fa_expires']  = (timezone.now() + timedelta(minutes=10)).isoformat()
            request.session['2fa_next']     = 'home'
            
            # 4. Dispatch verification credentials to the inbox
            try:
                _send_2fa_email(user.email, code)
            except Exception:
                messages.error(request, 'Account created, but we could not send your verification email. Please try logging in to retry.')
                return redirect('login')
                
            # 5. Redirect straight to your verification terminal
            messages.success(request, "Account created successfully! Please check your email for your verification code.")
            return redirect('verify_2fa')
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

# ── Feedback ──────────────────────────────────────────────────────────────────
def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            fb = form.save(commit=False)
            if request.user.is_authenticated:
                fb.user = request.user
            fb.save()
            messages.success(request, "Thanks for your feedback — we really appreciate it!")
            return redirect('feedback')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        initial = {}
        if request.user.is_authenticated:
            initial['name'] = request.user.username
            initial['email'] = request.user.email
        form = FeedbackForm(initial=initial)
    return render(request, 'pages/feedback.html', {'form': form})

# ── Profile ───────────────────────────────────────────────────────────────────
@login_required
def profile(request):
    # Fetch user favourites 
    favourites = FavouriteRecipe.objects.select_related('recipe').filter(user=request.user)
    
    # Fetch user created recipes
    my_recipes = Recipe.objects.filter(user=request.user)
    
    # Build the set of favourited recipe IDs
    favourited_ids = set(favourites.values_list('recipe_id', flat=True))
    
    return render(request, 'pages/user_profile.html', {
        'user':           request.user,
        'favourites':     favourites,
        'my_recipes':     my_recipes,
        'favourited_ids': favourited_ids,
    })

# ── Profile Update ────────────────────────────────────────────────────────────
@login_required
def profile_update(request):
    """
    Handles the profile update form submission. Validates unique username
    and updates the current user's profile information.
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()

        # Validation checks matching signup/login style
        if not username or not email:
            messages.error(request, "Username and Email fields cannot be blank.")
            return redirect('profile')

        # Check if the chosen username is taken by another user
        if AppUser.objects.filter(username__iexact=username).exclude(pk=request.user.pk).exists():
            messages.error(request, f"The username '{username}' is already taken.")
            return redirect('profile')

        try:
            # Update user instance
            user = request.user
            user.username = username
            user.email = email
            user.save(update_fields=['username', 'email'])
            
            messages.success(request, "Your profile has been successfully updated!")
        except Exception as e:
            messages.error(request, f"An error occurred while saving: {str(e)}")
            
    return redirect('profile')

# ── Comments API ──────────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(['POST'])
def add_comment(request, recipe_id):
    """Add a comment to a recipe"""
    recipe = get_object_or_404(Recipe, id=recipe_id)
    user = request.user if request.user.is_authenticated else AppUser.objects.first()
    
    try:
        data = json.loads(request.body)
        commentary = data.get('comment', '').strip()
        
        if not commentary:
            return JsonResponse({'error': 'Comment cannot be empty'}, status=400)
        
        comment = Comment.objects.create(
            user=user,
            recipe=recipe,
            commentary=commentary
        )
        
        return JsonResponse({
            'success': True,
            'comment_id': comment.id,
            'username': user.username,
            'commentary': commentary,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(['GET'])
def get_comments(request, recipe_id):
    """Get all comments for a recipe"""
    recipe = get_object_or_404(Recipe, id=recipe_id)
    comments = Comment.objects.filter(recipe=recipe)
    
    data = [
        {
            'comment_id': c.id,
            'username': c.user.username,
            'commentary': c.commentary,
            'created_at': c.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for c in comments
    ]
    return JsonResponse(data, safe=False)

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