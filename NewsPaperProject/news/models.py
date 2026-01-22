from django.db import models
from django.contrib.auth.models import User
from django.forms import CharField
from django.urls import reverse
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    subscribers = models.ManyToManyField(
        User,
        through='Subscription',
        related_name='subscribed_categories',
        blank=True
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_news', kwargs={'category_id': self.id})


class Subscription(models.Model):
    """Промежуточная модель для подписок с дополнительными полями"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    last_weekly_email = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'category']

    def __str__(self):
        return f"{self.user.username} подписан на {self.category.name}"

    def update_last_email(self):
        """Обновляет дату последней рассылки"""
        self.last_weekly_email = timezone.now()
        self.save()

class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)

    def update_rating(self):
        post_rating = 0
        for post in self.post_set.all():
            post_rating += post.rating
        post_rating *= 3

        comment_rating = 0
        for comment in Comment.objects.filter(user=self.user):
            comment_rating += comment.rating

        post_comments_rating = 0
        for post in self.post_set.all():
            for comment in post.comment_set.all():
                post_comments_rating += comment.rating

        self.rating = post_rating + comment_rating + post_comments_rating
        self.save()
        return self.rating

class PostCategory(models.Model):  # ← ИСПРАВИЛ ЗДЕСЬ!
    post = models.ForeignKey('Post', on_delete=models.CASCADE)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)

class Post(models.Model):
    ARTICLE = 'AR'
    NEWS = 'NW'
    POST_TYPES = [
        (ARTICLE, 'Статья'),
        (NEWS, 'Новость'),
    ]

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    post_type = models.CharField(max_length=2, choices=POST_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    text = models.TextField()
    rating = models.IntegerField(default=0)
    categories = models.ManyToManyField(Category, through='PostCategory')

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()

    def preview(self):
        return f"{self.text[:124]}..."

class Comment(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(default=0)

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()


class WeeklyDigest(models.Model):
    """Модель для хранения отправленных еженедельных дайджестов"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)
    period_start = models.DateTimeField()  # Начало периода (понедельник)
    period_end = models.DateTimeField()  # Конец периода (воскресенье)
    posts_count = models.IntegerField(default=0)  # Количество новостей в рассылке

    def __str__(self):
        return f"Дайджест {self.category.name} за {self.period_start.date()}"

    class Meta:
        ordering = ['-sent_at']