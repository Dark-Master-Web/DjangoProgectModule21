from django.shortcuts import render, get_object_or_404
from .models import Post

def news_list(request):
    """Список всех новостей (только тип 'NW')"""
    news = Post.objects.filter(post_type=Post.NEWS).order_by('-created_at')
    return render(request, 'news/news_list.html', {'news_list': news})

def news_detail(request, news_id):
    """Детальная страница новости"""
    news_item = get_object_or_404(Post, id=news_id, post_type=Post.NEWS)
    return render(request, 'news/news_detail.html', {'news': news_item})
