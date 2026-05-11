from rest_framework import serializers
from .models import RecipeComment


class RecipeCommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    # ISO timestamp → JS can format it nicely
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model  = RecipeComment
        fields = ['id', 'username', 'rating', 'body', 'created_at']
        read_only_fields = ['id', 'username', 'created_at']

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value