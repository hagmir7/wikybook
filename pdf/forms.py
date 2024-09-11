from django import forms
from django_summernote.widgets import SummernoteWidget
from .models import Book, Post
from django.core.exceptions import ValidationError
import os


class PostForm(forms.ModelForm):
    body = forms.CharField(widget=SummernoteWidget())

    class Meta:
        model = Post
        fields = ["title", "image", "tags", "category", "description", "body"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": "form-control"})


class BookForm(forms.ModelForm):
    body = forms.CharField(widget=SummernoteWidget())

    class Meta:
        model = Book
        fields = [
            "name", "author", "category",
            "language", "image", "description",
            "body", "tags",  "file",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": "form-control"})
        self.fields["description"].widget.attrs.update({"rows": 4})
        self.fields["body"].widget.attrs.update({"rows": 6})


    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            allowed_extensions = [".txt", ".pdf", ".epub"]
            file_extension = os.path.splitext(file.name)[1]
            if file_extension.lower() not in allowed_extensions:
                raise ValidationError("Invalid file type. Only .txt, .pdf and .epub files are allowed.")
        return file


    def clean_name(self):
        name = self.cleaned_data.get('name')
        if Book.objects.filter(name=name).exists():
            raise ValidationError("Book with this name is already exists.")
        return name
