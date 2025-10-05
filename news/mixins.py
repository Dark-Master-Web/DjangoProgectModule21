from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages


class AuthRequiredMixin(LoginRequiredMixin):
    """Миксин для проверки аутентификации пользователя"""
    login_url = '/accounts/login/'  # Используем allauth URL

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Для доступа к этой странице необходимо войти в систему.')
            return redirect(self.login_url)
        return super().dispatch(request, *args, **kwargs)


from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect


class PermissionRequiredMixinWithMessage(PermissionRequiredMixin):
    """Миксин для проверки прав с пользовательскими сообщениями"""
    permission_denied_message = "У вас недостаточно прав для доступа к этой странице."

    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect('news_list')