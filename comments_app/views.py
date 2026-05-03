from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

from .models import RecipeComment
from .serializers import RecipeCommentSerializer


# ─── GET /api/comments/<recipe_id>/  ──────────────────────────────────────────
@require_http_methods(["GET"])
def comment_list(request, recipe_id):
    """Return all comments for a recipe, newest first."""
    qs = (
        RecipeComment.objects
        .filter(recipe_id=recipe_id)
        .select_related('user')
        .order_by('-created_at')
    )
    serializer = RecipeCommentSerializer(qs, many=True)

    # also compute average rating
    ratings  = list(qs.values_list('rating', flat=True))
    avg      = round(sum(ratings) / len(ratings), 1) if ratings else None
    user_comment_id = None

    if request.user.is_authenticated:
        own = qs.filter(user=request.user).first()
        if own:
            user_comment_id = own.id

    return JsonResponse({
        'comments':        serializer.data,
        'count':           len(serializer.data),
        'average_rating':  avg,
        'user_comment_id': user_comment_id,
    })


# ─── POST /api/comments/<recipe_id>/  ─────────────────────────────────────────
@login_required
@require_http_methods(["POST"])
def comment_create(request, recipe_id):
    """Create (or update) the current user's comment on a recipe."""
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    # upsert: one comment per user per recipe
    obj, created = RecipeComment.objects.get_or_create(
        recipe_id=recipe_id,
        user=request.user,
        defaults={'rating': payload.get('rating', 5), 'body': payload.get('body', '')},
    )
    if not created:
        obj.rating = payload.get('rating', obj.rating)
        obj.body   = payload.get('body', obj.body)
        obj.save()

    serializer = RecipeCommentSerializer(obj)
    status_code = 201 if created else 200
    return JsonResponse(serializer.data, status=status_code)


# ─── DELETE /api/comments/delete/<comment_id>/  ───────────────────────────────
@login_required
@require_http_methods(["DELETE"])
def comment_delete(request, comment_id):
    """Delete the current user's own comment."""
    try:
        comment = RecipeComment.objects.get(id=comment_id, user=request.user)
    except RecipeComment.DoesNotExist:
        return JsonResponse({'error': 'Comment not found.'}, status=404)

    comment.delete()
    return JsonResponse({'deleted': comment_id}, status=200)