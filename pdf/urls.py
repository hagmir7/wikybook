from django.urls import path
from .views import *
from pdf.sites.zpdf import zpdf
from pdf.sites.dpdf import dpdf
from pdf.sites.pdfjatt import pdfjatt
from pdf.sites.archive import archive


urlpatterns = [
    path("upload", upload, name="upload"),
    path("book/create", book_create, name="book_create"),
    path("", index, name="index"),
    path("book/<str:slug>", show_book, name="show_book"),
    path("blogs", blogs, name="blogs"),
    path("books", books, name="books"),
    path("authors", authors, name="authors"),
    path("author/<str:slug>/books", show_author, name="show_author"),
    # Scraping
    path("zpdf", zpdf, name="zpdf"),
    path("dpdf", dpdf, name="dpdf"),
    path("pdfjatt", pdfjatt, name="pdfjatt"),
    path("archive", archive, name="archive"),
]
