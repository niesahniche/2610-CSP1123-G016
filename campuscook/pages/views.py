from django.shortcuts import render

def base(request):
    return render(request, "pages/base.html")

def home(request):
    return render(request, "pages/home.html")

def about(request):
    return render(request, "pages/about.html")

def grocery(request):
    return render(request, "pages/grocery.html")

from django.shortcuts import render
from .models import Grocery, AppUser

def grocery_test(request):
    user = AppUser.objects.first()  #take first user from database for demonstration
    groceries = Grocery.objects.filter(user=user)

    return render(request, 'pages/grocery_test.html', {
        'groceries': groceries
    })
    
