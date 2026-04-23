from django.shortcuts import render

def base(request):
    return render(request, "pages/base.html")

def home(request):
    return render(request, "pages/home.html")

def about(request):
    return render(request, "pages/about.html")

def grocery(request):
    return render(request, "pages/grocery.html")

