from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin, PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages

from .models import Post, Author, Category, Subscription
from .filters import PostFilter
from .forms import PostForm
from .mixins import AuthRequiredMixin


class PermissionRequiredMixinWithMessage(PermissionRequiredMixin):
    permission_denied_message = "У вас недостаточно прав для доступа к этой странице."

    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect('news_list')


class AuthorRequiredMixin(UserPassesTestMixin):
    permission_denied_message = "Только авторы могут создавать и редактировать контент."

    def test_func(self):
        return self.request.user.groups.filter(name='authors').exists()

    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect('news_list')


# 🆕 Функции для работы с подписками (С ОТЛАДКОЙ)
@login_required
def subscribe_to_category(request, category_id):
    """Подписка на категорию"""
    print(f"🔔 ЗАПРОС НА ПОДПИСКУ: пользователь={request.user.username}, категория_id={category_id}")

    category = get_object_or_404(Category, id=category_id)
    print(f"📦 Найдена категория: {category.name}")

    # Проверяем существующие подписки
    existing_subscription = Subscription.objects.filter(
        user=request.user,
        category=category
    ).exists()
    print(f"📊 Подписка уже существует: {existing_subscription}")

    subscription, created = Subscription.objects.get_or_create(
        user=request.user,
        category=category
    )

    if created:
        print(f"✅ СОЗДАНА НОВАЯ ПОДПИСКА: {request.user.username} -> {category.name}")
        messages.success(request, f'✅ Вы успешно подписались на категорию "{category.name}"!')
    else:
        print(f"ℹ️ ПОДПИСКА УЖЕ СУЩЕСТВУЕТ: {request.user.username} -> {category.name}")
        messages.info(request, f'ℹ️ Вы уже подписаны на категорию "{category.name}"')

    # Проверяем общее количество подписок пользователя
    user_subscriptions_count = Subscription.objects.filter(user=request.user).count()
    print(f"📈 Всего подписок у пользователя: {user_subscriptions_count}")

    return redirect('category_posts', category_id=category_id)


@login_required
def unsubscribe_from_category(request, category_id):
    """Отписка от категории"""
    print(f"🔔 ЗАПРОС НА ОТПИСКУ: пользователь={request.user.username}, категория_id={category_id}")

    category = get_object_or_404(Category, id=category_id)
    print(f"📦 Найдена категория: {category.name}")

    # Проверяем существующие подписки перед удалением
    subscription_exists = Subscription.objects.filter(
        user=request.user,
        category=category
    ).exists()
    print(f"📊 Подписка найдена для удаления: {subscription_exists}")

    deleted_count = Subscription.objects.filter(
        user=request.user,
        category=category
    ).delete()[0]

    if deleted_count > 0:
        print(f"❌ ПОДПИСКА УДАЛЕНА: {request.user.username} -> {category.name}")
        messages.success(request, f'❌ Вы отписались от категории "{category.name}"')
    else:
        print(f"⚠️ ПОДПИСКА НЕ НАЙДЕНА: {request.user.username} -> {category.name}")
        messages.warning(request, f'⚠️ Вы не были подписаны на категорию "{category.name}"')

    # Проверяем общее количество подписок пользователя после удаления
    user_subscriptions_count = Subscription.objects.filter(user=request.user).count()
    print(f"📈 Всего подписок у пользователя после отписки: {user_subscriptions_count}")

    return redirect('category_posts', category_id=category_id)


@login_required
def my_subscriptions(request):
    """Страница с подписками пользователя"""
    print(f"🔔 ЗАПРОС МОИ ПОДПИСКИ: пользователь={request.user.username}")

    subscriptions = Subscription.objects.filter(user=request.user).select_related('category')
    print(f"📋 Найдено подписок: {subscriptions.count()}")

    for sub in subscriptions:
        print(f"   - {sub.category.name} (подписка с {sub.subscribed_at})")

    context = {
        'subscriptions': subscriptions,
        'categories': Category.objects.all()
    }
    return render(request, 'news/my_subscriptions.html', context)


