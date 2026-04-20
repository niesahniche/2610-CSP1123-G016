from django.shortcuts import render

def home(request):
    return render(request, "recipesite/home.html")

def about(request):
    return render(request, "recipesite/about.html")

def grocery(request):
    return render(request, "recipesite/grocery.html")
