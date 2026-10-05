import time
import requests
from io import BytesIO
from PIL import Image

from app import app, db, Book


def process_portraits():
    while True:
        with app.app_context():
            books = Book.query.filter(
                Book.author_portrait.isnot(None),
                Book.portrait_width.is_(None)
            ).all()

            for book in books:
                try:
                    response = requests.get(
                        book.author_portrait,
                        timeout=30
                    )
                    response.raise_for_status()

                    image_data = BytesIO(response.content)

                    with Image.open(image_data) as image:
                        book.portrait_width = image.width
                        book.portrait_height = image.height

                    book.portrait_size = len(response.content)
                    db.session.commit()

                    print(
                        f"Background task processed "
                        f"portrait for book: {book.title}"
                    )

                except Exception as error:
                    print(f"Could not process portrait: {error}")

        time.sleep(10)


process_portraits()
