from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from .models import Subscription, Post, Category
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


def send_weekly_digest():
    """Отправляет еженедельную рассылку всем подписчикам"""
    # Определяем период (последние 7 дней)
    week_ago = timezone.now() - timedelta(days=7)

    # Получаем все активные подписки
    subscriptions = Subscription.objects.select_related('user', 'category').all()

    # Группируем подписки по пользователю
    user_subscriptions = {}
    for subscription in subscriptions:
        user_id = subscription.user.id
        if user_id not in user_subscriptions:
            user_subscriptions[user_id] = {
                'user': subscription.user,
                'categories': [],
                'subscriptions': []
            }
        user_subscriptions[user_id]['categories'].append(subscription.category)
        user_subscriptions[user_id]['subscriptions'].append(subscription)

    total_emails_sent = 0

    # Для каждого пользователя формируем и отправляем письмо
    for user_data in user_subscriptions.values():
        user = user_data['user']
        categories = user_data['categories']

        # Собираем все новые статьи за неделю из категорий пользователя
        weekly_posts = Post.objects.filter(
            categories__in=categories,
            created_at__gte=week_ago,
            post_type=Post.NEWS  # Можно добавить и статьи (Post.ARTICLE)
        ).distinct().order_by('-created_at')

        # Если есть новые статьи - отправляем письмо
        if weekly_posts.exists():
            try:
                # Формируем контекст для шаблона
                context = {
                    'user': user,
                    'posts': weekly_posts,
                    'categories': categories,
                    'week_start': week_ago.date(),
                    'week_end': timezone.now().date(),
                    'post_count': weekly_posts.count(),
                }

                # HTML содержимое
                html_content = render_to_string(
                    'news/email/weekly_digest.html',
                    context
                )

                # Текстовое содержимое
                text_content = f'''
                Еженедельная рассылка новостей

                Здравствуйте, {user.username}!

                За последнюю неделю в ваших подписках появилось {weekly_posts.count()} новых статей.

                '''

                for post in weekly_posts:
                    categories_list = ', '.join([cat.name for cat in post.categories.all()])
                    text_content += f'''
                    - {post.title}
                      Категории: {categories_list}
                      Автор: {post.author.username}
                      Дата: {post.created_at.strftime("%d.%m.%Y")}
                      {post.text[:100]}...
                      Ссылка: http://127.0.0.1:8000/news/{post.id}/

                    '''

                text_content += '''
                Приятного чтения!

                Новостной портал
                '''

                # Отправляем письмо
                subject = f'Еженедельная рассылка новостей ({week_ago.date()} - {timezone.now().date()})'

                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email='weekly@newspaper.com',
                    to=[user.email],
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()

                # Обновляем дату последней рассылки для всех подписок пользователя
                for subscription in user_data['subscriptions']:
                    subscription.update_last_email()

                total_emails_sent += 1
                logger.info(f'Еженедельная рассылка отправлена пользователю {user.email}')

            except Exception as e:
                logger.error(f'Ошибка отправки еженедельной рассылки для {user.email}: {e}')

    return total_emails_sent


@shared_task
def send_new_post_notifications(post_id):
    """Асинхронная отправка уведомлений о новом посте"""
    try:
        post = Post.objects.get(id=post_id)

        if post.post_type != Post.NEWS:
            return

        categories = post.categories.all()

        for category in categories:
            subscribers = category.subscribers.all()

            for subscriber in subscribers:
                try:
                    # Пропускаем если у пользователя нет email
                    if not subscriber.email:
                        continue

                    subject = f'Новая новость: {post.title}'

                    html_content = render_to_string(
                        'news/email/new_post_notification.html',
                        {
                            'post': post,
                            'user': subscriber,
                            'category': category,
                        }
                    )

                    text_content = f'''
                    Здравствуй, {subscriber.username}. Новая статья в твоём любимом разделе!

                    Заголовок: {post.title}

                    {post.text[:50]}...

                    Читать полностью: http://127.0.0.1:8000/news/{post.id}/
                    '''

                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=text_content,
                        from_email='admin@newspaper.com',
                        to=[subscriber.email],
                    )
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()

                    logger.info(f'Email отправлен {subscriber.email} для поста {post.id}')

                except Exception as e:
                    logger.error(f'Ошибка отправки email для {subscriber.email}: {e}')

    except Post.DoesNotExist:
        logger.error(f'Пост с id {post_id} не найден')
    except Exception as e:
        logger.error(f'Ошибка в задаче send_new_post_notifications: {e}')


@shared_task
def send_weekly_newsletter():
    """Еженедельная рассылка с последними новостями"""
    try:
        # Дата неделю назад
        week_ago = timezone.now() - timedelta(days=7)

        # Получаем все категории
        categories = Category.objects.all()

        for category in categories:
            # Получаем новости за последнюю неделю в этой категории
            recent_posts = Post.objects.filter(
                categories=category,
                created_at__gte=week_ago,
                post_type=Post.NEWS
            ).order_by('-created_at')[:10]  # Последние 10 новостей

            if not recent_posts.exists():
                continue

            # Получаем подписчиков категории
            subscribers = category.subscribers.all()

            for subscriber in subscribers:
                try:
                    if not subscriber.email:
                        continue

                    subject = f'Еженедельная рассылка: Новости категории "{category.name}"'

                    html_content = render_to_string(
                        'news/email/weekly_newsletter.html',
                        {
                            'user': subscriber,
                            'category': category,
                            'posts': recent_posts,
                            'week_ago': week_ago,
                        }
                    )

                    text_content = f'''
                    Здравствуй, {subscriber.username}!

                    Еженедельная подборка новостей в категории "{category.name}".

                    За последнюю неделю опубликовано {recent_posts.count()} новостей:
                    '''

                    for post in recent_posts:
                        text_content += f'\n- {post.title}\n  {post.text[:100]}...\n'

                    text_content += '\nЧитайте на нашем портале: http://127.0.0.1:8000/news/'

                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=text_content,
                        from_email='newsletter@newspaper.com',
                        to=[subscriber.email],
                    )
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()

                    logger.info(f'Еженедельная рассылка отправлена {subscriber.email}')

                except Exception as e:
                    logger.error(f'Ошибка отправки еженедельной рассылки для {subscriber.email}: {e}')

        logger.info('Еженедельная рассылка завершена')

    except Exception as e:
        logger.error(f'Ошибка в задаче send_weekly_newsletter: {e}')


@shared_task
def test_celery():
    """Тестовая задача для проверки работы Celery"""
    print("Celery работает корректно!")
    return "Celery task executed successfully"