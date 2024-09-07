from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from django.utils import timezone
import uuid
import os
from django.utils.translation import gettext_lazy as _
from PIL import Image


def is_image(file_path):
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except (IOError, SyntaxError):
        return False


# Generate file name
def filename(instance, filename):
    if filename:
        ext = filename.split(".")[-1]  # Get the file extension
        new_filename = f"{uuid.uuid4().hex}.{ext}"
        base_path = f"{str(instance._meta.model_name).lower()}s/{ext.upper()}"
        current_date = timezone.now().strftime("%Y-%m-%d")
        file = os.path.join(base_path, current_date, new_filename)

        return file
    else:
        return None


class Location(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ip = models.CharField(max_length=100)
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    country_flag = models.CharField(max_length=300, null=True, blank=True)
    country_code = models.CharField(max_length=10, null=True, blank=True)
    browser = models.CharField(max_length=100, null=True, blank=True)
    os = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.ip


class IpModel(models.Model):
    ip = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.ip


class Language(models.Model):
    name = models.CharField(max_length=30)
    code = models.CharField(max_length=3)

    def __str__(self):
        return self.name


class Subscribe(models.Model):
    email = models.EmailField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=100, null=True, blank=True)
    catgory = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.email


class BookList(models.Model):
    name = models.CharField(max_length=300, verbose_name="Name ")
    description = models.TextField(blank=True, null=True)
    cover = models.ImageField(upload_to=filename, default="default-post.png")
    language = models.ForeignKey(Language, on_delete=models.CASCADE, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=50)
    language = models.ForeignKey(Language, on_delete=models.CASCADE, blank=True, null=True)
    slug = models.SlugField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.slug == None:
            self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Author(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=100)
    image = models.ImageField(_("Image"), upload_to=filename, null=True, blank=True)
    description = models.TextField(_("Description"), null=True, blank=True)
    slug = models.SlugField(blank=True, null=True, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.slug == None:
            self.slug = slugify(self.full_name)
        super(Author, self).save(*args, **kwargs)

    def __str__(self):
        return self.full_name


class BookManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(removed=None)


class Book(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    title = models.CharField(max_length=150, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="books", null=True, blank=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    language = models.ForeignKey(Language, on_delete=models.CASCADE, blank=True, null=True,)

    pages = models.IntegerField(null=True, blank=True)
    size = models.CharField(null=True, blank=True, max_length=100)
    type = models.CharField(max_length=30, null=True, blank=True)
    isbn = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to=filename, null=True, blank=True)
    description = models.TextField(null=True, blank=True, verbose_name=_("Description"))
    body = models.TextField(verbose_name="Body", null=True, blank=True)
    tags = models.CharField(max_length=500, null=True, blank=True)
    views = models.ManyToManyField("Location", through="BookView")
    file = models.FileField(upload_to=filename, null=True, blank=True, verbose_name=_("File"))
    status = models.BooleanField(default=True, null=True, blank=True)
    slug = models.SlugField(blank=True, null=True, editable=False, unique=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    removed = models.DateField(null=True, blank=True)

    def get_absolute_url(self, *args, **kwargs):
        return f"/{self.language.code}/book/{self.slug}"

    class Meta:
        ordering = ["-created_at"]

    def remove(self):
        self.removed = timezone.now()
        self.save()

    # def __str__(self):
    #     return self.name

    def next(self):
        return self.get_next_by_created_at()

    def pre(self):
        return self.get_previous_by_created_at()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BookView(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    view = models.ForeignKey(Location, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class CommentBook(models.Model):
    book = models.ForeignKey(Book, related_name="comments_book", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    body = models.TextField()
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        name = self.name
        post = self.post
        return f"{name} Comment at {post}"

    class Meta:
        ordering = ("-date",)


# Contact
class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    body = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    title = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="post_images", null=True, blank=True)
    description = models.TextField()
    tags = models.CharField(max_length=150, null=True, blank=True)
    body = models.TextField()
    slug = models.SlugField(max_length=300, null=True, blank=True, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    removed = models.DateField(null=True, blank=True)

    def get_absolute_url(self, *args, **kwargs):
        return f"/p/{self.slug}"

    class Meta:
        ordering = ["-created_at"]

    def remove(self):
        self.removed = timezone.now()
        self.save()

    def __str__(self):
        return self.title

    def next(self):
        return self.get_next_by_created_at()

    def pre(self):
        return self.get_previous_by_created_at()

    def save(self, *args, **kwargs):
        if self.slug == None:
            self.slug = slugify(self.title)
        super(Post, self).save(*args, **kwargs)
