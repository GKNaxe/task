from django.test import TestCase
from django.contrib.auth.models import User
from news.models import Category, Post


class ModelsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Технологии')

    def test_category_str(self):
        """Тест строкового представления категории"""
        self.assertEqual(str(self.category), 'Технологии')

    def test_post_creation(self):
        """Тест создания новости"""
        post = Post.objects.create(
            title='Тестовая новость',
            text='Текст новости',
            author=self.user,
            post_type=Post.NEWS
        )
        post.categories.add(self.category)

        self.assertEqual(post.title, 'Тестовая новость')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.post_type, Post.NEWS)
        self.assertTrue(self.category in post.categories.all())

    def test_post_str(self):
        """Тест строкового представления новости"""
        post = Post.objects.create(
            title='Тест',
            text='Текст',
            author=self.user,
            post_type=Post.NEWS
        )
        self.assertEqual(str(post), 'Тест')