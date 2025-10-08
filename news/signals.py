from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from django.db import transaction
from allauth.account.signals import user_signed_up
from .models import Post


@receiver(user_signed_up)
def add_user_to_common_group(sender, request, user, **kwargs):
    """Добавляет пользователя в группу common при регистрации"""
    common_group, created = Group.objects.get_or_create(name='common')
    user.groups.add(common_group)
    user.save()
    print(f"Пользователь {user.email} добавлен в группу common")


@receiver(m2m_changed, sender=Post.categories.through)
def send_notifications_on_categories_added(sender, instance, action, **kwargs):
    """
    Отправляет уведомления когда к посту добавляются категории через ManyToMany
    """
    print(f"🎯 Сигнал ManyToMany: action={action}, пост='{instance.title}'")

    # Обрабатываем только добавление связей
    if action == "post_add":
        print(f"🚀 Категории добавлены к посту '{instance.title}'")

        # Используем transaction.on_commit чтобы убедиться, что все сохранено в БД
        transaction.on_commit(lambda: process_post_notifications(instance))


def process_post_notifications(post):
    """
    Обрабатывает отправку уведомлений после коммита транзакции
    """
    print(f"📧 Запуск отправки уведомлений для поста: '{post.title}' (ID: {post.pk})")

    try:
        # Перезагружаем пост с актуальными данными из БД
        refreshed_post = Post.objects.get(pk=post.pk)
        categories = refreshed_post.categories.all()

        print(f"📂 Категории поста после коммита: {[cat.name for cat in categories]}")
        print(f"🔢 Количество категорий: {categories.count()}")

        if categories:
            print(f"👥 Начинаем отправку уведомлений для {categories.count()} категорий...")
            # Используем существующий метод для отправки уведомлений
            refreshed_post.send_notifications_to_subscribers()
            print("✅ Уведомления успешно отправлены!")
        else:
            print("⚠️ Категории не найдены - возможно ошибка в создании связей")

    except Post.DoesNotExist:
        print(f"❌ Пост с ID {post.pk} не найден в базе данных")
    except Exception as e:
        print(f"❌ Ошибка при отправке уведомлений: {e}")


# 🆕 Дополнительный сигнал для постов созданных через админку
@receiver(post_save, sender=Post)
def check_post_categories_after_save(sender, instance, created, **kwargs):
    """
    Проверяем категории после сохранения поста (для отладки)
    """
    if created:
        print(f"🔍 Пост создан: '{instance.title}', категории: {instance.categories.count()}")