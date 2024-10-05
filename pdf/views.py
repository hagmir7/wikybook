# views.py
import fitz  # PyMuPDF
from .forms import *
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from .tasks import check_website_status
from django.http import (
    Http404,
    HttpResponseRedirect,
    JsonResponse,
    HttpResponse,
    HttpResponseBadRequest,
)

import openai
import os


from django.conf import settings
import json

def getSite():
    with open(settings.BASE_DIR / "site.json", 'r') as file:
        return json.load(file)


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


    title = getSite()['title']
    context = {"posts": posts, "title": title}
    return render(request, "blogs/list.html", context)


def delete_blog(request, id):
    post = get_object_or_404(Post, id=id)
    post.delete()
    messages.success(request, "Post deleted successfully")
    return redirect(request.META.get("HTTP_REFERER", "/"))

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
    context = {"books": books, "title": getSite()["books_title"]}
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
    context = {"authors": authors, "title": f"Book authors - {getSite()['name']} "}
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


def book_list(request):
    books_list = Book.objects.all().order_by("-created_at")
    paginator = Paginator(books_list, 60)
    page_number = request.GET.get("page")
    books = paginator.get_page(page_number)
    context = {"books": books, "title": getSite()["title"]}
    return render(request, "dash/book/list.html", context)


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


def categories(request):
    category_list = Category.objects.all()
    paginator = Paginator(category_list, 60)
    page_number = request.GET.get('page')
    categories = paginator.get_page(page_number)

    context = {
        "title" : getSite()['title'],
        'categories' : categories
    }
    return render(request, "category/list.html", context)


def category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    books_list = Book.objects.filter(category__name=category.name)
    paginator = Paginator(books_list, 30)
    page_number = request.GET.get("page")
    books = paginator.get_page(page_number)
    context = {
        "title": f"{category.name} - books",
        "category": category,
        "books" : books
    }
    return render(request, "category/show.html", context)


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


def create_book(request, book_id=None):
    if book_id:
        book = get_object_or_404(Book, id=book_id, user=request.user)
        form = BookForm(instance=book)
        title = f"Update {book.name}"
    else:
        book = None
        form = BookForm()
        title = "Create Book"

    if request.method == "POST":
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            action = "updated" if book_id else "created"
            if(book_id):
                book.verified = True
                book.save()
            messages.success(request, f"Book {action} successfully.")
            return redirect(reverse('update_book', kwargs={'book_id': obj.id}))

    context = {
        "form": form,
        "title": title,
        "book" : book
    }
    return render(request, "dash/book/create.html", context)


def create_post(request, id=None):
    if id:
        post = get_object_or_404(Post, id=id)
        form = PostForm(instance=post)
        title = "Update post"
    else:
        post = None
        form = PostForm()
        title = "Create post"

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            obj = form.save(commit=False)
            if not id:
                obj.user = request.user
            obj.save()
            action = "updated" if id else "created"
            messages.success(request, f"post {action} successfully.")
            return redirect(reverse("update_post", kwargs={"id": obj.id}))

    context = {
        "form": form,
        "title": title,
    }
    return render(request, "dash/post/create.html", context)


def post_list(request):
    posts_list = Post.objects.all().order_by("-created_at")
    paginator = Paginator(posts_list, 60)
    page_number = request.GET.get("page")
    posts = paginator.get_page(page_number)
    context = {"posts": posts, "title": f"Blog list - {getSite()['name']}"}
    return render(request, "dash/post/list.html", context)


def scrap(request):
    return render(request, "scrap.html")


def home(request):
    return render(request, "home.html")


def create_author(request):
    form = AuthorForm()
    if request.method == "POST":
        form = AuthorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Author Created successfully")
            return redirect("authors")
    context = {"form": form, "title": f"Create new author"}
    return render(request, 'dash/author/create.html', context)


def update_author(request, slug):
    author = get_object_or_404(Author, slug=slug)
    if request.method == "POST":
        form = AuthorForm(request.POST, request.FILES, instance=author)
        if form.is_valid():
            form.save()
            messages.success(request, "Author updated successfully")
            return redirect("authors")
    else:
        form = AuthorForm(instance=author)

    context = {"form": form, "title": f"Update {author.full_name}", "author": author}
    return render(request, "dash/author/create.html", context)


def list_author(request):
    authors_list = Author.objects.all().order_by("-created_at")
    paginator = Paginator(authors_list, 30)
    page_number = request.GET.get("page")
    authors = paginator.get_page(page_number)
    context = {"authors": authors, "title": f"Authors list"}
    return render(request, "dash/author/list.html", context)


def rename_books(request):
    books = Book.objects.filter(name__icontains=" by ")
    for book in books:
        name = str(book.name).lower().split(" by ")[0].title()
        book.name = name
        book.save()
    return redirect('/')

openai.api_key = os.getenv("AI_KEY")


import json
import markdown


def post_content_ai(book):
    prompt = f"""Summarize the book '{book.name}' by {book.author}. 
            Please follow these guidelines:
            1. Use Markdown format.
            2. Use proper heading hierarchy (H2, H3, H4) for different sections, don't add (h1) title to the summary .
            3. Use **bold** for important words or phrases.
            4. Include a brief introduction, main themes, key points, and a conclusion.
            5. Aim for a comprehensive yet concise summary.
            6. Ensure the content is SEO-friendly with relevant keywords.
            7. Content must be long more than 13000 letters
            Please don't make mstiks return just a result no anothor text
        """
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes books.",
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content


def post_meta_keywords(name):
    prompt = f"Give me meta keywords for this book {name}, and return just result by comma , and less than 150 charactor"
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that get books. book infos",
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content


def post_meta_description(name):
    prompt = f"Give me meta description for this book {name}, and return just result"
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that get books. book infos",
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content


def generate_post(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    title = f"{book.name} by {book.author.full_name}"
    post = Post.objects.create(
        title=f"{title} - Book Summary",
        body=markdown.markdown(post_content_ai(book)),
        user=User.objects.get(id=1),
        category=book.category,
        description=post_meta_description(title),
        tags=str(post_meta_keywords(title))[0:150],
    )

    return redirect("show_blog", post.slug)
