from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from news.models import Category, Post


class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Создаем группы
        self.common_group = Group.objects.create(name='common')
        self.authors_group = Group.objects.create(name='authors')

        # Создаем обычного пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.groups.add(self.common_group)

        # Создаем автора
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='authorpass123'
        )
        self.author.groups.add(self.authors_group)

        # Создаем категорию
        self.category = Category.objects.create(name='Политика')

        # Создаем новость
        self.post = Post.objects.create(
            title='Тестовая новость',
            text='Текст тестовой новости',
            author=self.author,
            post_type=Post.NEWS
        )
        self.post.categories.add(self.category)

    def test_home_page(self):
        """Тест главной страницы"""
        response = self.client.get(reverse('news_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Новостной портал')

    def test_login_required_for_create(self):
        """Тест: Создание новости требует авторизации"""
        # Без авторизации
        response = self.client.get(reverse('news_create'))
        self.assertNotEqual(response.status_code, 200)

        # С авторизацией обычного пользователя
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('news_create'))
        # Должен быть редирект на "Стать автором" или ошибка доступа
        self.assertNotEqual(response.status_code, 200)

        # С авторизацией автора
        self.client.login(username='author', password='authorpass123')
        response = self.client.get(reverse('news_create'))
        self.assertEqual(response.status_code, 200)

    def test_subscribe_view(self):
        """Тест подписки на категорию"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(
            reverse('subscribe', kwargs={'category_id': self.category.id})
        )

        # Должен быть редирект
        self.assertEqual(response.status_code, 302)

        # Проверяем, что пользователь подписан
        self.assertTrue(self.user in self.category.subscribers.all())