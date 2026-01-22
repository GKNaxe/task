from django.core.management.base import BaseCommand
from news.tasks import send_weekly_digest


class Command(BaseCommand):
    help = 'Manually send weekly newsletter to all subscribers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Send test email to admin only'
        )

    def handle(self, *args, **options):
        if options['test']:
            # Тестовая отправка администратору
            from django.contrib.auth.models import User
            from news.models import Category, Post
            from django.utils import timezone
            from datetime import timedelta

            admin = User.objects.filter(is_superuser=True).first()
            if admin:
                # Создаем тестовые данные
                category = Category.objects.first()
                if not category:
                    category = Category.objects.create(name="Тестовая")

                # Создаем тестовую статью
                post = Post.objects.create(
                    title="Тест еженедельной рассылки",
                    text="Это тестовая статья для проверки еженедельной рассылки новостей.",
                    author=admin,
                    post_type='NW'
                )
                post.categories.add(category)

                self.stdout.write(
                    self.style.SUCCESS(f'Test data created for admin {admin.email}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('No admin user found')
                )
        else:
            # Полная рассылка всем подписчикам
            count = send_weekly_digest()
            self.stdout.write(
                self.style.SUCCESS(f'Weekly newsletter sent to {count} users')
            )