from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Author, Category, Post, Comment, Subscription, ActivationToken, PostCategory


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['user', 'rating']
    search_fields = ['user__username', 'user__email']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'subscribers_count']
    search_fields = ['name']

    def subscribers_count(self, obj):
        return obj.subscribers.count()

    subscribers_count.short_description = 'Кол-во подписчиков'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'subscribed_at']
    list_filter = ['category', 'subscribed_at']
    search_fields = ['user__username', 'category__name']
    date_hierarchy = 'subscribed_at'


class PostCategoryInline(admin.TabularInline):
    model = PostCategory
    extra = 1


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'post_type', 'author', 'created_at', 'rating', 'categories_list']
    list_filter = ['post_type', 'created_at', 'categories']
    search_fields = ['title', 'content']
    inlines = [PostCategoryInline]
    readonly_fields = ['created_at']
    actions = ['send_notifications_action']

    def categories_list(self, obj):
        return ", ".join([category.name for category in obj.categories.all()])

    categories_list.short_description = 'Категории'

    def save_model(self, request, obj, form, change):
        """
        Переопределяем сохранение модели в админке
        """
        print(f"🔄 Сохранение поста в админке: {obj.title}, изменение: {change}")
        super().save_model(request, obj, form, change)

        # 🆕 Для новых постов запускаем проверку категорий после полного сохранения
        if not change:
            print(f"🎯 Новый пост создан через админку, запускаем отложенную проверку...")
            self._schedule_notification_check(obj)

    def _schedule_notification_check(self, post):
        """
        Планирует проверку категорий и отправку уведомлений
        """
        import threading
        import time

        def check_categories_and_notify():
            # Ждем немного чтобы связи ManyToMany успели создаться
            time.sleep(2)

            try:
                # Перезагружаем пост с актуальными данными
                refreshed_post = Post.objects.get(pk=post.pk)
                categories = refreshed_post.categories.all()

                print(f"📂 Проверка категорий для поста '{refreshed_post.title}': {categories.count()} категорий")

                if categories:
                    print(f"🚀 Найдены категории, отправляем уведомления...")
                    refreshed_post.send_notifications_to_subscribers()
                else:
                    print("⚠️ Категории все еще не найдены")

            except Exception as e:
                print(f"❌ Ошибка при проверке категорий: {e}")

        # Запускаем в отдельном потоке
        thread = threading.Thread(target=check_categories_and_notify)
        thread.daemon = True
        thread.start()

    def send_notifications_action(self, request, queryset):
        """
        Действие для ручной отправки уведомлений для выбранных постов
        """
        for post in queryset:
            print(f"📧 Ручная отправка уведомлений для поста: {post.title}")
            categories = post.categories.all()

            if categories:
                try:
                    post.send_notifications_to_subscribers()
                    self.message_user(request, f"✅ Уведомления отправлены для '{post.title}'")
                except Exception as e:
                    self.message_user(request, f"❌ Ошибка для '{post.title}': {e}", level='ERROR')
            else:
                self.message_user(request, f"⚠️ У поста '{post.title}' нет категорий", level='WARNING')

    send_notifications_action.short_description = "📧 Отправить уведомления подписчикам"

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at', 'rating']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__title', 'text']


# 🆕 Inline для отображения подписок в админке пользователей
class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 1
    verbose_name = 'Подписка'
    verbose_name_plural = 'Подписки пользователя'


# 🆕 Inline для отображения подписок в админке категорий
class CategorySubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 1
    verbose_name = 'Подписчик'
    verbose_name_plural = 'Подписчики категории'


# Расширяем стандартную админку категорий
class CustomCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'subscribers_count']
    search_fields = ['name']
    inlines = [CategorySubscriptionInline]

    def subscribers_count(self, obj):
        return obj.subscribers.count()

    subscribers_count.short_description = 'Кол-во подписчиков'


# Расширяем стандартную админку пользователей
class CustomUserAdmin(UserAdmin):
    inlines = [SubscriptionInline]


# Перерегистрируем с улучшенными админками
admin.site.unregister(Category)
admin.site.register(Category, CustomCategoryAdmin)

# Опционально: раскомментировать если хотите видеть подписки в админке пользователей
# admin.site.unregister(User)
# admin.site.register(User, CustomUserAdmin)

@admin.register(ActivationToken)
class ActivationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'created_at', 'activated', 'is_expired']
    list_filter = ['activated', 'created_at']
    search_fields = ['user__username', 'token']
    readonly_fields = ['created_at']

    def is_expired(self, obj):
        return obj.is_expired()

    is_expired.boolean = True
    is_expired.short_description = 'Истек'