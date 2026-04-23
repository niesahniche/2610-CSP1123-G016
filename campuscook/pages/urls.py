from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("grocery/", views.grocery, name="grocery"),
    path('grocery_test/', views.grocery_test, name='grocery'),
]