def category_posts(request, category_id):
    """Страница с постами категории"""
    print(
        f"🔔 ЗАПРОС КАТЕГОРИЯ: категория_id={category_id}, пользователь={request.user.username if request.user.is_authenticated else 'неавторизован'}")

    category = get_object_or_404(Category, id=category_id)
    print(f"📦 Категория: {category.name}")

    posts = Post.objects.filter(categories=category).order_by('-created_at')
    print(f"📄 Постов в категории: {posts.count()}")

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    is_subscribed = False
    if request.user.is_authenticated:
        is_subscribed = Subscription.objects.filter(
            user=request.user,
            category=category
        ).exists()
        print(f"👤 Статус подписки пользователя: {is_subscribed}")
    else:
        print("👤 Пользователь не аутентифицирован")

    context = {
        'category': category,
        'page_obj': page_obj,
        'is_subscribed': is_subscribed,
        'categories': Category.objects.all()
    }
    return render(request, 'news/category_posts.html', context)


# 🆕 Функция для добавления в авторы
@login_required
def become_author(request):
    """Добавляет пользователя в группу authors"""
    print(f"🔔 ЗАПРОС СТАТЬ АВТОРОМ: пользователь={request.user.username}")

    authors_group, created = Group.objects.get_or_create(name='authors')
    print(f"📋 Группа authors: {'создана' if created else 'уже существует'}")

    content_type = ContentType.objects.get_for_model(Post)
    post_permissions = Permission.objects.filter(content_type=content_type)
    print(f"🔐 Найдено прав для модели Post: {post_permissions.count()}")

    authors_group.permissions.set(post_permissions)
    print(f"✅ Права назначены группе authors")

    if not request.user.groups.filter(name='authors').exists():
        request.user.groups.add(authors_group)
        print(f"🎉 ПОЛЬЗОВАТЕЛЬ ДОБАВЛЕН В АВТОРЫ: {request.user.username}")
        messages.success(request, 'Поздравляем! Теперь вы автор и можете создавать новости и статьи.')
    else:
        print(f"ℹ️ ПОЛЬЗОВАТЕЛЬ УЖЕ АВТОР: {request.user.username}")
        messages.info(request, 'Вы уже являетесь автором.')

    return redirect('news_list')


# 🆕 ОБНОВЛЕННЫЕ КЛАССЫ-ПРЕДСТАВЛЕНИЯ С КАТЕГОРИЯМИ
class NewsList(ListView):
    model = Post
    template_name = 'news/news_list.html'
    context_object_name = 'news_list'
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.NEWS).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        print(
            f"📰 Страница новостей: {context['news_list'].count()} новостей, {context['categories'].count()} категорий")
        return context


class NewsDetail(DetailView):
    model = Post
    template_name = 'news/news_detail.html'
    context_object_name = 'news'

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.NEWS)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()

        # Добавляем информацию о подписках пользователя
        if self.request.user.is_authenticated:
            post_categories = self.object.categories.all()
            user_subscriptions = Subscription.objects.filter(
                user=self.request.user,
                category__in=post_categories
            ).values_list('category_id', flat=True)
            context['user_subscribed_categories'] = list(user_subscriptions)
            print(f"📖 Детали новости: '{self.object.title}', подписан на категории: {len(user_subscriptions)}")
        return context


class NewsSearch(ListView):
    model = Post
    template_name = 'news/news_search.html'
    context_object_name = 'news_list'
    paginate_by = 10

    def get_queryset(self):
        queryset = Post.objects.filter(post_type=Post.NEWS).order_by('-created_at')
        self.filterset = PostFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        context['categories'] = Category.objects.all()
        print(f"🔍 Поиск новостей: найдено {context['news_list'].count()} результатов")
        return context


# 🆕 ОБНОВЛЕННЫЕ CRUD ПРЕДСТАВЛЕНИЯ
class NewsCreate(PermissionRequiredMixinWithMessage, AuthRequiredMixin, CreateView):
    form_class = PostForm
    model = Post
    template_name = 'news/news_edit.html'
    permission_required = 'news.add_post'

    def form_valid(self, form):
        post = form.save(commit=False)
        post.post_type = Post.NEWS
        author, created = Author.objects.get_or_create(user=self.request.user)
        post.author = author
        response = super().form_valid(form)

        # 🆕 Отправляем уведомления после успешного сохранения формы
        print(f"📝 Пост создан, отправляем уведомления для ID: {self.object.pk}")
        self.object.send_notifications_to_subscribers()

        return response

    def get_success_url(self):
        messages.success(self.request, 'Новость успешно создана! Подписчики получат уведомления.')
        return reverse_lazy('news_detail', kwargs={'pk': self.object.pk})


