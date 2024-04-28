from . import views

from django.urls import path

app_name = "blog"

urlpatterns = [
    path("posts/create/", views.PostCreateView.as_view(), name="create_post"),
    path("posts/<int:pk>/edit/",
         views.PostUpdateView.as_view(),
         name="edit_post"
         ),
    path("posts/<int:pk>/delete/",
         views.PostDeleteView.as_view(),
         name="delete_post"
         ),
    path("<int:pk>/comment/", views.add_comment, name="add_comment"),
    path(
        "posts/<int:post_pk>/delete_comment/<int:pk>/",
        views.PostDeleteCommentView.as_view(),
        name="delete_comment",
    ),
    path(
        "posts/<int:post_pk>/edit_comment/<int:pk>/",
        views.PostEditCommentView.as_view(),
        name="edit_comment",
    ),
    path("", views.IndexView.as_view(), name="index"),
    path("posts/<int:pk>/",
         views.PostDetailView.as_view(),
         name="post_detail"
         ),
    path(
        "category/<slug:category_slug>/",
        views.CategoryPostsView.as_view(),
        name="category_posts",
    ),
    path("profile/edit_profile/", views.edit_profile, name="edit_profile"),
    path("profile/<path:username>/", views.user_profile, name="profile"),
]
