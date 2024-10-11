from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


from django.contrib.sitemaps import GenericSitemap

# from video.sitemaps import PlayListSitemap, MovieSitemap
from django.contrib.sitemaps import views as sitemaps_views
from pdf.models import Book, Author, Category, Post


class PaginatedSitemap(GenericSitemap):
    limit = 1000


sitemap = {
    "books": PaginatedSitemap(
        {"queryset": Book.objects.all().order_by("id")},
        priority=1.0,
        changefreq="daily",
    ),
    "authors": PaginatedSitemap(
        {"queryset": Author.objects.all().order_by("id")},
        priority=1.0,
        changefreq="daily",
    ),
    "categories": PaginatedSitemap(
        {"queryset": Category.objects.all().order_by("id")},
        priority=1.0,
        changefreq="daily",
    ),
    "posts": PaginatedSitemap(
        {"queryset": Post.objects.all().order_by("id")},
        priority=1.0,
        changefreq="daily",
    ),
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("pdf.urls")),
    path("summernote/", include("django_summernote.urls")),
      path('sitemap.xml', sitemaps_views.index, {'sitemaps': sitemap}, name='django.contrib.sitemaps.views.sitemap'),
    path('sitemap-<section>.xml', sitemaps_views.sitemap, {'sitemaps': sitemap}, name='django.contrib.sitemaps.views.sitemap'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