class NewsUpdate(PermissionRequiredMixinWithMessage, AuthRequiredMixin, UpdateView):
    form_class = PostForm
    model = Post
    template_name = 'news/news_edit.html'
    permission_required = 'news.change_post'

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.NEWS)

    def get_success_url(self):
        return reverse_lazy('news_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class NewsDelete(PermissionRequiredMixinWithMessage, AuthRequiredMixin, DeleteView):
    model = Post
    template_name = 'news/news_delete.html'
    success_url = reverse_lazy('news_list')
    permission_required = 'news.delete_post'

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.NEWS)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class ArticleCreate(PermissionRequiredMixinWithMessage, AuthRequiredMixin, CreateView):
    form_class = PostForm
    model = Post
    template_name = 'news/article_edit.html'
    permission_required = 'news.add_post'

    def form_valid(self, form):
        post = form.save(commit=False)
        post.post_type = Post.ARTICLE
        author, created = Author.objects.get_or_create(user=self.request.user)
        post.author = author
        response = super().form_valid(form)

        # 🆕 Отправляем уведомления после успешного сохранения формы
        print(f"📄 Статья создана, отправляем уведомления для ID: {self.object.pk}")
        self.object.send_notifications_to_subscribers()

        return response

    def get_success_url(self):
        messages.success(self.request, 'Статья успешно создана! Подписчики получат уведомления.')
        return reverse_lazy('news_detail', kwargs={'pk': self.object.pk})


class ArticleUpdate(PermissionRequiredMixinWithMessage, AuthRequiredMixin, UpdateView):
    form_class = PostForm
    model = Post
    template_name = 'news/article_edit.html'
    permission_required = 'news.change_post'

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.ARTICLE)

    def get_success_url(self):
        return reverse_lazy('news_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class ArticleDelete(PermissionRequiredMixinWithMessage, AuthRequiredMixin, DeleteView):
    model = Post
    template_name = 'news/article_delete.html'
    success_url = reverse_lazy('news_list')
    permission_required = 'news.delete_post'

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.ARTICLE)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class ActivationView(TemplateView):
    template_name = 'accounts/activation.html'

    def get(self, request, token, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        try:
            activation_token = ActivationToken.objects.get(token=token)

            if activation_token.is_expired():
                context['status'] = 'expired'
                context['message'] = 'Ссылка активации устарела. Пожалуйста, запросите новую.'
            elif activation_token.activated:
                context['status'] = 'already_activated'
                context['message'] = 'Аккаунт уже был активирован ранее.'
            else:
                # Активируем аккаунт
                activation_token.activated = True
                activation_token.save()

                # Активируем пользователя
                user = activation_token.user
                user.is_active = True
                user.save()

                context['status'] = 'success'
                context['message'] = 'Аккаунт успешно активирован! Теперь вы можете войти в систему.'
                context['username'] = user.username

        except ActivationToken.DoesNotExist:
            context['status'] = 'invalid'
            context['message'] = 'Неверная ссылка активации. Пожалуйста, проверьте правильность ссылки.'

        return self.render_to_response(context)


@login_required
def resend_activation_email(request):
    """
    Повторная отправка письма активации
    """
    try:
        activation_token = ActivationToken.objects.get(user=request.user)

        if activation_token.activated:
            messages.info(request, 'Ваш аккаунт уже активирован.')
        elif activation_token.is_expired():
            # Создаем новый токен
            activation_token.delete()
            new_token = ActivationToken.create_token(request.user)
            activation_url = f"{settings.SITE_URL}/accounts/activate/{new_token.token}/"
            EmailService.send_welcome_email(request.user, activation_url)
            messages.success(request, 'Новое письмо активации отправлено на ваш email.')
        else:
            # Отправляем существующий токен
            activation_url = f"{settings.SITE_URL}/accounts/activate/{activation_token.token}/"
            EmailService.send_welcome_email(request.user, activation_url)
            messages.success(request, 'Письмо активации отправлено на ваш email.')

    except ActivationToken.DoesNotExist:
        # Создаем новый токен, если по какой-то причине его нет
        new_token = ActivationToken.create_token(request.user)
        activation_url = f"{settings.SITE_URL}/accounts/activate/{new_token.token}/"
        EmailService.send_welcome_email(request.user, activation_url)
        messages.success(request, 'Письмо активации отправлено на ваш email.')

    return redirect('profile')  # или другая подходящая страница