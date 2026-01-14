from django.views.generic import ListView, DetailView
from .models import Post
from django.shortcuts import render
from django.views.generic import ListView
from .filters import NewsFilter
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .forms import NewsForm
from .models import Post


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

class NewsCreateView(CreateView):
    model = Post
    form_class = NewsForm
    template_name = 'news/news_edit.html'

    def form_valid(self, form):
        form.instance.post_type = Post.NEWS
        form.instance.author = Author.objects.get(user=self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
            return reverse_lazy('news_detail', kwargs={'news_id': self.object.id})

class NewsUpdateView(UpdateView):
    model = Post
    form_class = NewsForm
    template_name = 'news/news_edit.html'
    pk_url_kwarg = 'news_id'

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.NEWS)

class NewsDeleteView(DeleteView):
    model = Post
    template_name = 'news/news_delete.html'
    pk_url_kwarg = 'news_id'
    success_url = reverse_lazy('news_list')

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.NEWS)


class ArticleCreateView(CreateView):
    model = Post
    template_name = 'news/article_edit.html'
    fields = ['title', 'text', 'categories']

    def form_valid(self, form):
        form.instance.post_type = Post.ARTICLE  # ← ОТЛИЧИЕ: ARTICLE, не NEWS
        form.instance.author = Author.objects.get(user=self.request.user)
        return super().form_valid(form)


class ArticleUpdateView(UpdateView):
    model = Post
    template_name = 'news/article_edit.html'
    fields = ['title', 'text', 'categories']
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.ARTICLE)  # ← только статьи


class ArticleDeleteView(DeleteView):
    model = Post
    template_name = 'news/article_delete.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('news_list')

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.ARTICLE)