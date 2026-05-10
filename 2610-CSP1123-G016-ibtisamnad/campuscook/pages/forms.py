from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import AppUser, Recipe, Ingredient

class AppUserCreationForm(UserCreationForm):
    class Meta:
        model  = AppUser
        fields = ('username', 'password1', 'password2')

class RecipeForm(forms.ModelForm):
    # ingredients → ManyToManyField to Ingredient table
    # shown as checkboxes in the template
    ingredients = forms.ModelMultipleChoiceField(
        queryset=Ingredient.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
 
    class Meta:
        model  = Recipe
        # user and filters are excluded — user is set automatically in the view
        fields = ('name', 'cooking_time', 'appliance', 'instructions', 'image_url', 'ingredients', 'is_halal', 'budget')