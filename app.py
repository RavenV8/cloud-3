from flask import Flask, render_template, request, redirect
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


if __name__ == "__main__":
    app.run(debug=True)
