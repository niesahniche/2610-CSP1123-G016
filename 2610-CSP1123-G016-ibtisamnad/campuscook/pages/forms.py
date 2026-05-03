from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import AppUser, Recipe, Grocery

class AppUserCreationForm(UserCreationForm):
    class Meta:
        model  = AppUser
        fields = ('username', 'password1', 'password2')

class RecipeForm(forms.ModelForm):
    # ingredients → ManyToManyField to Grocery table
    # shown as checkboxes in the template
    # queryset is set dynamically in the view based on logged-in user
    ingredients = forms.ModelMultipleChoiceField(
        queryset=Grocery.objects.none(),  # overridden in view
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
 
    class Meta:
        model  = Recipe
        # user and filters are excluded — user is set automatically in the view
        fields = ('name', 'cooking_time', 'appliance', 'instructions', 'ingredients')
 