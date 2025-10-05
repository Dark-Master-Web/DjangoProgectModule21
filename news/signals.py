from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from allauth.account.signals import user_signed_up

@receiver(user_signed_up)
def add_user_to_common_group(sender, request, user, **kwargs):
    """Добавляет пользователя в группу common при регистрации"""
    common_group, created = Group.objects.get_or_create(name='common')
    user.groups.add(common_group)
    user.save()
    print(f"Пользователь {user.email} добавлен в группу common")