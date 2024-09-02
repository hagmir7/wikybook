import os
import fitz  # PyMuPDF
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Book
from django.conf import settings


@receiver(post_save, sender=Book)
def save_book(sender, instance, **kwargs):

    if instance.file and not instance.pages:
        instance.type = "PDF"
        if instance.type == "PDF":
            doc = fitz.open(instance.file.path)
            instance.pages = doc.page_count
            doc.close()

        if round(instance.file.size * 1e-6, 3) >= 1:
            instance.size = str(round(instance.file.size * 1e-6, 2)) + " MB"
        else:
            instance.size = str(round(instance.file.size * 0.001, 2)) + " KB"

        instance.save()


# # Get video file size
# def get_file_size(file_path):
#     try:
#         file_size = os.path.getsize(file_path)
#         return file_size
#     except Exception as e:
#         print("Error:", str(e))
#         return None


# # Format file size
# def format_size(size_in_bytes):
#     for unit in ["B", "KB", "MB", "GB"]:
#         if size_in_bytes < 1024.0:
#             return f"{size_in_bytes:.2f} {unit}"
#         size_in_bytes /= 1024.0


# @receiver(post_save, sender=Book)
# def process_pdf(sender, instance, **kwargs):

#     if instance.file:
#         if settings.CPANEL:
#             file_path = os.path.normpath(f'/home/agha6919/freesad/{os.path.join(instance.file.url)}')
#         else:
#             file_path = os.path.normpath(f'{os.path.join(instance.file.url)}')

#         instance.size = get_file_size(file_path)

#         pdf_path = instance.file.path
#         with open(pdf_path, "rb") as pdf_file:
#             pdf_document = fitz.open(pdf_file)
#             instance.pages = pdf_document.page_count
#             instance.type = 'PDF'

#         # Save the updated instance
#         instance.save()
