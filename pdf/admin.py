from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import *
from django.utils.translation import gettext_lazy as _
from import_export import resources


from django_summernote.admin import SummernoteModelAdmin


class BookResource(resources.ModelResource):

    def export(self, queryset=None, *args, **kwargs):
        # Get the dataset
        dataset = super().export(queryset, *args, **kwargs)

        # Convert NULL values to 0 for 'pages' column
        for row in dataset.dict:
            # Ensure only 'pages' column is modified
            if "pages" in row and row["pages"] is None:
                row["pages"] = 0

        return dataset


admin.site.site_header = _("FacePY Admin Panel")
admin.site.site_title = _("FacePY")
# admin.site.index_title = _("Welcome to Your Custom Admin Site")


class BookModelAdmin(ImportExportModelAdmin, SummernoteModelAdmin):
    list_display = ("name", "author", "category")
    search_fields = ("name", "title", 'id')
    list_filter = ("category",)
    resource_class = BookResource


@admin.register(Book)
class BookAdmin(BookModelAdmin):
    pass


class CategoryModelAdmin(ImportExportModelAdmin):
    search_fields = ["name", "id"]
    list_display = ('name', 'language')
    list_filter = ("language",)


@admin.register(Category)
class CategoryImportExport(CategoryModelAdmin):
    pass


@admin.register(Post)
class PostImportExport(ImportExportModelAdmin):
    pass


@admin.register(Contact)
class ContactImportExport(ImportExportModelAdmin):
    pass


@admin.register(Language)
class LanguageImportExport(ImportExportModelAdmin):
    pass


@admin.register(Author)
class AuthorImportExport(ImportExportModelAdmin):
    pass


@admin.register(Subscribe)
class SubscribeImportExport(ImportExportModelAdmin):
    pass


admin.site.register(Location)
admin.site.register(BookList)

admin.site.register(BookView)
admin.site.register(CommentBook)
