from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from PIL import Image
import os
import threading
import time
app = Flask(__name__)

# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# File storage
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)


# Book model
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    published_date = db.Column(db.Date, nullable=False)
    pages = db.Column(db.Integer, nullable=False)
    available = db.Column(db.Boolean, default=True)
    author_portrait = db.Column(db.String(255), nullable=True)
    portrait_width = db.Column(db.Integer, nullable=True)
    portrait_height = db.Column(db.Integer, nullable=True)
    portrait_size = db.Column(db.Integer, nullable=True)


# Create database
with app.app_context():
    db.create_all()


# -------------------------
# WEB APPLICATION
# -------------------------

# List all books
@app.route("/")
def index():
    books = Book.query.all()
    return render_template("index.html", books=books)


# Add a book
@app.route("/add", methods=["POST"])
def add_book():
    title = request.form["title"]
    author = request.form["author"]

    try:
        published_date = datetime.strptime(
            request.form["published_date"],
            "%Y-%m-%d"
        ).date()

        pages = int(request.form["pages"])

        if pages <= 0:
            return "Pages must be greater than 0", 400

    except (ValueError, KeyError):
        return "Invalid date or pages", 400

    available = "available" in request.form

    # Upload author portrait
    portrait = request.files.get("author_portrait")
    filename = None

    if portrait and portrait.filename:
        filename = portrait.filename
        portrait.save(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )
        )

    book = Book(
        title=title,
        author=author,
        published_date=published_date,
        pages=pages,
        available=available,
        author_portrait=filename
    )

    db.session.add(book)
    db.session.commit()

    return redirect(url_for("index"))


# Edit book
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_book(id):
    book = Book.query.get_or_404(id)

    if request.method == "POST":
        book.title = request.form["title"]
        book.author = request.form["author"]

        try:
            book.published_date = datetime.strptime(
                request.form["published_date"],
                "%Y-%m-%d"
            ).date()

            book.pages = int(request.form["pages"])

            if book.pages <= 0:
                return "Pages must be greater than 0", 400

        except (ValueError, KeyError):
            return "Invalid date or pages", 400

        book.available = "available" in request.form

        # Optional new portrait
        portrait = request.files.get("author_portrait")

        if portrait and portrait.filename:
            filename = portrait.filename

            portrait.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

            book.author_portrait = filename

        db.session.commit()

        return redirect(url_for("index"))

    return render_template("edit.html", book=book)


# Delete book
@app.route("/delete/<int:id>")
def delete_book(id):
    book = Book.query.get_or_404(id)

    db.session.delete(book)
    db.session.commit()

    return redirect(url_for("index"))


# Serve uploaded files
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


# -------------------------
# PUBLIC REST API
# -------------------------

# GET all books
@app.route("/api/books", methods=["GET"])
def api_get_books():
    books = Book.query.all()

    return jsonify([
        {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "published_date": book.published_date.isoformat(),
            "pages": book.pages,
            "available": book.available,
            "author_portrait": book.author_portrait
        }
        for book in books
    ])


# GET one book
@app.route("/api/books/<int:id>", methods=["GET"])
def api_get_book(id):
    book = Book.query.get_or_404(id)

    return jsonify({
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "published_date": book.published_date.isoformat(),
        "pages": book.pages,
        "available": book.available,
        "author_portrait": book.author_portrait
    })


# CREATE book through API
@app.route("/api/books", methods=["POST"])
def api_create_book():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON data is required"
        }), 400

    try:
        title = data["title"]
        author = data["author"]

        published_date = datetime.strptime(
            data["published_date"],
            "%Y-%m-%d"
        ).date()

        pages = int(data["pages"])
        available = bool(data["available"])

        if not title or not author:
            return jsonify({
                "error": "Title and author are required"
            }), 400

        if pages <= 0:
            return jsonify({
                "error": "Pages must be greater than 0"
            }), 400

    except (KeyError, ValueError, TypeError):
        return jsonify({
            "error": "Invalid input"
        }), 400

    book = Book(
        title=title,
        author=author,
        published_date=published_date,
        pages=pages,
        available=available
    )

    db.session.add(book)
    db.session.commit()

    return jsonify({
        "message": "Book created",
        "id": book.id
    }), 201


# UPDATE book through API
@app.route("/api/books/<int:id>", methods=["PUT"])
def api_update_book(id):
    book = Book.query.get_or_404(id)

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON data is required"
        }), 400

    try:
        book.title = data["title"]
        book.author = data["author"]

        book.published_date = datetime.strptime(
            data["published_date"],
            "%Y-%m-%d"
        ).date()

        book.pages = int(data["pages"])
        book.available = bool(data["available"])

        if not book.title or not book.author:
            return jsonify({
                "error": "Title and author are required"
            }), 400

        if book.pages <= 0:
            return jsonify({
                "error": "Pages must be greater than 0"
            }), 400

    except (KeyError, ValueError, TypeError):
        return jsonify({
            "error": "Invalid input"
        }), 400

    db.session.commit()

    return jsonify({
        "message": "Book updated"
    })


# DELETE book through API
@app.route("/api/books/<int:id>", methods=["DELETE"])
def api_delete_book(id):
    book = Book.query.get_or_404(id)

    db.session.delete(book)
    db.session.commit()

    return jsonify({
        "message": "Book deleted"
    })


# -------------------------
# RUN APPLICATION
# -------------------------

def process_portraits():
    while True:
        with app.app_context():

            books = Book.query.filter(
                Book.author_portrait.isnot(None),
                Book.portrait_width.is_(None)
            ).all()

            for book in books:
                file_path = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    book.author_portrait
                )

                if os.path.exists(file_path):
                    try:
                        with Image.open(file_path) as image:
                            book.portrait_width = image.width
                            book.portrait_height = image.height

                        book.portrait_size = os.path.getsize(file_path)

                        db.session.commit()

                        print(
                            f"Background task processed portrait "
                            f"for book: {book.title}"
                        )

                    except Exception as error:
                        print(
                            f"Could not process portrait: {error}"
                        )

        time.sleep(10)

def process_portraits():
    while True:
        with app.app_context():

            books = Book.query.filter(
                Book.author_portrait.isnot(None),
                Book.portrait_width.is_(None)
            ).all()

            for book in books:
                file_path = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    book.author_portrait
                )

                if os.path.exists(file_path):
                    try:
                        with Image.open(file_path) as image:
                            book.portrait_width = image.width
                            book.portrait_height = image.height

                        book.portrait_size = os.path.getsize(file_path)

                        db.session.commit()

                        print(
                            f"Background task processed portrait "
                            f"for book: {book.title}"
                        )

                    except Exception as error:
                        print(
                            f"Could not process portrait: {error}"
                        )

        time.sleep(10)

if __name__ == "__main__":
    background_thread = threading.Thread(
        target=process_portraits,
        daemon=True
    )

    background_thread.start()

    app.run(debug=True)
