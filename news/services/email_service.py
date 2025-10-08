from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


class EmailService:
    @staticmethod
    def send_welcome_email(user, activation_url):
        """
        Отправка приветственного письма с ссылкой активации
        """
        subject = 'Добро пожаловать в News Portal! Подтвердите вашу регистрацию'

        # Контекст для шаблона
        context = {
            'username': user.username,
            'activation_url': activation_url,
            'site_url': settings.SITE_URL,
            'support_email': 'support@newshub.com'
        }

        # HTML версия письма
        html_content = render_to_string('emails/welcome_email.html', context)

        # Текстовая версия письма (для клиентов без HTML поддержки)
        text_content = render_to_string('emails/welcome_email.txt', context)

        # Создание письма
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")

        try:
            email.send()
            print(f"Приветственное письмо отправлено на {user.email}")
            return True
        except Exception as e:
            print(f"Ошибка отправки email для {user.email}: {e}")
            return False

    @staticmethod
    def send_activation_success_email(user):
        """
        Отправка письма об успешной активации
        """
        subject = 'Аккаунт успешно активирован!'

        context = {
            'username': user.username,
            'site_url': settings.SITE_URL,
            'login_url': f"{settings.SITE_URL}/accounts/login/"
        }

        html_content = render_to_string('emails/activation_success.html', context)
        text_content = render_to_string('emails/activation_success.txt', context)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")

        try:
            email.send()
            print(f"Письмо об успешной активации отправлено на {user.email}")
            return True
        except Exception as e:
            print(f"Ошибка отправки email активации для {user.email}: {e}")
            return False