from django.db import models
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string  # 🆕 КРИТИЧЕСКИ ВАЖНЫЙ ИМПОРТ
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)

    def update_rating(self):
        # Ваша логика расчета рейтинга
        pass

    def __str__(self):
        return self.user.username


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    subscribers = models.ManyToManyField(User, through='Subscription', related_name='subscribed_categories', blank=True)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.category.name}"


class Post(models.Model):
    ARTICLE = 'AR'
    NEWS = 'NW'
    POST_TYPES = [
        (ARTICLE, 'Статья'),
        (NEWS, 'Новость'),
    ]

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    post_type = models.CharField(max_length=2, choices=POST_TYPES, default=ARTICLE)
    categories = models.ManyToManyField(Category, through='PostCategory')
    title = models.CharField(max_length=255)
    content = models.TextField()
    rating = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def preview(self):
        return self.content[:124] + '...' if len(self.content) > 124 else self.content

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()

    def send_notifications_to_subscribers(self):
        """Отправляет уведомления подписчикам категорий поста"""
        categories = self.categories.all()
        for category in categories:
            subscribers = category.subscribers.all()
            for subscriber in subscribers:
                try:
                    subject = f'Новая статья в категории {category.name}'
                    message = f'Здравствуй, {subscriber.username}. Новая статья в твоём любимом разделе!'
                    html_message = render_to_string('news/email_notification.html', {
                        'username': subscriber.username,
                        'post_title': self.title,
                        'post_preview': self.preview(),
                        'category_name': category.name,
                        'post_url': f"{settings.SITE_URL}/news/{self.id}/"
                    })
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[subscriber.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    print(f"Уведомление отправлено {subscriber.email}")
                except Exception as e:
                    print(f"Ошибка отправки уведомления для {subscriber.email}: {e}")


class PostCategory(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.post.title} - {self.category.name}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(default=0)

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"


class ActivationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    activated = models.BooleanField(default=False)

    def is_expired(self):
        expiration_days = 7  # Срок действия токена
        return timezone.now() > self.created_at + timedelta(days=expiration_days)

    @classmethod
    def create_token(cls, user):
        token = get_random_string(64)
        return cls.objects.create(user=user, token=token)

    def __str__(self):
        return f"Token for {self.user.username} - {'Activated' if self.activated else 'Pending'}"