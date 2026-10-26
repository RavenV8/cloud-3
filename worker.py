
from io import BytesIO
import os
import requests
from PIL import Image, UnidentifiedImageError

from app import app, db, Book


def process_portraits():
    print("WORKER STARTED", flush=True)

    with app.app_context():
        try:
            books = Book.query.filter(
                Book.author_portrait.isnot(None),
                Book.portrait_width.is_(None)
            ).all()

            print(
                f"Rasta knygų nuotraukų apdorojimui: {len(books)}",
                flush=True
            )

            for book in books:
                try:
                    print(
                        f"Apdorojama: {book.title}",
                        flush=True
                    )

                    response = requests.get(
                        book.author_portrait,
                        timeout=30
                    )
                    response.raise_for_status()

                    image_data = response.content

                    with Image.open(BytesIO(image_data)) as image:
                        width, height = image.size
                        image.verify()

                    book.portrait_width = width
                    book.portrait_height = height
                    book.portrait_size = len(image_data)

                    db.session.commit()

                    print(
                        f"APDOROTA: {book.title} "
                        f"({width}x{height}, {len(image_data)} bytes)",
                        flush=True
                    )

                except (
                    requests.RequestException,
                    UnidentifiedImageError,
                    OSError,
                    ValueError
                ) as error:
                    db.session.rollback()
                    print(
                        f"KLAIDA apdorojant '{book.title}': {error}",
                        flush=True
                    )

                except Exception as error:
                    db.session.rollback()
                    print(
                        f"NETIKĖTA KLAIDA '{book.title}': {error}",
                        flush=True
                    )

        except Exception as error:
            db.session.rollback()
            print(
                f"WORKER FAILED: {error}",
                flush=True
            )
            raise

        finally:
            db.session.remove()

    print("WORKER FINISHED", flush=True)


if __name__ == "__main__":
    process_portraits()
