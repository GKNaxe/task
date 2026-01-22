from django.urls import path, include
from django.contrib import admin
from . import views
from django.contrib.auth import views as auth_views
from .views import NewsListView, NewsDetailView
from .views import NewsSearchView
from .views import subscribe, unsubscribe, my_subscriptions
from .views import (
    NewsListView, NewsDetailView, NewsSearchView,
    NewsCreateView, NewsUpdateView, NewsDeleteView,
    ArticleCreateView, ArticleUpdateView, ArticleDeleteView,
    become_author, subscribe, unsubscribe, my_subscriptions,
    CategoryNewsListView
)
from .views import become_author
urlpatterns = [
    path('', NewsListView.as_view(), name='news_list'),
    path('<int:news_id>/', NewsDetailView.as_view(), name='news_detail'),
    path('', NewsListView.as_view(), name='news_list'),
    path('<int:news_id>/', NewsDetailView.as_view(), name='news_detail'),
    path('search/', NewsSearchView.as_view(), name='news_search'),
    path('', NewsListView.as_view(), name='news_list'),
    path('<int:news_id>/', NewsDetailView.as_view(), name='news_detail'),
    path('search/', NewsSearchView.as_view(), name='news_search'),
    path('create/', NewsCreateView.as_view(), name='news_create'),
    path('<int:news_id>/edit/', NewsUpdateView.as_view(), name='news_edit'),
    path('<int:news_id>/delete/', NewsDeleteView.as_view(), name='news_delete'),
    path('articles/create/', ArticleCreateView.as_view(), name='article_create'),
    path('articles/<int:pk>/edit/', ArticleUpdateView.as_view(), name='article_edit'),
    path('articles/<int:pk>/delete/', ArticleDeleteView.as_view(), name='article_delete'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('become-author/', become_author, name='become_author'),
    path('category/<int:category_id>/', CategoryNewsListView.as_view(), name='category_news'),
    path('category/<int:category_id>/subscribe/', subscribe, name='subscribe'),
    path('category/<int:category_id>/unsubscribe/', unsubscribe, name='unsubscribe'),
    path('my-subscriptions/', my_subscriptions, name='my_subscriptions'),
    path('subscriptions/settings/', subscription_settings, name='subscription_settings'),
]