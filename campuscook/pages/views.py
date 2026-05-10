from django.shortcuts import render
from django.shortcuts import redirect
from .models import Grocery, AppUser , Ingredient , Recipe

def base(request):
    return render(request, "pages/base.html")

def home(request):
    return render(request, "pages/home.html")

def about(request):
    return render(request, "pages/about.html")

def check(request):
    recipes = Recipe.objects.all()
    return render(request, "pages/check.html", {
        'recipes': recipes
    })


#grocery list view
def grocery(request):
    user = AppUser.objects.first()  # temporary user

    if request.method == "POST":

        # Add preset ingredient
        if 'ingredient_id' in request.POST:
            ing_id = request.POST.get('ingredient_id')
            ingredient = Ingredient.objects.get(id=ing_id)

            Grocery.objects.create(user=user, ingredient=ingredient)

        # Add custom ingredient
        elif 'custom_name' in request.POST:
            name = request.POST.get('custom_name')

            if name:
                Grocery.objects.create(user=user, custom_name=name)

        return redirect('grocery')

    groceries = Grocery.objects.filter(user=user)
    ingredients = Ingredient.objects.all()

    return render(request, 'pages/grocery.html', {
        'groceries': groceries,
        'ingredients': ingredients
    })
    

def remove_item(request, id):
    Grocery.objects.filter(id=id).delete()
    return redirect('grocery')
    

def check_recipe(request, recipe_id):
    user = AppUser.objects.first()  # temporary user
    
    recipe = Recipe.objects.get(id=recipe_id)
    recipe_ingredients = recipe.ingredients.all()
    
    my_groceries = Ingredient.objects.filter(grocery__user=user)

    missing = recipe_ingredients.exclude(id__in=my_groceries)

    return render(request, 'pages/check.html', {
        'recipe': recipe,
        'missing': missing
    })