from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from django.db.models import Count
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm

INDEX_PAGINATE = 10


class OnlyAuthorMixin(UserPassesTestMixin):
    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("blog:post_detail", pk=pk)


@login_required
def simple_view(request):
    return HttpResponse("Страница для залогиненных пользователей!")


def get_filtered_posts(posts, **kwargs):
    return posts.filter(**kwargs).order_by("-pub_date").annotate(
        comment_count=Count("comments")
    )


class IndexView(ListView):
    template_name = "blog/index.html"
    model = Post
    context_object_name = "page_obj"
    paginate_by = INDEX_PAGINATE

    def get_queryset(self):
        return get_filtered_posts(super().get_queryset()).filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )


class CategoryPostsView(ListView):
    template_name = "blog/category.html"
    context_object_name = "page_obj"
    paginate_by = INDEX_PAGINATE

    def get_queryset(self):
        category_slug = self.kwargs.get("category_slug")
        category = get_object_or_404(
            Category,
            slug=category_slug,
            is_published=True
        )
        posts = get_filtered_posts(
            Post.objects.filter(
                category=category,
                is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now()
            )
        )
        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs.get("category_slug")
        category = get_object_or_404(
            Category,
            slug=category_slug,
            is_published=True
        )
        context["category"] = category
        return context


def user_profile(request, username):
    template_name = "blog/profile.html"
    profile = get_object_or_404(User, username=username)

    posts = get_filtered_posts(
        Post.objects.filter(author=profile)
    )

    paginator = Paginator(posts, INDEX_PAGINATE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {"profile": profile, "page_obj": page_obj}
    return render(request, template_name, context)


class PostCreateView(LoginRequiredMixin, CreateView):
    template_name = "blog/create.html"
    model = Post
    forms_class = PostForm
    fields = (
        "title",
        "text",
        "pub_date",
        "image",
        "location",
        "category"
    )

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "blog:profile", kwargs={"username": self.request.user.username}
        )


class PostUpdateView(OnlyAuthorMixin, LoginRequiredMixin, UpdateView):
    template_name = "blog/create.html"
    model = Post
    form_class = PostForm

    def handle_no_permission(self):
        return HttpResponseRedirect(
            reverse_lazy("blog:post_detail", kwargs={"pk": self.kwargs["pk"]})
        )

    def get_success_url(self):
        return reverse_lazy("blog:post_detail", kwargs={"pk": self.object.pk})


class PostDeleteView(OnlyAuthorMixin, LoginRequiredMixin, DeleteView):
    template_name = "blog/create.html"
    model = Post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = PostForm(instance=self.object)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy(
            "blog:profile", kwargs={"username": self.request.user.username}
        )


class GetSuccessUrlMixin():
    def get_success_url(self):
        return reverse_lazy(
            "blog:post_detail",
            kwargs={"pk": self.object.post.pk}
        )


class PostDeleteCommentView(
    OnlyAuthorMixin,
    GetSuccessUrlMixin,
    LoginRequiredMixin,
    DeleteView
):
    template_name = "blog/comment.html"
    model = Comment
    form_class = CommentForm


class PostEditCommentView(
    OnlyAuthorMixin,
    GetSuccessUrlMixin,
    LoginRequiredMixin,
    UpdateView
):
    template_name = "blog/comment.html"
    model = Comment
    form_class = CommentForm


class PostDetailView(DetailView):
    template_name = "blog/detail.html"
    model = Post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CommentForm()
        context["comments"] = self.object.comments.select_related("author")
        return context

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.request.user != self.object.author:
            if not (
                self.object.is_published
                and self.object.category.is_published
                and self.object.pub_date <= timezone.now()
            ):
                raise Http404("Page not found")

        return super().dispatch(request, *args, **kwargs)


@login_required
def edit_profile(request):
    if request.method == "POST":
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            profile_url = reverse_lazy(
                "blog:profile", kwargs={"username": request.user.username}
            )
            return redirect(profile_url)
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, "blog/user.html", {"form": form})


class CustomUserChangeForm(UserChangeForm):
    password = None

    class Meta(UserChangeForm.Meta):
        fields = ("first_name", "last_name", "username", "email")
