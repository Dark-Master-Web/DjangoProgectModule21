from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User


class EmailService:

    @staticmethod
    def send_welcome_email(user, activation_url):
        """Отправка приветственного письма с активацией"""
        subject = 'Добро пожаловать в News Portal!'

        context = {
            'user': user,
            'activation_url': activation_url,
            'site_url': settings.SITE_URL
        }

        text_content = render_to_string('emails/welcome_email.txt', context)
        html_content = render_to_string('emails/welcome_email.html', context)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

    @staticmethod
    def send_activation_success_email(user):
        """Отправка письма об успешной активации"""
        subject = 'Аккаунт успешно активирован!'

        context = {
            'user': user,
            'site_url': settings.SITE_URL
        }

        text_content = render_to_string('emails/activation_success.txt', context)
        html_content = render_to_string('emails/activation_success.html', context)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

    @staticmethod
    def send_new_post_notification(post):
        """Отправка уведомлений о новой новости подписчикам категорий"""
        categories = post.categories.all()

        for category in categories:
            subscribers = category.subscribers.all()

            for subscriber in subscribers:
                if subscriber.email:
                    subject = f'Новая новость в категории "{category.name}"'

                    context = {
                        'subscriber': subscriber,
                        'post': post,
                        'category': category,
                        'site_url': settings.SITE_URL,
                        'post_url': f"{settings.SITE_URL}/news/{post.id}/"
                    }

                    text_content = render_to_string('emails/new_post_notification.txt', context)
                    html_content = render_to_string('emails/new_post_notification.html', context)

                    email = EmailMultiAlternatives(
                        subject=subject,
                        body=text_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[subscriber.email]
                    )
                    email.attach_alternative(html_content, "text/html")
                    email.send()