from django.urls import path
from .views import *
from pdf.sites.zpdf import zpdf
from pdf.sites.dpdf import dpdf
from pdf.sites.pdfjatt import pdfjatt
from pdf.sites.archive import archive
from pdf.sites.thegreatestbooks import thegreatestbooks

from pdf.sites.goodreaders import goodreads, one_book


urlpatterns = [
    path("upload", upload, name="upload"),
    path("", blogs, name="index"),
    path("blogs", blogs, name="blogs"),
    path("menu", menu, name="menu"),
    path("blog/<str:slug>", show_blog, name="show_blog"),
    path("blog/delete/<int:id>", delete_blog, name="delete_blog"),
    path("books", books, name="books"),
    path("authors", authors, name="authors"),
    path("author/<str:slug>/books", show_author, name="show_author"),
    path("author/update/<str:slug>", update_author, name="update_author"),
    path("author/create", create_author, name="create_author"),
    path("author/list", list_author, name="list_author"),
    path("privacy-policy", privacy, name="privacy"),
    path("contact", contact, name="contact"),
    path("about-us", about, name="about"),
    path("categories", categories, name="categories"),
    path("category/<str:slug>", category, name="category"),
    # Dashboard
    path("dashboard", dashboard, name="dashboard"),
    path("book/create", create_book, name="create_book"),
    path("book/update/<int:book_id>", create_book, name="update_book"),
    path("post/create/", create_post, name="create_post"),
    path("post/update/<int:id>/", create_post, name="update_post"),
    path("book/list", book_list, name="book_list"),
    path("book/<str:slug>", show_book, name="show_book"),
    path("post/list", post_list, name="post_list"),
    path("generate/body/body/<int:id>", book_body_generator, name="book_body_generator"),
    path("robots.txt", robots),
    # Scraping
    path("zpdf", zpdf, name="zpdf"),
    path("dpdf", dpdf, name="dpdf"),
    path("pdfjatt", pdfjatt, name="pdfjatt"),
    path("archive", archive, name="archive"),
    path("goodreads", goodreads, name="goodreads"),
    path("thegreatestbooks", thegreatestbooks, name="thegreatestbooks"),
    # scrap
    path("scrap", scrap, name="scrap"),
    path("goodreads-one-book", one_book, name="goodreads_one_book"),
    path("rename_books", rename_books),
    path("generate/post/<int:book_id>", generate_post, name="generate_post"),
]
