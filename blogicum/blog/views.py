from django.shortcuts import get_object_or_404, render
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from django.db.models import Count
from blogicum.settings import LEFT_LIMIT, RIGHT_LIMIT
from blog.models import Post, Category, Comment
from .forms import PostForm, CommentForm
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.mixins import AccessMixin
from django.http import Http404
from django.utils import timezone

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

class IndexView(ListView):
    template_name = "blog/index.html"
    model = Post
    context_object_name = "page_obj"
    paginate_by = 10

    def get_queryset(self):
        posts = (
            super()
            .get_queryset()
            .filter(is_published=True, category__is_published=True)
            .order_by("-pub_date")
            .annotate(comment_count=Count("comments"))
        )
        return posts

class CategoryPostsView(ListView):
    template_name = "blog/category.html"
    context_object_name = "page_obj"
    paginate_by = 10

    def get_queryset(self):
        category_slug = self.kwargs.get("category_slug")
        category = get_object_or_404(Category, slug=category_slug, is_published=True)
        posts = (
            get_posts_qs()
            .filter(category=category)
            .order_by("-pub_date")
            .annotate(comment_count=Count("comments"))
        )
        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs.get("category_slug")
        category = get_object_or_404(
            Category, 
            slug=category_slug, 
            is_published=True,)
        context["category"] = category
        return context

def get_posts_qs():
    # cur_date = timezone.now()
    return Post.objects.filter(
        # pub_date__lte=cur_date,
        is_published=True,
        category__is_published=True,
    )

def user_profile(request, username):
    template_name = "blog/profile.html"
    profile = get_object_or_404(User, username=username)
    posts = (
        Post.objects.filter(author=profile)
        .order_by("-pub_date")
        .annotate(comment_count=Count("comments"))
    )
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {"profile": profile, "page_obj": page_obj}
    return render(request, template_name, context)

class PostCreateView(LoginRequiredMixin, CreateView):
    template_name = "blog/create.html"
    model = Post
    forms_class = PostForm
    fields = ("title", "text", "pub_date", "image", "location", "category")

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
        return HttpResponseRedirect(reverse_lazy("blog:post_detail", kwargs={"pk": self.kwargs["pk"]}))

    def get_success_url(self):
        return reverse_lazy("blog:post_detail", kwargs={"pk": self.object.pk})

class PostDeleteView(OnlyAuthorMixin, LoginRequiredMixin, DeleteView):
    template_name = "blog/create.html"
    model = Post
    success_url = reverse_lazy("blog:profile")

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

class PostDeleteCommentView(OnlyAuthorMixin, LoginRequiredMixin, DeleteView):
    template_name = "blog/comment.html"
    model = Comment
    form_class = CommentForm

    def get_success_url(self):
        return reverse_lazy("blog:post_detail", kwargs={"pk": self.object.post.pk})

class PostEditCommentView(OnlyAuthorMixin, LoginRequiredMixin, UpdateView):
    template_name = "blog/comment.html"
    model = Comment
    form_class = CommentForm

    def get_success_url(self):
        return reverse_lazy("blog:post_detail", kwargs={"pk": self.object.post.pk})

class PostDetailView(DetailView):
    template_name = "blog/detail.html"
    model = Post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CommentForm()
        context["comments"] = self.object.comments.select_related("author")
        return context
    
    def dispatch(self, request, *args, **kwargs):
        """
        Переопределение метода dispatch() для дополнительной проверки.
        """
        self.object = self.get_object()

        print(f"is_published: {self.object.is_published}")
        print(f"category.is_published: {self.object.category.is_published}")
        print(f"pub_date: {self.object.pub_date}")

        
        if self.request.user != self.object.author:
            if not (self.object.is_published and self.object.category.is_published and self.object.pub_date <= timezone.now()):
                raise Http404("Page not found")
        return super().dispatch(request, *args, **kwargs)

@login_required
def edit_profile(request):
    if request.method == "POST":
        form = CustomUserChangeForm(
            request.POST,
            instance=request.user,
        )
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
