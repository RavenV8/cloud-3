from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    published_date = db.Column(db.Date, nullable=False)
    pages = db.Column(db.Integer, nullable=False)
    available = db.Column(db.Boolean, default=True)


with app.app_context():
    db.create_all()


# --------------------
# WEB APPLICATION
# --------------------

@app.route("/")
def home():
    books = Book.query.all()
    return render_template("index.html", books=books)


@app.route("/add", methods=["POST"])
def add_book():
    title = request.form["title"]
    author = request.form["author"]

    published_date = datetime.strptime(
        request.form["published_date"], "%Y-%m-%d"
    ).date()

    pages = int(request.form["pages"])
    available = "available" in request.form

    if pages <= 0:
        return "Pages must be greater than 0", 400

    book = Book(
        title=title,
        author=author,
        published_date=published_date,
        pages=pages,
        available=available
    )

    db.session.add(book)
    db.session.commit()

    return redirect("/")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_book(id):
    book = Book.query.get_or_404(id)

    if request.method == "POST":

        book.title = request.form["title"]
        book.author = request.form["author"]

        book.published_date = datetime.strptime(
            request.form["published_date"], "%Y-%m-%d"
        ).date()

        book.pages = int(request.form["pages"])
        book.available = "available" in request.form

        if book.pages <= 0:
            return "Pages must be greater than 0", 400

        db.session.commit()

        return redirect("/")

    return render_template("edit.html", book=book)


@app.route("/delete/<int:id>")
def delete_book(id):
    book = Book.query.get_or_404(id)

    db.session.delete(book)
    db.session.commit()

    return redirect("/")


# --------------------
# PUBLIC API
# --------------------

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
            "available": book.available
        }
        for book in books
    ])


@app.route("/api/books/<int:id>", methods=["GET"])
def api_get_book(id):

    book = Book.query.get_or_404(id)

    return jsonify({
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "published_date": book.published_date.isoformat(),
        "pages": book.pages,
        "available": book.available
    })


@app.route("/api/books", methods=["POST"])
def api_create_book():

    data = request.get_json()

    try:
        title = data["title"]
        author = data["author"]
        published_date = datetime.strptime(
            data["published_date"], "%Y-%m-%d"
        ).date()
        pages = int(data["pages"])
        available = bool(data["available"])

        if not title or not author:
            return jsonify({"error": "Title and author are required"}), 400

        if pages <= 0:
            return jsonify({"error": "Pages must be greater than 0"}), 400

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

    book = Book.query.get_or_404(id)
    data = request.get_json()

    try:
        book.title = data["title"]
        book.author = data["author"]

        book.published_date = datetime.strptime(
            data["published_date"], "%Y-%m-%d"
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
        return jsonify({"error": "Invalid input"}), 400

    db.session.commit()

    return jsonify({
        "message": "Book updated"
    })


@app.route("/api/books/<int:id>", methods=["DELETE"])
def api_delete_book(id):

    book = Book.query.get_or_404(id)

    db.session.delete(book)
    db.session.commit()

    return jsonify({
        "message": "Book deleted"
    })


if __name__ == "__main__":
    app.run(debug=True)
