from django.contrib import admin
from .models import Author, Category, Post, PostCategory, Comment

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['user', 'rating']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']

class PostCategoryInline(admin.TabularInline):
    model = PostCategory
    extra = 1

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'post_type', 'author', 'created_at', 'rating']
    list_filter = ['post_type', 'created_at', 'categories']
    search_fields = ['title', 'content']
    inlines = [PostCategoryInline]

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at', 'rating']
    list_filter = ['created_at']
