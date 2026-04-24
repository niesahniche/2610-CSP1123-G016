from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("grocery/", views.grocery, name="grocery"),
    path("check/<int:recipe_id>/", views.check_recipe, name="check_recipe"),
    path('remove/<int:id>/', views.remove_item, name='remove_item'),
    
]


