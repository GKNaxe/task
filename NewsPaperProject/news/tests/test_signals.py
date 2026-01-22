from django.test import TestCase, override_settings
from django.contrib.auth.models import User, Group
from news.models import Category, Post


class SignalsTestCase(TestCase):
    def setUp(self):
        """Настройка тестовых данных"""
        # Создаем группы
        self.common_group = Group.objects.create(name='common')
        self.authors_group = Group.objects.create(name='authors')

        # Создаем категории
        self.category1 = Category.objects.create(name='Политика')
        self.category2 = Category.objects.create(name='Спорт')

    def test_user_auto_add_to_common_group(self):
        """Тест: Новый пользователь автоматически добавляется в группу common"""
        # Создаем нового пользователя
        user = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='password123'
        )

        # Проверяем
        self.assertTrue(user.groups.filter(name='common').exists())
        self.assertEqual(user.groups.count(), 1)

    def test_subscribe_to_category(self):
        """Тест: Пользователь может подписаться на категорию"""
        # Создаем пользователя
        user = User.objects.create_user(
            username='subscriber',
            email='subscriber@example.com',
            password='password123'
        )

        # Подписываем
        self.category1.subscribers.add(user)

        # Проверяем
        self.assertTrue(user in self.category1.subscribers.all())
        self.assertEqual(self.category1.subscribers.count(), 1)

    def test_create_post_with_category(self):
        """Тест: Создание новости с категорией"""
        # Создаем автора
        author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='password123'
        )
        author.groups.add(self.authors_group)

        # Создаем подписчика
        subscriber = User.objects.create_user(
            username='subscriber2',
            email='subscriber2@example.com',
            password='password123'
        )
        self.category1.subscribers.add(subscriber)

        # Создаем новость
        post = Post.objects.create(
            title='Тестовая новость',
            text='Текст тестовой новости для проверки.',
            author=author,
            post_type=Post.NEWS
        )
        post.categories.add(self.category1)

        # Проверяем
        self.assertEqual(post.title, 'Тестовая новость')
        self.assertEqual(post.categories.count(), 1)
        self.assertTrue(self.category1 in post.categories.all())