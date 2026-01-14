import django_filters
from django import forms
from .models import Post


class NewsFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(
        field_name='title',
        lookup_expr='icontains',
        label='Заголовок содержит:'  # ← ЭТО покажется пользователю
    )

    author_name = django_filters.CharFilter(
        field_name='author__user__username',
        lookup_expr='icontains',
        label='Имя автора:'  # ← ЭТО покажется пользователю
    )

    after_date = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Не раньше даты:',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = Post
        fields = []

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        # Сначала фильтруем только новости
        if queryset is None:
            queryset = Post.objects.filter(post_type=Post.NEWS)
        else:
            queryset = queryset.filter(post_type=Post.NEWS)

        super().__init__(data, queryset, request=request, prefix=prefix)