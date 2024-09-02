from base64 import encode
from bs4 import BeautifulSoup, Comment
from django.shortcuts import render, redirect, get_object_or_404
import re
import requests
from pdf.models import Post, Language, Category, Book, Author
from django.http import JsonResponse
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from urllib.request import urlopen
import random
import string
import time
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
import sys


remove_str = ["Free PDF Download", "Free ePub Download", "Download", "PDF", "Free"]

def clean_str(text):
    for item in remove_str:
        text = text.replace(item, "")
    return text


def slug(length=8):
    characters = string.ascii_lowercase + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def remove_spaces_and_lines(string):
    return "".join(string.split()).replace("\n", "")


def remove_extra_spaces_and_lines(text):
    # Split the text into lines
    lines = text.split("\n")
    # Remove empty lines and leading/trailing whitespaces
    lines = [line.strip() for line in lines if line.strip()]
    # Join the lines with a single space
    cleaned_text = " ".join(lines)
    return cleaned_text


def delete_word(sentence, word):
    return sentence.replace(word, "")


def remove_extra_spaces(string):
    return " ".join(string.split())


def remove_hashtags(string):
    pattern = r"\#\d+(\.\d+)?|\(\d+(\.\d+)?\)"
    return re.sub(pattern, "", string)


headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
}


def download_image(url, id):
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        response.raise_for_status()

        file_temp = NamedTemporaryFile()
        file_temp.write(response.content)
        file_temp.flush()

        book = Book.objects.get(id=id)
        with open(file_temp.name, "rb") as file:
            book.image.save("image.png", File(file))
            print("File saved successfully.")
    else:
        print("Failed to download the file. =>", response.text)


def download_file(url, id):
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        response.raise_for_status()

        file_temp = NamedTemporaryFile()
        file_temp.write(response.content)
        file_temp.flush()

        book = Book.objects.get(id=id)
        with open(file_temp.name, "rb") as file:
            book.file.save("file.pdf", File(file))
            print("File saved successfully.")
    else:
        print("Failed to download the file. =>", response.text)


def page_download(data):
    if Category.objects.filter(name__icontains=data.get("category")).exists():
        category = Category.objects.filter(
            name__icontains=data.get("category")
        )[0]
    else:
        category = Category.objects.create(
            name=data.get("category"),
            language=Language.objects.get(code="en"),
        )

    if Author.objects.filter(full_name__icontains=data.get("author")).exists():
        author = Author.objects.filter(full_name__icontains=data.get("author"))[0]
    else:
        author = Author.objects.create(full_name=data.get("author"))

    if not Book.objects.filter(name__icontains=data.get("name")):
        book = Book.objects.create(
            name=remove_extra_spaces(str(data.get("name"))),
            user=User.objects.get(id=1),
            author=author,
            language=Language.objects.get(code="en"),
            description=remove_extra_spaces_and_lines(str(data.get("body").text)),
            body=str(data.get("body")),
            tags=str(data.get("tags")),
            category=category,
            # isbn=data.get("isbn"),
        )
        download_image(data.get("image"), book.id)


def archive(request):
    for page in range(1, 46071, 1):
        url = f"https://archive.bookfrom.net/allbooks/page/{page}/"
        response = requests.get(url, verify=True, headers=headers)
        try:
            if response.status_code == 200:
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")
                books = soup.find_all("div", {"class": "text"})
                for book in books:
                    image_url = (
                        book.find("a", {"class": "highslide"})["href"]
                        if book.find("a", {"class": "highslide"})
                        else None
                    )
                    name = (
                        book.find("h2", {"class": "title"}).text
                        if book.find("h2", {"class": "title"})
                        else None
                    )
                    author = book.find("h4").text if book.find("h4") else None
                    category = (
                        remove_extra_spaces(str(book.find_all("h2")[1].text).split("/")[0])
                        if len(book.find_all("h2")) > 1
                        else None
                    )

                    tags = remove_extra_spaces(str(book.find_all("h2")[1].text).replace("/", ","))
                    body = book.find("div", {"class": "text3"})
                    if body and body.a:
                        body.a.decompose() 

                    if body and body.span:
                        body.span.decompose() 

                data = {
                    "image": image_url,
                    "name": name,
                    "category": category,
                    "author": author,
                    "language": "en",
                    "body": body,
                    "description": str(body)[0:300],
                    "tags": tags,
                    # "isbn": isbn,
                }
                page_download(data)
                print("Book Create successfully ==>", name)
        except Exception as e:
            print("An error occurred ==> ", e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            filename = exc_tb.tb_frame.f_code.co_filename
            line_num = exc_tb.tb_lineno
            print("File:", filename)
            print("Line:", line_num)
            print(url)

    return JsonResponse({"message": "Scraped Successfully..."})
