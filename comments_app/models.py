from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class RecipeComment(models.Model):
    recipe = models.ForeignKey(
        'accounts.Recipe',         
        on_delete=models.CASCADE,
        related_name='comments',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe_comments',
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Star rating from 1 to 5",
    )
    body = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        # one comment per user per recipe 
        unique_together = ('recipe', 'user')

    def __str__(self):
        return f"{self.user.username} → recipe {self.recipe_id} ({self.rating}★)"