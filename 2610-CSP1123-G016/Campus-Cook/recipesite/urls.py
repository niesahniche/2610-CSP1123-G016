from django.urls import path
from . import views

urlpatterns = [
    path('', views.recipe_list, name='recipe_list'),        # ← homepage now
    path('filter/', views.recipe_filter, name='recipe_filter'),
    path('recipes/<int:id>/', views.recipe_detail, name='recipe_detail'),
]