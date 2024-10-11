from django.contrib.sitemaps import Sitemap
from .models import Book, Post, Category, Author


class BookSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Book.objects.all()

    def lastmod(self, obj):
        return obj.created_at


class PostSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Post.objects.all()

    def lastmod(self, obj):
        return obj.uploaded_at


class AuthorSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Author.objects.all()

    def lastmod(self, obj):
        return obj.uploaded_at


class CategorySitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Category.objects.all()

    def lastmod(self, obj):
        return obj.uploaded_at
