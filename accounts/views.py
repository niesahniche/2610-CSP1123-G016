from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

 
 
# ------- 2 Hardcoded Users -------
HARDCODED_USERS = [
    {
        "name": "Khairin Aqilah",
        "username": "qyla",
        "email": "khairin.aqilah@gmail.com",
        "password": "2809",
    },
    {
        "name": "Khairol Zharfan",
        "username": "kai",
        "email": "khai.zhar@gmail.com",
        "password": "6311",
    },
]

def create_hardcoded_users():
    """Creates the hardcoded users since database don't exist yet."""
    for u in HARDCODED_USERS:
        if not User.objects.filter(username=u["username"]).exists():
            new_user = User.objects.create_user(
                username=u["username"],
                email=u["email"],
                first_name=u["name"],
            )
            new_user.set_password(u["password"])
            new_user.save()

# Auto-create hardcoded users when the app loads
try:
    create_hardcoded_users()
except Exception:
    pass
# ---------------------------------------------------  

def find_hardcoded_user(email, password):
    """Returns matching hardcoded user dict, or None."""
    for u in HARDCODED_USERS:
        if u["email"] == email and u["password"] == password:
            return u
    return None
def find_user_by_username(username, password):
    for u in HARDCODED_USERS:
        if u["username"] == username and u["password"] == password:
            return u
    return None
         

def signup(request):
    if request.user.is_authenticated:
        return redirect("home")  
 
    if request.method == "POST":
        # Check if submitted details match one of the hardcoded users
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password1", "").strip() # matches name="password1" in signup.html
        matched = find_hardcoded_user(email, password)
        
        if matched:
            try:
                user = User.objects.get(username=matched["username"])
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                messages.success(request, f"Welcome, {matched['name']}! You're now signed in.")
                return redirect("home")
            except User.DoesNotExist:
                messages.error(request, "Account setup incomplete. Please contact support.")
        else:
            messages.error(request, "These details do not match any registered account.")
 
    return render(request, "pages/signup.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    
    if request.method == "POST":
        email = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        matched = find_user_by_username(email, password)

        if matched:
            try:
                user = User.objects.get(username=matched["username"])
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                messages.success(request, f"Welcome back, {matched['name']}!")
                return redirect("home")
            except User.DoesNotExist:
                messages.error(request, "Account setup incomplete. Please contact support.")
        else:
            messages.error(request, "Invalid email or password.")
 
    return render(request, "pages/login.html")


def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been logged out successfully.")
        return redirect("login")
    # If someone visits /logout/ via GET, redirect to home
    return redirect("home")


@login_required
def home(request):
    return render(request, "pages/home.html", {"user": request.user}) #passes user to template

@login_required
def profile(request):
    return render(request, "pages/user_profile.html", {"user": request.user})
def about(request):
    return render(request, "pages/about.html")

@login_required
def grocery(request):
    return render(request, "pages/grocery.html")


# ── Imports for recipe views ──────────────────────────────────────────────────
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from .models import Recipe, Ingredient, SavedRecipe
import json


# ── Recipe list ───────────────────────────────────────────────────────────────
@login_required
def recipe_list(request):
    search = request.GET.get('search', '')
    recipes = Recipe.objects.all()
    if search:
        recipes = recipes.filter(name__icontains=search)
    paginator = Paginator(recipes, 6)
    page = request.GET.get('page')
    recipes = paginator.get_page(page)
    return render(request, "pages/recipe_list.html", {"recipes": recipes})


# ── Recipe detail ─────────────────────────────────────────────────────────────
@login_required
def recipe_detail(request, id):
    recipe = get_object_or_404(Recipe, pk=id)
    return render(request, "pages/recipe_detail.html", {"recipe": recipe})


# ── Recipe filter ─────────────────────────────────────────────────────────────
@login_required
def recipe_filter(request):
    recipes = Recipe.objects.all()
    search = request.GET.get('search', '')
    time   = request.GET.get('time', '')
    appliances = request.GET.getlist('appliance')
    if search:
        recipes = recipes.filter(name__icontains=search)
    if time == 'quick':
        recipes = recipes.filter(cooking_time__lt=15)
    elif time == 'medium':
        recipes = recipes.filter(cooking_time__gte=15, cooking_time__lte=30)
    elif time == 'long':
        recipes = recipes.filter(cooking_time__gt=30)
    if appliances:
        recipes = recipes.filter(appliance__in=appliances)
    return render(request, "pages/recipe_filter.html", {"recipes": recipes})


# ── Saved recipes page ────────────────────────────────────────────────────────
@login_required
def saved_recipes(request):
    return render(request, "pages/saved_recipes.html")


# ── Save recipe API ───────────────────────────────────────────────────────────
@login_required
@require_http_methods(["POST"])
def save_recipe(request):
    data = json.loads(request.body)
    recipe = get_object_or_404(Recipe, pk=data.get('recipe_id'))
    obj, created = SavedRecipe.objects.get_or_create(user=request.user, recipe=recipe)
    return JsonResponse({'created': created})


# ── Saved recipe list API ─────────────────────────────────────────────────────
@login_required
def saved_recipe_list(request):
    saved = SavedRecipe.objects.filter(user=request.user).select_related('recipe')
    data = [
        {
            'saved_recipes_id': s.id,
            'recipe_id':        s.recipe.id,
            'title':            s.recipe.name,
        }
        for s in saved
    ]
    return JsonResponse(data, safe=False)


# ── Unsave recipe API ─────────────────────────────────────────────────────────
@login_required
@require_http_methods(["DELETE"])
def unsave_recipe(request, saved_recipe_id):
    obj = get_object_or_404(SavedRecipe, pk=saved_recipe_id, user=request.user)
    obj.delete()
    return JsonResponse({'deleted': saved_recipe_id})


# ── Remove grocery item ───────────────────────────────────────────────────────
@login_required
def remove_item(request, id):
    return redirect('grocery')

