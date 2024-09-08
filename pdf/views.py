# views.py
import fitz  # PyMuPDF
from .forms import BookForm
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import (
    Http404,
    HttpResponseRedirect,
    JsonResponse,
    HttpResponse,
    HttpResponseBadRequest,
)


def index(request):
    books = Book.objects.all().order_by("-created_at")[0:50]
    authors = Author.objects.all().order_by("-created_at")[0:50]
    context = {"books": books, "authors": authors}
    return render(request, "index.html", context)


def blogs(request):
    posts_list = Post.objects.all().order_by("-created_at")
    paginator = Paginator(posts_list, 50)
    page_number = request.GET.get("page")
    posts = paginator.get_page(page_number)
    context = {"posts": posts, "title": "Weky Books: Your Guide to Book Summaries"}
    return render(request, "blogs/list.html", context)


def show_blog(request, slug):
    post = get_object_or_404(Post, slug=slug)
    context = {
        "post": post,
        "title": post.title,
        "image" : post.image,
        "description" : post.description,
        "keyword" : post.tags

    }
    return render(request, "blogs/show.html", context)


def books(request):
    books_list = Book.objects.all().order_by("-created_at")
    paginator = Paginator(books_list, 60)
    page_number = request.GET.get("page")
    books = paginator.get_page(page_number)
    context = {"books": books, "title": "Weky Books: Find Your Favorite Books"}
    return render(request, "books/list.html", context)


def show_book(request, slug):
    book = get_object_or_404(Book, slug=slug)
    books = Book.objects.filter(category=book.category).order_by("created_at")
    context = {
        "book": book,
        "books": books,
        "title": book.name,
        "description": book.description,
        "keywords": book.tags,
        "image": book.image.url if book.image else False,
    }
    return render(request, "books/show.html", context)


def authors(request):
    authors_list = Author.objects.all().order_by("-created_at")
    paginator = Paginator(authors_list, 50)
    page_number = request.GET.get("page")
    authors = paginator.get_page(page_number)
    context = {"authors": authors, "title": "Book authors - Weky books "}
    return render(request, "authors/list.html", context)


def show_author(request, slug):
    author = Author.objects.get(slug=slug)
    books = Book.objects.filter(author=author).order_by('-created_at')
    context = {
        "books" : books,
        "author": author,
        "title": f"{author.full_name} - Books"
    }
    return render(request, "authors/show.html", context)


def upload(request):
    if request.method == "POST":
        if "file" not in request.FILES:
            return JsonResponse({"error": "No file uploaded."}, status=400)

        uploaded_file = request.FILES["file"]

        if uploaded_file.content_type != "application/pdf":
            return JsonResponse({"error": "File must be a PDF."}, status=400)

        # Save the file temporarily to extract metadata
        file_instance = BookForm(file=uploaded_file)
        file_instance.save()

        # Extract PDF metadata using PyMuPDF
        file_path = file_instance.file.path
        try:
            document = fitz.open(file_path)
            metadata = document.metadata
            document.close()
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

        # Return metadata information
        meta_info = {
            "Title": metadata.get("title", "Unknown"),
            "Author": metadata.get("author", "Unknown"),
            "Subject": metadata.get("subject", "Unknown"),
            "Producer": metadata.get("producer", "Unknown"),
            "Creator": metadata.get("creator", "Unknown"),
            "CreationDate": metadata.get("creationDate", "Unknown"),
        }

        return JsonResponse(
            {"message": "File uploaded successfully!", "metadata": meta_info},
            status=200,
        )

    return render(request, "upload.html")


def book_create(request):

    form = BookForm()
    if request.method == "POST":
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            return redirect("/book/create")

    context = {"form": form}
    return render(request, "books/create.html", context)


def privacy(request):
    return render(request, "privacy.html")


def contact(request):
    return render(request, "contact.html")


def about(request):
    return render(request, "about.html")


# Start Dashobard


def dashboard(request):
    users = User.objects.all().count()
    posts = Post.objects.all().count()
    books = Book.objects.all().count()
    views = Location.objects.all().count()
    context = {
        "users" : users,
        "posts" : posts,
        "views" : views,
        'books' : books
    }
    return render(request, 'dash/index.html', context)


def create_book(request):
    form = BookForm()
    if request.method == "POST":
        form = BookForm(request.POST, files=request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            if obj.save():
                messages.success(request, "Book created successfully.")

    context = {
        "form": form,
        "title": "Create Book",
    }
    return render(request, "dash/book/create.html", context)
