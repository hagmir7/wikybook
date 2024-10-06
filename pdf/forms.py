from django import forms
from django_summernote.widgets import SummernoteWidget
from .models import Book, Post, Author, Contact
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


    def clean_title(self):
        title = self.cleaned_data.get("title")
        if self.instance.pk:
            if Post.objects.filter(title=title).exclude(pk=self.instance.pk).exists():
                raise ValidationError("Post with this title already exists.")
        else:
            if Post.objects.filter(title=title).exists():
                raise ValidationError("Post with this title already exists.")

        return title


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
        name = self.cleaned_data.get("name")
        if self.instance.pk:
            if Book.objects.filter(name=name).exclude(pk=self.instance.pk).exists():
                raise ValidationError("Book with this name already exists.")
        else:
            if Book.objects.filter(name=name).exists():
                raise ValidationError("Book with this name already exists.")

        return name


class AuthorForm(forms.ModelForm):
    description = forms.CharField(widget=SummernoteWidget())

    class Meta:
        model = Author
        fields = ["full_name", "image", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": "form-control"})

    def clean_full_name(self):
        full_name = self.cleaned_data.get("full_name")
        if Author.objects.filter(full_name=full_name).exists():
            raise ValidationError("Author with this full name is already exists.")
        return full_name


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ["name", "email", "subject", "body"]
