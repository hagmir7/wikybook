from base64 import encode
from bs4 import BeautifulSoup, Comment
from django.shortcuts import render, redirect, get_object_or_404
import re
import requests
from pdf.models import Language, Book, Category, Author
from django.http import JsonResponse
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from urllib.request import urlopen
import random
import string
import time
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.translation import gettext as _
import traceback
import sys
import os
from django.conf import settings
# from freewsad.config.ask import *




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
    response = requests.get(url, headers=headers, verify=True)
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
    response = requests.get(url, headers=headers, verify=True)
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

    response = requests.get(data.get("pdf"), verify=True, headers=headers)
    if response.status_code == 200:
        response.raise_for_status()

        file_temp = NamedTemporaryFile()
        file_temp.write(response.content)
        file_temp.flush()

        if Category.objects.filter(name__icontains=data.get("category")).exists():
            category = Category.objects.filter(
                name__icontains=data.get("category")
            )[0]
        else:
            category = Category.objects.create(
                name=data.get("category"),
                language=Language.objects.get(code="en"),
            )

        author = remove_extra_spaces(str(data.get("author")))
        if Author.objects.filter(full_name__icontains=author).exists():
            author = Author.objects.filter(full_name__icontains=author)[0]
        else:
            author = Author.objects.create(full_name=author)

        if not Book.objects.filter(name__icontains=str(data.get("name"))).exists():
            book = Book.objects.create(
                name=remove_extra_spaces(str(data.get("name"))),
                user=User.objects.get(id=1),
                author=author,
                language=Language.objects.get(code="en"),
                description=remove_extra_spaces_and_lines(str(data.get("description")))[0:300],
                body=str(data.get("body")),
                tags=str(data.get("tags")),
                category=category,
                isbn=str(data.get("isbn")),
            )
            download_image(data.get("image"), book.id)
            download_file(data.get("pdf"), book.id)
    else:
        print("Error Download file")


def get_item(url):
    response = requests.get(url, verify=True, headers=headers)
    if response.status_code == 200:
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table", {"class": "table is-fullwidth"}).find_all("td")
        name = table[0].text
        if not Book.objects.filter(name__icontains=name).exists():
            author = table[1].text
            tags = table[2].find_all("a", {"class": "dotted"})
            category = tags[0].text
            tags_string = ""
            image_url = soup.find("img", {"itemprop": "image"})["src"]
            file_url = soup.find("a", {"rel": "nofollow"})["href"]

            content = soup.find("div", {"class": "content"}).text
            description = soup.find("div", {"class": "content"}).text

            for tag in tags:
                tags_string += tag.text + ","

            isbn = table[4].text

            data = {
                "image": image_url,
                "name": name,
                "category": category,
                "author": author,
                "language": "en",
                "description": description,
                "pdf": file_url,
                "tags": tags_string,
                "body": content,
                "isbn": isbn,
            }
            page_download(data)
            print("Book Create successfully ==>", name)
        else:
            print("Book already exists")
    else:
        print("Request Error")


# Max 12019 - 17 - 05 - 2024
def pdfjatt(request):
    page_url = f"https://pdfjatt.com/"
    response = requests.get(page_url, verify=True, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    categoris = soup.find("div", {"class", "buttons"}).find_all("a")
    for category in categoris:
        url = "https://pdfjatt.com" + str(category["href"])
        response = requests.get(url, verify=True, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        cards = soup.find_all("h5", {"class": "mb-1"})
        for card in cards:
            url = "https://pdfjatt.com" + card.find("a")["href"]
            print(url)
            try:
                get_item(url)
            except Exception as e:
                print(e)

    return JsonResponse({"message": "Scraped Successfully..."})
