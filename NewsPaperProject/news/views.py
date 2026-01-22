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
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.shortcuts import redirect

class PostLimitMixin:
    """Миксин для ограничения количества публикаций в сутки"""

    def check_post_limit(self, user):
        """Проверяет, не превысил ли пользователь лимит публикаций"""
        # Определяем начало суток
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Считаем количество постов пользователя за сегодня
        today_posts_count = Post.objects.filter(
            author=user,
            created_at__gte=today_start,
            post_type=Post.NEWS  # Ограничиваем только новости, статьи не учитываем
        ).count()

        # Лимит - 3 новости в сутки
        MAX_POSTS_PER_DAY = 3

        return today_posts_count, MAX_POSTS_PER_DAY

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST':
            user = request.user
            today_posts_count, max_posts = self.check_post_limit(user)

            if today_posts_count >= max_posts:
                messages.error(
                    request,
                    f'Вы не можете публиковать более {max_posts} новостей в сутки! '
                    f'Сегодня вы уже опубликовали {today_posts_count} новостей. '
                    f'Попробуйте завтра или напишите статью вместо новости.'
                )
                return redirect('news_list')

        return super().dispatch(request, *args, **kwargs)

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


class NewsCreateView(PostLimitMixin, AuthorRequiredMixin, LoginRequiredMixin, CreateView):
    model = Post
    form_class = NewsForm
    template_name = 'news/news_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_posts_count = Post.objects.filter(
                author=user,
                created_at__gte=today_start,
                post_type=Post.NEWS
            ).count()

            context['today_posts_count'] = today_posts_count
            context['remaining_posts'] = 3 - today_posts_count

        return context


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

class CategoryNewsListView(ListView):
    """Список новостей по категории"""
    model = Post
    template_name = 'news/category_news.html'
    context_object_name = 'news_list'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(Category, id=self.kwargs['category_id'])
        return Post.objects.filter(
            categories=self.category,
            post_type=Post.NEWS
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['is_subscribed'] = (
                self.request.user.is_authenticated and
                self.request.user in self.category.subscribers.all()
        )
        return context


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category, Subscription


@login_required
def subscribe(request, category_id):
    """Подписаться на категорию"""
    category = get_object_or_404(Category, id=category_id)
    user = request.user

    # Проверяем, не подписан ли уже пользователь
    if not Subscription.objects.filter(user=user, category=category).exists():
        Subscription.objects.create(user=user, category=category)
        messages.success(request, f'Вы успешно подписались на категорию "{category.name}"')
    else:
        messages.info(request, f'Вы уже подписаны на категорию "{category.name}"')

    # Возвращаем на предыдущую страницу
    return redirect(request.META.get('HTTP_REFERER', 'news_list'))


@login_required
def unsubscribe(request, category_id):
    """Отписаться от категории"""
    category = get_object_or_404(Category, id=category_id)
    user = request.user

    # Удаляем подписку
    Subscription.objects.filter(user=user, category=category).delete()
    messages.success(request, f'Вы отписались от категории "{category.name}"')

    # Возвращаем на предыдущую страницу
    return redirect(request.META.get('HTTP_REFERER', 'news_list'))


@login_required
def my_subscriptions(request):
    """Страница моих подписок"""
    subscriptions = Subscription.objects.filter(user=request.user).select_related('category')

    context = {
        'subscriptions': subscriptions,
    }
    return render(request, 'news/my_subscriptions.html', context)


class NewsCreateView(PostLimitMixin, AuthorRequiredMixin, LoginRequiredMixin, CreateView):
    model = Post
    form_class = NewsForm
    template_name = 'news/news_form.html'

    def form_valid(self, form):
        user = self.request.user
        today_posts_count, max_posts = self.check_post_limit(user)

        # Проверяем лимит перед сохранением
        if today_posts_count >= max_posts:
            messages.error(
                self.request,
                f'Вы превысили лимит публикаций! '
                f'Максимум {max_posts} новостей в сутки. '
                f'Сегодня вы уже опубликовали {today_posts_count} новостей.'
            )
            return self.form_invalid(form)

        # Показываем информацию о лимите
        remaining_posts = max_posts - today_posts_count - 1  # -1 для текущей новости
        if remaining_posts > 0:
            messages.info(
                self.request,
                f'✅ У вас осталось {remaining_posts} новостей на сегодня'
            )
        else:
            messages.warning(
                self.request,
                f'⚠️ Это ваша последняя новость на сегодня'
            )

        # Сохраняем новость
        form.instance.author = user
        form.instance.post_type = Post.NEWS

        response = super().form_valid(form)

        # Отображаем успешное сообщение
        messages.success(
            self.request,
            f'Новость успешно создана! '
            f'Уведомления отправлены {form.instance.categories.count()} категориям.'
        )

        return response

@login_required
def user_stats(request):
    """Страница статистики пользователя"""
    user = request.user
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Статистика за сегодня
    today_posts = Post.objects.filter(
        author=user,
        created_at__gte=today_start,
        post_type=Post.NEWS
    )

    # Статистика за неделю
    week_start = timezone.now() - timedelta(days=7)
    week_posts = Post.objects.filter(
        author=user,
        created_at__gte=week_start,
        post_type=Post.NEWS
    )

    # Подписки пользователя
    subscriptions = user.subscribed_categories.all()

    context = {
        'today_posts': today_posts,
        'today_count': today_posts.count(),
        'week_count': week_posts.count(),
        'subscriptions_count': subscriptions.count(),
        'max_daily_posts': 3,
        'remaining_posts': max(0, 3 - today_posts.count()),
    }

    return render(request, 'news/user_stats.html', context)


@login_required
def subscription_settings(request):
    """Настройки подписок пользователя"""
    subscriptions = Subscription.objects.filter(user=request.user).select_related('category')

    # Получаем категории без подписки
    all_categories = Category.objects.all()
    subscribed_category_ids = subscriptions.values_list('category_id', flat=True)
    available_categories = all_categories.exclude(id__in=subscribed_category_ids)

    if request.method == 'POST':
        # Обработка изменения настроек
        action = request.POST.get('action')

        if action == 'subscribe_all':
            # Подписаться на все доступные категории
            for category in available_categories:
                Subscription.objects.get_or_create(
                    user=request.user,
                    category=category
                )
            messages.success(request, 'Вы подписались на все категории')

        elif action == 'unsubscribe_all':
            # Отписаться от всех категорий
            subscriptions.delete()
            messages.success(request, 'Вы отписались от всех категорий')

        elif action == 'update_frequency':
            # Изменить частоту уведомлений (можно расширить)
            frequency = request.POST.get('frequency', 'weekly')
            # Сохранить настройки в профиле пользователя
            messages.info(request, f'Настройки частоты обновлены: {frequency}')

        return redirect('subscription_settings')

    context = {
        'subscriptions': subscriptions,
        'available_categories': available_categories,
        'total_categories': all_categories.count(),
    }

    return render(request, 'news/subscription_settings.html', context)