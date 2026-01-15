from django.views.generic import ListView, DetailView
from .models import Post
from django.shortcuts import render
from django.views.generic import ListView
from .filters import NewsFilter
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Post, Category
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib import messages
from .forms import NewsForm, ArticleForm
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class AuthorRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not request.user.groups.filter(name='authors').exists():
            from django.contrib import messages
            messages.warning(request, 'Только авторы могут создавать и редактировать новости!')
            return redirect('become_author')
        return super().dispatch(request, *args, **kwargs)

@login_required
def become_author(request):
    user = request.user
    authors_group, created = Group.objects.get_or_create(name='authors')
    if not user.groups.filter(name='authors').exists():
        user.groups.add(authors_group)
        messages.success(request, 'Поздравляем! Теперь вы автор! Вы можете создавать новости и статьи.')
    else:
        messages.info(request, 'Вы уже являетесь автором.')
    return redirect('news_list')

class NewsListView(ListView):
    model = Post
    template_name = 'news/news_list.html'
    context_object_name = 'news'
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.NEWS).order_by('-created_at')


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Все новости'
        return context

class NewsDetailView(DetailView):
    model = Post
    template_name = 'news/news_detail.html'
    context_object_name = 'news'
    pk_url_kwarg = 'news_id'

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.NEWS)


class NewsSearchView(ListView):
    model = Post
    template_name = 'news/news_search.html'
    context_object_name = 'news'
    paginate_by = 10

    def get_queryset(self):
        queryset = Post.objects.filter(post_type=Post.NEWS).order_by('-created_at')
        self.filterset = NewsFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        return context

class NewsCreateView(AuthorRequiredMixin, LoginRequiredMixin, CreateView):
    model = Post
    form_class = NewsForm
    template_name = 'news/news_edit.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post_type = Post.NEWS
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('news_detail', kwargs={'pk': self.object.id})


class NewsUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = NewsForm
    template_name = 'news/news_form.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        if obj.author != request.user:
            raise PermissionDenied("Вы не являетесь автором этой новости")

        if not request.user.groups.filter(name='authors').exists():
            messages.warning(request, 'Только авторы могут редактировать новости!')
            return redirect('become_author')

        return super().dispatch(request, *args, **kwargs)
    def get_success_url(self):
        return reverse_lazy('news_detail', kwargs={'pk': self.object.id})


class NewsDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'news/news_confirm_delete.html'
    success_url = reverse_lazy('news_list')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        if obj.author != request.user:
            raise PermissionDenied("Вы не являетесь автором этой новости")

        if not request.user.groups.filter(name='authors').exists():
            messages.warning(request, 'Только авторы могут удалять новости!')
            return redirect('become_author')

        return super().dispatch(request, *args, **kwargs)


class ArticleCreateView(AuthorRequiredMixin, CreateView):
    model = Post
    form_class = ArticleForm
    template_name = 'news/article_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post_type = Post.ARTICLE
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('news_detail', kwargs={'pk': self.object.id})


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = ArticleForm
    template_name = 'news/article_form.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        if obj.author != request.user:
            raise PermissionDenied("Вы не являетесь автором этой статьи")

        if not request.user.groups.filter(name='authors').exists():
            messages.warning(request, 'Только авторы могут редактировать статьи!')
            return redirect('become_author')

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('news_detail', kwargs={'pk': self.object.id})


class ArticleDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'news/article_confirm_delete.html'
    success_url = reverse_lazy('news_list')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        if obj.author != request.user:
            raise PermissionDenied("Вы не являетесь автором этой статьи")

        if not request.user.groups.filter(name='authors').exists():
            messages.warning(request, 'Только авторы могут удалять статьи!')
            return redirect('become_author')

        return super().dispatch(request, *args, **kwargs)