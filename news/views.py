from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin, PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages

from .models import Post, Author
from .filters import PostFilter
from .forms import PostForm
from .mixins import AuthRequiredMixin


# 🆕 Сначала определим все миксины
class PermissionRequiredMixinWithMessage(PermissionRequiredMixin):
    """Миксин для проверки прав с пользовательскими сообщениями"""
    permission_denied_message = "У вас недостаточно прав для доступа к этой странице."

    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect('news_list')


class AuthorRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки что пользователь в группе authors"""
    permission_denied_message = "Только авторы могут создавать и редактировать контент."

    def test_func(self):
        return self.request.user.groups.filter(name='authors').exists()

    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect('news_list')


# 🆕 Функция для добавления в авторы
@login_required
def become_author(request):
    """Добавляет пользователя в группу authors и назначает права"""
    authors_group, created = Group.objects.get_or_create(name='authors')

    # Получаем права для модели Post
    content_type = ContentType.objects.get_for_model(Post)
    post_permissions = Permission.objects.filter(content_type=content_type)

    # Добавляем права к группе authors
    authors_group.permissions.set(post_permissions)

    if not request.user.groups.filter(name='authors').exists():
        request.user.groups.add(authors_group)
        messages.success(request, 'Поздравляем! Теперь вы автор и можете создавать новости и статьи.')
        print(f"Пользователь {request.user.email} добавлен в группу authors с правами на Post")
    else:
        messages.info(request, 'Вы уже являетесь автором.')

    return redirect('news_list')


# Затем остальные представления
class NewsList(ListView):
    model = Post
    template_name = 'news/news_list.html'
    context_object_name = 'news_list'
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.NEWS).order_by('-created_at')


class NewsDetail(DetailView):
    model = Post
    template_name = 'news/news_detail.html'
    context_object_name = 'news'

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.NEWS)


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
        return context


# 🆕 Обновленные CRUD представления с проверкой прав
class NewsCreate(PermissionRequiredMixinWithMessage, AuthRequiredMixin, CreateView):
    form_class = PostForm
    model = Post
    template_name = 'news/news_edit.html'
    permission_required = 'news.add_post'  # Право на создание новостей

    def form_valid(self, form):
        post = form.save(commit=False)
        post.post_type = Post.NEWS
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('news_detail', kwargs={'pk': self.object.pk})


class NewsUpdate(PermissionRequiredMixinWithMessage, AuthRequiredMixin, UpdateView):
    form_class = PostForm
    model = Post
    template_name = 'news/news_edit.html'
    permission_required = 'news.change_post'  # Право на редактирование новостей

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.NEWS)

    def get_success_url(self):
        return reverse_lazy('news_detail', kwargs={'pk': self.object.pk})


class NewsDelete(PermissionRequiredMixinWithMessage, AuthRequiredMixin, DeleteView):
    model = Post
    template_name = 'news/news_delete.html'
    success_url = reverse_lazy('news_list')
    permission_required = 'news.delete_post'  # Право на удаление новостей

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.NEWS)


class ArticleCreate(PermissionRequiredMixinWithMessage, AuthRequiredMixin, CreateView):
    form_class = PostForm
    model = Post
    template_name = 'news/article_edit.html'
    permission_required = 'news.add_post'  # Право на создание статей

    def form_valid(self, form):
        post = form.save(commit=False)
        post.post_type = Post.ARTICLE
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('news_detail', kwargs={'pk': self.object.pk})


class ArticleUpdate(PermissionRequiredMixinWithMessage, AuthRequiredMixin, UpdateView):
    form_class = PostForm
    model = Post
    template_name = 'news/article_edit.html'
    permission_required = 'news.change_post'  # Право на редактирование статей

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.ARTICLE)

    def get_success_url(self):
        return reverse_lazy('news_detail', kwargs={'pk': self.object.pk})


class ArticleDelete(PermissionRequiredMixinWithMessage, AuthRequiredMixin, DeleteView):
    model = Post
    template_name = 'news/article_delete.html'
    success_url = reverse_lazy('news_list')
    permission_required = 'news.delete_post'  # Право на удаление статей

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.ARTICLE)