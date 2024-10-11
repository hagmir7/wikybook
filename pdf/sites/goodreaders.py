from bs4 import BeautifulSoup
from django.shortcuts import get_object_or_404, redirect
import requests
from pdf.models import Language, Category, Book, Author
from django.core.files import File
from django.contrib.auth.models import User
import json
from django.http import JsonResponse
from datetime import datetime
from tempfile import NamedTemporaryFile
import time
import traceback

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
}


def date_format(string_date):
    try:
        timestamp = int(string_date) / 1000
        readable_date = datetime.utcfromtimestamp(timestamp).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        return readable_date
    except:
        return datetime.now()


def remove_extra_spaces_and_lines(text):
    lines = text.split("\n")
    lines = [line.strip() for line in lines if line.strip()]
    cleaned_text = " ".join(lines)
    return cleaned_text


def download_image(url, id):
    try:
        response = requests.get(url, verify=True)
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


def download_file(url, id):
    try:
        response = requests.get(url, headers=headers, verify=True)
        if response.status_code == 200:
            with NamedTemporaryFile(delete=False) as file_temp:
                file_temp.write(response.content)
                file_temp.flush()
                book = Book.objects.get(id=id)
                with open(file_temp.name, "rb") as file:
                    book.file.save("file.pdf", File(file))
            print(f"PDF file saved successfully for book ID {id}.")
        else:
            print(
                f"Failed to download PDF for book ID {id}. Status code: {response.status_code}"
            )
    except Book.DoesNotExist:
        print(f"Book not found with ID {id}.")
    except Exception as e:
        print(f"An error occurred while downloading PDF for book ID {id}: {e}")


def page_download(data):
    try:
        if data.get("pdf"):
            print("There is a PDF ✅")
            download_file(data["pdf"], data.get("id"))
        else:
            print("There is no PDF 📕❌")

        # Get or create the English language
        try:
            english_language = Language.objects.get(code="en")
        except Language.DoesNotExist:
            english_language, _ = Language.objects.get_or_create(
                code="en",
                defaults={"name": "English"}
            )

        category_name = data.get("genres")[0] if data.get("genres") else "Uncategorized"
        category, _ = Category.objects.get_or_create(
            name=category_name,
            defaults={"language": english_language},
        )

        author_name = data.get("author", "Unknown Author")
        author, _ = Author.objects.get_or_create(
            full_name=author_name, 
            defaults={
                'description' : data.get("author_description")
            }
        )

        language_name = data.get("language", "Unknown Language")
        language_code = str(language_name[:2]).lower() if language_name else "un"
        language, _ = Language.objects.get_or_create(
            code=language_code,
            defaults={"name": language_name}
        )

        book_name = data.get("name", "Untitled Book")
        body_description = BeautifulSoup(data.get("description", ""), "html.parser")

        book, created = Book.objects.get_or_create(
            name=book_name,
            defaults={
                "user": User.objects.get(id=1),
                "author": author,
                "language": language,
                "description": remove_extra_spaces_and_lines(str(body_description.get_text()))[:300],
                "isbn13": data.get("isbn13"),
                "body": str(body_description),
                "tags": ", ".join(data.get("genres", [])),
                "category": category,
                "isbn": data.get("isbn"),
                "publication_date": date_format(data.get("publication_date")),
                "pages": data.get("pages")
            },
        )

        if created:
            if data.get("image"):
                download_image(data["image"], book.id)
            print(f"Book '{book_name}' created successfully.")
        else:
            print(f"Book '{book_name}' already exists.")

    except User.DoesNotExist:
        print("Error: Default user (id=1) does not exist. Please create a default user or modify the user assignment logic.")
    except Exception as e:
        print(f"An error occurred while processing book data: {e}")
        traceback.print_exc()


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
        print(f"An error occurred while extracting book info: {e}")
        traceback.print_exc()
        return None


def get_book(url):
    try:
        response = requests.get(url, verify=True, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        json_script = soup.find("script", {"id": "__NEXT_DATA__"})

        if json_script is None:
            raise ValueError("Could not find __NEXT_DATA__ script tag")

        json_string = json_script.text
        book_info = extract_book_info(json_string)

        if book_info is None:
            raise ValueError("Failed to extract book info")

        page_download(book_info)
    except requests.RequestException as e:
        print(f"HTTP Request failed for URL {url}: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed for URL {url}: {e}")
    except ValueError as e:
        print(f"Value error for URL {url}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred for URL {url}: {e}")
        traceback.print_exc()


def goodreads(request):
    total_books_processed = 0
    if request.GET.get("start") and request.GET.get("url"):
        start = int(request.GET.get("start"))
        url = request.GET.get("url")

    else:
        return JsonResponse({"message": "Url and start is required"})
    for page in range(start, int(start) + 2):
        print(f"Processing page {page}")
        url = f"{url}?page={page}/"
        try:
            response = requests.get(url, verify=True, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            table = soup.find("table", {"class": "tableList"})
            if table is None:
                print(f"No table found on page {page}. Stopping scraping.")
                break
            books = table.find_all("tr")
            print(f"Found {len(books)} books on page {page}")
            for index, book in enumerate(books, 1):
                slug = book.find("a", {"itemprop": "url"})
                if slug and slug.get("href"):
                    book_url = f"https://www.goodreads.com{slug['href']}"
                    print(f"Processing book {index} on page {page}: {book_url}")
                    get_book(book_url)
                    total_books_processed += 1
                else:
                    print(f"Could not find URL for book {index} on page {page}")
                time.sleep(1)  # Add a 1-second delay between requests
        except Exception as e:
            print(f"An error occurred while processing page {page}: {e}")
            traceback.print_exc()

    print(f"Scraping completed. Total books processed: {total_books_processed}")
    return JsonResponse(
        {
            "message": f"Scraping completed successfully. Processed {total_books_processed} books."
        }
    )


# If you want to run this script directly (not as a Django view)
if __name__ == "__main__":
    class DummyRequest:
        pass

    goodreads(DummyRequest())


def one_book(request):

    url = request.GET.get("url")

    if url:
        get_book(url)
    return redirect('books')
