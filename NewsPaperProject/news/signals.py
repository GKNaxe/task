from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.models import User, Group
from django.utils import timezone
from .models import Post, Category, Subscription
import logging
from datetime import timedelta
from .tasks import send_new_post_notifications

logger = logging.getLogger(__name__)


# 1. Сигнал для добавления в группу common
@receiver(post_save, sender=User)
def add_user_to_common_group(sender, instance, created, **kwargs):
    if created:
        try:
            common_group, _ = Group.objects.get_or_create(name='common')
            instance.groups.add(common_group)
            logger.info(f'Пользователь {instance.username} добавлен в группу "common"')
        except Exception as e:
            logger.error(f'Ошибка добавления пользователя в группу common: {e}')


# 2. Сигнал для отправки email при создании новости
@receiver(post_save, sender=Post)
def notify_subscribers_on_post_create(sender, instance, created, **kwargs):
    """
    Отправляет уведомления подписчикам при создании новости
    """
    if created and instance.post_type == Post.NEWS:
        # Получаем категории новости
        categories = instance.categories.all()

        if not categories:
            logger.info(f'Новость "{instance.title}" без категорий, уведомления не отправляются')
            return

        logger.info(f'Отправка уведомлений о новости "{instance.title}"')

        for category in categories:
            send_category_notification(instance, category)


def send_category_notification(post, category):
    """Отправляет уведомление подписчикам категории"""
    subscribers = category.subscribers.all()

    if not subscribers:
        logger.info(f'В категории "{category.name}" нет подписчиков')
        return

    logger.info(f'Отправка уведомлений для категории "{category.name}" ({len(subscribers)} подписчиков)')

    email_count = 0
    for subscriber in subscribers:
        try:
            # Формируем email
            subject = f'🔔 Новая новость в категории "{category.name}": {post.title}'

            html_content = render_to_string(
                'news/email/category_update.html',
                {
                    'post': post,
                    'user': subscriber,
                    'category': category,
                    'unsubscribe_url': f'http://127.0.0.1:8000/news/category/{category.id}/unsubscribe/',
                }
            )

            text_content = f'''
            Здравствуй, {subscriber.username}!

            📰 Новая новость в категории "{category.name}":

            Заголовок: {post.title}
            Автор: {post.author.username}
            Дата публикации: {post.created_at.strftime("%d.%m.%Y %H:%M")}

            Краткое содержание:
            {post.text[:100]}...

            ➡️ Читать полностью: http://127.0.0.1:8000/news/{post.id}/

            ---
            Вы получили это письмо, потому что подписаны на категорию "{category.name}"
            Чтобы отписаться: http://127.0.0.1:8000/news/category/{category.id}/unsubscribe/
            '''

            # Отправляем email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email='noreply@newspaper.com',
                to=[subscriber.email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            email_count += 1
            logger.debug(f'Email отправлен {subscriber.email}')

        except Exception as e:
            logger.error(f'Ошибка отправки email для {subscriber.email}: {e}')

    logger.info(f'Отправлено {email_count} email уведомлений для категории "{category.name}"')

@receiver(post_save, sender=Post)
def notify_subscribers_async(sender, instance, created, **kwargs):
    """Отправляет уведомления подписчикам через Celery"""
    if created and instance.post_type == Post.NEWS:
        # Запускаем асинхронную задачу
        send_new_post_notifications.delay(instance.id)
        print(f'Задача отправки уведомлений поставлена в очередь для поста {instance.id}')