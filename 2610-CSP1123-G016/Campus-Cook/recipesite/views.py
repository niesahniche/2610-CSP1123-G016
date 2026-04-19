from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Recipe

def recipe_list(request):
    recipes = Recipe.objects.all().order_by('-created_at')

    search = request.GET.get('search', '')
    if search:
        recipes = recipes.filter(title__icontains=search)

    paginator = Paginator(recipes, 6)
    page_number = request.GET.get('page')
    recipes = paginator.get_page(page_number)

    return render(request, 'recipesite/recipe_list.html', {'recipes': recipes})


def recipe_filter(request):
    recipes = Recipe.objects.all()

    search = request.GET.get('search', '')
    if search:
        recipes = recipes.filter(title__icontains=search)

    categories = request.GET.getlist('category')
    if categories:
        recipes = recipes.filter(category__in=categories)

    budgets = request.GET.getlist('budget')
    if budgets:
        recipes = recipes.filter(budget__in=budgets)

    appliances = request.GET.getlist('appliance')
    if appliances:
        recipes = recipes.filter(appliance__in=appliances)

    time = request.GET.get('time', '')
    if time == 'quick':
        recipes = recipes.filter(time_minutes__lt=15)
    elif time == 'medium':
        recipes = recipes.filter(time_minutes__gte=15, time_minutes__lte=30)
    elif time == 'long':
        recipes = recipes.filter(time_minutes__gt=30)

    halal = request.GET.get('halal', '')
    if halal == 'true':
        recipes = recipes.filter(is_halal=True)
    elif halal == 'false':
        recipes = recipes.filter(is_halal=False)

    return render(request, 'recipesite/recipe_filter.html', {'recipes': recipes})


def recipe_detail(request, id):
    recipe = get_object_or_404(Recipe, id=id)
    return render(request, 'recipesite/recipe_detail.html', {'recipe': recipe})