from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)

    def update_rating(self):
        post_rating = self.post_set.aggregate(post_rating_sum=Sum('rating'))['post_rating_sum'] or 0
        post_rating *= 3

        comment_rating = self.user.comment_set.aggregate(comment_rating_sum=Sum('rating'))['comment_rating_sum'] or 0

        from .models import Comment
        post_comment_rating = Comment.objects.filter(post__author=self).aggregate(
            post_comment_rating_sum=Sum('rating')
        )['post_comment_rating_sum'] or 0

        self.rating = post_rating + comment_rating + post_comment_rating
        self.save()

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

    class Meta:
        unique_together = ('user', 'category')

    def __str__(self):
        return f'{self.user.username} - {self.category.name}'


class Post(models.Model):
    ARTICLE = 'AR'
    NEWS = 'NW'
    POST_TYPES = [
        (ARTICLE, 'Статья'),
        (NEWS, 'Новость'),
    ]

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    post_type = models.CharField(max_length=2, choices=POST_TYPES, default=ARTICLE)
    created_at = models.DateTimeField(auto_now_add=True)
    categories = models.ManyToManyField(Category, through='PostCategory')
    title = models.CharField(max_length=255)
    content = models.TextField()
    rating = models.IntegerField(default=0)

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()

    def preview(self):
        return self.content[:124] + '...' if len(self.content) > 124 else self.content

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        print(f"🔄 Сохранение поста: {self.title}, новый: {is_new}")
        super().save(*args, **kwargs)
        # 🆕 УБРАНА авто-отправка уведомлений - теперь только через сигналы

    def send_notifications_to_subscribers(self):
        """Отправляет уведомления всем подписчикам категорий поста"""
        print(f"📬 Начало отправки уведомлений для поста: '{self.title}'")

        categories = self.categories.all()
        print(f"📂 Категории поста: {[cat.name for cat in categories]}")

        if not categories:
            print("⚠️ У поста нет категорий - некому отправлять уведомления")
            return

        for category in categories:
            subscribers = category.subscribers.all()
            print(f"👥 Категория '{category.name}': {subscribers.count()} подписчиков")

            if not subscribers:
                print(f"ℹ️ В категории '{category.name}' нет подписчиков")
                continue

            for user in subscribers:
                print(f"   👤 Отправка пользователю: {user.username} ({user.email})")
                self.send_email_notification(user, category)

    def send_email_notification(self, user, category):
        """Отправляет email уведомление конкретному пользователю"""
        print(f"📧 Попытка отправки email пользователю {user.email}")

        subject = self.title

        # HTML версия письма
        html_message = render_to_string('news/email_notification.html', {
            'username': user.username,
            'post_title': self.title,
            'post_preview': self.content[:50] + '...' if len(self.content) > 50 else self.content,
            'category_name': category.name,
            'post_url': f"{settings.SITE_URL}/news/{self.id}/" if hasattr(settings, 'SITE_URL') else f"/news/{self.id}/"
        })

        # Текстовая версия письма
        message = f"""
        Здравствуй, {user.username}. Новая статья в твоём любимом разделе {category.name}!

        {self.title}
        {self.content[:50]}...

        Читать полностью: {settings.SITE_URL}/news/{self.id}/
        """

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            print(f"✅ Email успешно отправлен пользователю {user.username}")
        except Exception as e:
            print(f"❌ Ошибка отправки email пользователю {user.username}: {e}")

    def __str__(self):
        return self.title


class PostCategory(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.post.title} - {self.category.name}'


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
        return f'Comment by {self.user.username} on {self.post.title}'