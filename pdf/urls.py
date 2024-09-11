from django.urls import path
from .views import *
from pdf.sites.zpdf import zpdf
from pdf.sites.dpdf import dpdf
from pdf.sites.pdfjatt import pdfjatt
from pdf.sites.archive import archive


urlpatterns = [
    path("upload", upload, name="upload"),
    path("", index, name="index"),
    path("blogs", blogs, name="blogs"),
    path("blog/<str:slug>", show_blog, name="show_blog"),
    path("books", books, name="books"),
    path("authors", authors, name="authors"),
    path("author/<str:slug>/books", show_author, name="show_author"),
    path("privacy-policy", privacy, name="privacy"),
    path("contact", contact, name="contact"),
    path("about-us", about, name="about"),
    # Dashboard
    path("dashboard", dashboard, name="dashboard"),
    path("book/create", create_book, name="create_book"),
    path("book/update/<int:book_id>", create_book, name="update_book"),
    path("post/create/", create_post, name="create_post"),
    path("post/create/<int:id>/", create_post, name="update_post"),
    path("book/list", book_list, name="book_list"),
    path("book/<str:slug>", show_book, name="show_book"),
    path("post/list", post_list, name="post_list"),
    # Scraping
    path("zpdf", zpdf, name="zpdf"),
    path("dpdf", dpdf, name="dpdf"),
    path("pdfjatt", pdfjatt, name="pdfjatt"),
    path("archive", archive, name="archive"),
]
