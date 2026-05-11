from django.urls import path
from . import views

urlpatterns = [
    # List comments for a recipe
    path('api/comments/<int:recipe_id>/',         views.comment_list,   name='comment_list'),
    # Create / upsert a comment
    path('api/comments/<int:recipe_id>/create/',  views.comment_create, name='comment_create'),
    # Delete a specific comment (owner only)
    path('api/comments/delete/<int:comment_id>/', views.comment_delete, name='comment_delete'),
]

# ── How to include these in your project's main urls.py ───────────────────────
#
#   from django.urls import path, include
#
#   urlpatterns = [
#       ...
#       path('', include('comments.urls')),   # or whatever your app is named
#   ]