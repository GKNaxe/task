from django.views.generic import ListView, DetailView
from .models import Post


class NewsListView(ListView):
    model = Post
    template_name = 'news/news_list.html'
    context_object_name = 'news'

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