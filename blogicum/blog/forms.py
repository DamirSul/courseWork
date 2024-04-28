from django import forms

from .models import Post, Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = (
            "is_published",
            "author",
        )
        widgets = {"post": forms.DateInput(attrs={"type": "date"})}
