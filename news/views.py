from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from .models import Post, Author
from .filters import PostFilter
from .forms import PostForm

def news_list(request):
    """Список всех новостей (только тип 'NW') - от новых к старым"""
    news = Post.objects.filter(post_type=Post.NEWS).order_by('-created_at')
    return render(request, 'news/news_list.html', {'news_list': news})

def news_detail(request, news_id):
    """Детальная страница новости"""
    news_item = get_object_or_404(Post, id=news_id, post_type=Post.NEWS)
    return render(request, 'news/news_detail.html', {'news': news_item})


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


class NewsCreate(CreateView):
    form_class = PostForm
    model = Post
    template_name = 'news/news_edit.html'

    def form_valid(self, form):
        post = form.save(commit=False)
        post.post_type = Post.NEWS
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('news_detail', kwargs={'pk': self.object.pk})


class NewsUpdate(UpdateView):
    form_class = PostForm
    model = Post
    template_name = 'news/news_edit.html'

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.NEWS)

    def get_success_url(self):
        return reverse_lazy('news_detail', kwargs={'pk': self.object.pk})


class NewsDelete(DeleteView):
    model = Post
    template_name = 'news/news_delete.html'
    success_url = reverse_lazy('news_list')

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.NEWS)


class ArticleCreate(CreateView):
    form_class = PostForm
    model = Post
    template_name = 'news/article_edit.html'

    def form_valid(self, form):
        post = form.save(commit=False)
        post.post_type = Post.ARTICLE
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('news_detail', kwargs={'pk': self.object.pk})


class ArticleUpdate(UpdateView):
    form_class = PostForm
    model = Post
    template_name = 'news/article_edit.html'

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.ARTICLE)

    def get_success_url(self):
        return reverse_lazy('news_detail', kwargs={'pk': self.object.pk})


class ArticleDelete(DeleteView):
    model = Post
    template_name = 'news/article_delete.html'
    success_url = reverse_lazy('news_list')

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.ARTICLE)