from bs4 import BeautifulSoup
from django.shortcuts import get_object_or_404
import requests
from pdf.models import Language, Category, Book, Author
from django.core.files import File
# from django.core.files.temp import NamedTemporaryFile
from django.contrib.auth.models import User
import json
from django.http import (
    Http404,
    HttpResponseRedirect,
    JsonResponse,
    HttpResponse,
    HttpResponseBadRequest,
)

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
}

from datetime import datetime

def date_format(string_date):
    try:
        timestamp = int(string_date) / 1000 
        readable_date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

        return readable_date
    except:
        return datetime.now


def remove_extra_spaces_and_lines(text):
    lines = text.split("\n")
    lines = [line.strip() for line in lines if line.strip()]
    cleaned_text = " ".join(lines)
    return cleaned_text


# import requests
# from django.core.files import File
# from tempfile import NamedTemporaryFile


# import requests
# from django.core.files import File
from tempfile import (
    NamedTemporaryFile,
)  # Make sure this is from Python's standard library


def download_image(url, id):
    try:
        # Get the image from the URL
        response = requests.get(url, verify=True)

        if response.status_code == 200:
            # Create a temporary file using Python's tempfile.NamedTemporaryFile
            with NamedTemporaryFile(delete=False) as file_temp:
                file_temp.write(response.content)
                file_temp.flush()  # Make sure all data is written

                # Get the Book object
                book = Book.objects.get(id=id)

                # Open the temporary file and save the image to the book
                with open(file_temp.name, "rb") as file:
                    book.image.save("image.png", File(file))

            print("File saved successfully.")
        else:
            print(f"Failed to download image. Status code: {response.status_code}")

    except Book.DoesNotExist:
        print("Book not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def page_download(data):
    if data.get("pdf"):
        print("There is a PDF ✅")
        response = requests.get(data["pdf"], verify=True, headers=headers)
        if response.status_code == 200:
            file_temp = NamedTemporaryFile(delete=False)
            file_temp.write(response.content)
            file_temp.close()
    else:
        print("There is no PDF 📕❌")

    # Check if category name is provided and not empty
    category_name = data.get("genres")[0]
    if not category_name:
        category_name = "Uncategorized"  # Default category name

    category, _ = Category.objects.get_or_create(
        name=category_name,
        defaults={
            "language": Language.objects.get(code="en"),
        },
    )

    author_name = data.get("author")
    if not author_name:
        author_name = "Unknown Author"  # Default author name

    author, _ = Author.objects.get_or_create(
        description=data.get("author_description"), full_name=author_name
    )

    # Language
    language_name = data.get("language")
    if not language_name:
        language_name = "Unknown Author"  # Default author name

    language, _ = Language.objects.get_or_create(
        code=str(language_name[0:2]).lower(), name=language_name
    )

    book_name = data.get("name")
    if not book_name:
        book_name = "Untitled Book"  # Default book name

    body_description = BeautifulSoup(data.get("description"), "html.parser")

    book, created = Book.objects.get_or_create(
        name=data.get("name"),
        defaults={
            "user": User.objects.get(id=1),
            "author": author,
            "language": language,
            "description": remove_extra_spaces_and_lines(
                str(body_description.get_text())
            )[:300],
            "isbn13": data.get("isbn13"),
            "body": str(body_description),
            "tags": ", ".join(data.get("genres")),
            "category": category,
            "isbn": data.get("isbn"),
            "publication_date": date_format(data.get("publication_date")),
            "pages" : data.get("pages")
        },
    )

    if created:
        download_image(data.get("image"), book.id)
        if data.get("pdf"):
            download_file(data.get("pdf"), book.id)


def download_file(url, id):
    response = requests.get(url, headers=headers, verify=True)
    if response.status_code == 200:
        file_temp = NamedTemporaryFile(delete=False)
        file_temp.write(response.content)
        file_temp.close()

        book = Book.objects.get(id=id)
        with open(file_temp.name, "rb") as file:
            book.file.save("file.pdf", File(file))
        print("File saved successfully.")
    else:
        print("Failed to download the file. =>", response.text)


def find_key_by_prefix(data, prefix):
    return next((k for k in data.keys() if k.startswith(prefix)), None)


def extract_book_info(json_data):
    try:
        data = json.loads(json_data)
        apollo_state = data["props"]["pageProps"]["apolloState"]

        book_key = find_key_by_prefix(apollo_state, "Book:")
        work_key = find_key_by_prefix(apollo_state, "Work:")

        if not book_key or not work_key:
            raise ValueError("Could not find Book or Work entry in the JSON data")

        book_data = apollo_state[book_key]
        work_data = apollo_state[work_key]

        author_ref = book_data["primaryContributorEdge"]["node"]
        author_id = (
            author_ref["__ref"]
            if isinstance(author_ref, dict) and "__ref" in author_ref
            else None
        )
        author_data = apollo_state.get(author_id, {}) if author_id else {}

        book_info = {
            "name": book_data.get("title"),
            "author": author_data.get("name"),
            "author_description": author_data.get("description"),
            "description": book_data.get("description"),
            "image": book_data.get("imageUrl"),
            "publication_date": book_data.get("details", {}).get("publicationTime"),
            "pages": book_data.get("details", {}).get("numPages"),
            "isbn": book_data.get("details", {}).get("isbn"),
            "isbn13": book_data.get("details", {}).get("isbn13"),
            "language": book_data.get("details", {}).get("language", {}).get("name"),
            "genres": [
                genre["genre"]["name"] for genre in book_data.get("bookGenres", [])
            ],
            "average_rating": work_data.get("stats", {}).get("averageRating"),
            "ratings_count": work_data.get("stats", {}).get("ratingsCount"),
        }

        return book_info
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def get_book(url):
    try:
        response = requests.get(url, verify=True, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        json_string = soup.find("script", {"id": "__NEXT_DATA__"}).text
        page_download(extract_book_info(json_string))
    except requests.RequestException as e:
        print(f"HTTP Request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def goodreaders(request):
    for page in range(8, 24):
        print("page => ", page)
        url = f"https://www.goodreads.com/list/show/143500.Best_Books_of_the_Decade_2020_s?page={page}/"
        response = requests.get(url, verify=True, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            table = soup.find("table", {"class": "tableList"})
            books = table.find_all("tr")
            for book in books:
                slug = book.find("a", {"itemprop": "url"})["href"]
                get_book(f"https://www.goodreads.com{slug}")
    return JsonResponse({"message": "Scraping competed successfully"})
