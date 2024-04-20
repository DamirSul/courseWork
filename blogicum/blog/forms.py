from django import forms
from .models import Post, Comment

from django.core.exceptions import ValidationError
from django.core.mail import send_mail


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
