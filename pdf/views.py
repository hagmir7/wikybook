# views.py
from django.http import JsonResponse
import fitz  # PyMuPDF
from .forms import BookForm
from django.shortcuts import render, redirect, get_object_or_404
from .models import *


def index(request):
    books = Book.objects.all().order_by('-created_at')[0:50]
    context = {"books" : books}
    return render(request, "index.html", context)


def show_book(request, slug):
    book = get_object_or_404(Book, slug=slug)
    context = {
        "book" : book
    }
    return render(request, 'books/show.html', context)

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

    return render(request, 'upload.html')


def book_create(request):

    form = BookForm()
    if request.method == "POST":
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            return redirect('/book/create')

    context = {
        "form" : form
    }
    return render(request, "books/create.html", context)
