
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify
)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

# Database
database_url = os.environ.get("DATABASE_URL")

if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://", "postgresql://", 1
        )

    # Compatibility with PostgreSQL URLs using older driver syntax
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://", "postgresql+psycopg2://", 1
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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


# Create tables if they do not exist
with app.app_context():
    db.create_all()


def book_to_dict(book):
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "published_date": book.published_date.isoformat(),
        "pages": book.pages,
        "available": book.available,
        "author_portrait": book.author_portrait,
        "portrait_width": book.portrait_width,
        "portrait_height": book.portrait_height,
        "portrait_size": book.portrait_size
    }


# -------------------------
# WEB APPLICATION
# -------------------------

@app.route("/")
def index():
    books = Book.query.all()
    return render_template("index.html", books=books)


@app.route("/add", methods=["POST"])
def add_book():
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()

    try:
        published_date = datetime.strptime(
            request.form["published_date"], "%Y-%m-%d"
        ).date()
        pages = int(request.form["pages"])

        if not title or not author or pages <= 0:
            return "Invalid title, author or pages", 400

    except (ValueError, KeyError):
        return "Invalid date or pages", 400

    available = "available" in request.form
    portrait = request.files.get("author_portrait")
    portrait_url = None

    if portrait and portrait.filename:
        result = cloudinary.uploader.upload(
            portrait, folder="book-manager"
        )
        portrait_url = result["secure_url"]

    book = Book(
        title=title,
        author=author,
        published_date=published_date,
        pages=pages,
        available=available,
        author_portrait=portrait_url
    )

    db.session.add(book)
    db.session.commit()

    return redirect(url_for("index"))


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_book(id):
    book = db.get_or_404(Book, id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()

        try:
            published_date = datetime.strptime(
                request.form["published_date"], "%Y-%m-%d"
            ).date()
            pages = int(request.form["pages"])

            if not title or not author or pages <= 0:
                return "Invalid title, author or pages", 400

        except (ValueError, KeyError):
            return "Invalid date or pages", 400

        book.title = title
        book.author = author
        book.published_date = published_date
        book.pages = pages
        book.available = "available" in request.form

        portrait = request.files.get("author_portrait")

        if portrait and portrait.filename:
            result = cloudinary.uploader.upload(
                portrait, folder="book-manager"
            )
            book.author_portrait = result["secure_url"]
            book.portrait_width = None
            book.portrait_height = None
            book.portrait_size = None

        db.session.commit()
        return redirect(url_for("index"))

    return render_template("edit.html", book=book)


@app.route("/delete/<int:id>", methods=["POST", "GET"])
def delete_book(id):
    book = db.get_or_404(Book, id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for("index"))


# -------------------------
# REST API
# -------------------------

@app.route("/api/books", methods=["GET"])
def api_get_books():
    return jsonify([
        book_to_dict(book) for book in Book.query.all()
    ])


@app.route("/api/books/<int:id>", methods=["GET"])
def api_get_book(id):
    book = db.get_or_404(Book, id)
    return jsonify(book_to_dict(book))


@app.route("/api/books", methods=["POST"])
def api_create_book():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON data is required"}), 400

    try:
        title = str(data["title"]).strip()
        author = str(data["author"]).strip()
        published_date = datetime.strptime(
            data["published_date"], "%Y-%m-%d"
        ).date()
        pages = int(data["pages"])
        available = data.get("available", True)

        if not title or not author or pages <= 0:
            raise ValueError

        if not isinstance(available, bool):
            raise ValueError

    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "Invalid input"}), 400

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


@app.route("/api/books/<int:id>", methods=["PUT"])
def api_update_book(id):
    book = db.get_or_404(Book, id)
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON data is required"}), 400

    try:
        title = str(data["title"]).strip()
        author = str(data["author"]).strip()
        published_date = datetime.strptime(
            data["published_date"], "%Y-%m-%d"
        ).date()
        pages = int(data["pages"])
        available = data["available"]

        if (
            not title or not author or pages <= 0
            or not isinstance(available, bool)
        ):
            raise ValueError

    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "Invalid input"}), 400

    book.title = title
    book.author = author
    book.published_date = published_date
    book.pages = pages
    book.available = available

    db.session.commit()

    return jsonify({"message": "Book updated"})


@app.route("/api/books/<int:id>", methods=["DELETE"])
def api_delete_book(id):
    book = db.get_or_404(Book, id)
    db.session.delete(book)
    db.session.commit()
    return jsonify({"message": "Book deleted"})


if __name__ == "__main__":
    app.run(debug=False)
