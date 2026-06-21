from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import AppUser, Recipe, Ingredient, Feedback

class AppUserCreationForm(UserCreationForm):
    # Added explicitly so it's required and validated (uniqueness + format)
    # rather than silently ignored by UserCreationForm's default field set.
    email = forms.EmailField(required=True, help_text='Used to send your login verification code.')

    class Meta:
        model  = AppUser
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if AppUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

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

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ('name', 'email', 'rating', 'message')
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5, 'placeholder': "Tell us what you think, what you'd like to see, or anything that's bugging you..."}),}