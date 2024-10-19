import logging
from bs4 import BeautifulSoup
from django.shortcuts import get_object_or_404, redirect
import requests
from pdf.models import Language, Category, Book, Author
from django.core.files import File
from django.contrib.auth.models import User
from django.http import JsonResponse
from datetime import datetime
from tempfile import NamedTemporaryFile
import traceback
from django.conf import settings
from requests.exceptions import RequestException
from django.core.exceptions import ObjectDoesNotExist

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
}


def date_format(year, hour=0, minute=0, second=0):
    try:
        # Check if year is None
        if year is None:
            raise ValueError("Year is None")

        # Create a datetime object with the given year and time
        date = datetime(int(year), 1, 1, hour, minute, second)

        # Format the datetime as "YYYY-MM-DD HH:MM:SS"
        formatted_date = date.strftime("%Y-%m-%d %H:%M:%S")
        return formatted_date
    except (ValueError, TypeError):
        # Handle invalid year and log or return a default value
        print(f"Invalid year provided: {year}. Using current date and time.")
        return datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )  # Format the current date and time


def remove_extra_spaces_and_lines(text):
    return " ".join(line.strip() for line in text.split("\n") if line.strip())


def download_image(url, id):
    try:
        response = requests.get(url, verify=True, headers=headers)
        if response.status_code == 200:
            with NamedTemporaryFile(delete=False) as file_temp:
                file_temp.write(response.content)
                file_temp.flush()
                book = Book.objects.get(id=id)
                with open(file_temp.name, "rb") as file:
                    book.image.save("image.png", File(file))
            print(f"Image saved successfully for book ID {id}.")
        else:
            print(
                f"Failed to download image for book ID {id}. Status code: {response.status_code}"
            )
    except Book.DoesNotExist:
        print(f"Book not found with ID {id}.")
    except Exception as e:
        print(f"An error occurred while downloading image for book ID {id}: {e}")


def process_book_data(data):
    try:
        # Get or create language
        language_name = data.get("original language", "Unknown Language")
        language_code = str(language_name[:2]).lower() if language_name else "un"
        language, _ = Language.objects.get_or_create(
            code=language_code, defaults={"name": language_name}
        )

        # Get or create category
        category_name = data.get("genres", ["Uncategorized"])[0]
        category, _ = Category.objects.get_or_create(
            name=category_name,
            defaults={"language": language},
        )

        # Get or create author
        author_name = data.get("author", "Unknown Author")
        author, _ = Author.objects.get_or_create(
            full_name=author_name
        )

        # Process book
        book_name = data.get("title", "Untitled Book")
        body_description = BeautifulSoup(data.get("description", ""), "html.parser")

        pages = data.get("pages")

        if pages is not None and "-" in pages:
            second_part = pages.split("-")[1]
        else:
            second_part = None  # Handle case when pages is None or there's no hyphen

        book, created = Book.objects.get_or_create(
            name=book_name,
            defaults={
                "user": User.objects.get(id=1),
                "author": author,
                "language": language,
                "description": remove_extra_spaces_and_lines(
                    str(body_description.get_text())
                )[:300],
                "isbn13": data.get("isbn13"),
                "body": str(body_description),
                "tags": ", ".join(data.get("genres", []))[:3],
                "category": category,
                "publication_date": date_format(int(data.get("published"))),
                "pages": second_part,
            },
        )

        if created:
            if data.get("images"):
                download_image(data["images"]["large"], book.id)
            logger.info(f"Book '{book_name}' created successfully.")
        else:
            logger.info(f"Book '{book_name}' already exists.")

    except ObjectDoesNotExist:
        print(
            f"Error: Default user (id={settings.DEFAULT_USER_ID}) does not exist."
        )
    except Exception as e:
        print(f"An error occurred while processing book data: {e}")
        print(traceback.format_exc())


def get_book(url):
    try:
        response = requests.get(url, verify=True, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        book_data = {
            "title": soup.find("h1").find("a").text.strip(),
            "author": soup.find("h1").find_all("a")[-1].text.strip(),
            "subtitle": (
                soup.find("h2", class_="sub_title").text.strip()
                if soup.find("h2", class_="sub_title")
                else ""
            ),
            "description": soup.find("p").text.strip() if soup.find("p") else "",
            "genres": [
                genre.find("a").text.strip()
                for genre in soup.find_all("h4", class_="pt-2 fs-6 text-primary ps-2")
            ],
            "images": {},
        }

        details = soup.find("dl", class_="row")
        if details:
            for dt, dd in zip(details.find_all("dt"), details.find_all("dd")):
                key = dt.text.strip().lower()
                value = dd.text.strip()
                book_data[key] = value

        large_image = soup.find("div", class_="large-book-image")
        if large_image and large_image.find("img"):
            book_data["images"]["large"] = large_image.find("img")["src"]

        default_image = soup.find("div", class_="default-book-image")
        if default_image and default_image.find("img"):
            book_data["images"]["default"] = default_image.find("img")["src"]

        return book_data
    except RequestException as e:
        print(f"Failed to fetch book data from {url}: {e}")
    except Exception as e:
        print(f"An error occurred while parsing book data from {url}: {e}")
    return None


def thegreatestbooks(request):
    books_processed = 0
    for book_id in range(5270, 22821 + 1):
        try:
            url = f"https://thegreatestbooks.org/books/{book_id}"
            book_data = get_book(url)
            process_book_data(book_data)
            books_processed += 1
        except Exception as e:
            print(f"Failed to process book {book_id}: {e}")
    return JsonResponse(
        {"message": f"Scraping completed. Processed {books_processed} books."}
    )


def one_book(request):
    url = request.GET.get("url")
    if url:
        book_data = get_book(url)
        if book_data:
            process_book_data(book_data)
    return redirect("books")
