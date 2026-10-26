
from io import BytesIO

import requests
from PIL import Image

from app import app, db, Book


def process_portraits():
    with app.app_context():
        try:
            books = Book.query.filter(
                Book.author_portrait.isnot(None),
                Book.portrait_width.is_(None),
            ).all()

            print(f"Rasta knygų nuotraukų apdorojimui: {len(books)}")

            for book in books:
                try:
                    response = requests.get(book.author_portrait, timeout=30)
                    response.raise_for_status()

                    with Image.open(BytesIO(response.content)) as image:
                        book.portrait_width = image.width
                        book.portrait_height = image.height

                    book.portrait_size = len(response.content)
                    db.session.commit()

                    print(f"Apdorota: {book.title}")

                except Exception as error:
                    db.session.rollback()
                    print(f"Nepavyko apdoroti '{book.title}': {error}")

        finally:
            db.session.remove()


if __name__ == "__main__":
    process_portraits()
