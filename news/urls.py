from django.urls import path
from . import views

urlpatterns = [
    path('news/', views.NewsList.as_view(), name='news_list'),
    path('news/<int:pk>/', views.NewsDetail.as_view(), name='news_detail'),
    path('news/search/', views.NewsSearch.as_view(), name='news_search'),
    path('news/create/', views.NewsCreate.as_view(), name='news_create'),
    path('news/<int:pk>/edit/', views.NewsUpdate.as_view(), name='news_edit'),
    path('news/<int:pk>/delete/', views.NewsDelete.as_view(), name='news_delete'),
    path('articles/create/', views.ArticleCreate.as_view(), name='article_create'),
    path('articles/<int:pk>/edit/', views.ArticleUpdate.as_view(), name='article_edit'),
    path('articles/<int:pk>/delete/', views.ArticleDelete.as_view(), name='article_delete'),
    path('become-author/', views.become_author, name='become_author'),

]