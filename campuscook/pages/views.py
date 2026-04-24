from django.shortcuts import render

def base(request):
    return render(request, "pages/base.html")

def home(request):
    return render(request, "pages/home.html")

def about(request):
    return render(request, "pages/about.html")


#paste your all views here
from django.shortcuts import render
from django.shortcuts import redirect
from .models import Grocery, AppUser , Ingredient

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
    