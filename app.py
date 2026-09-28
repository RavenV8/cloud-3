from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    published_date = db.Column(db.String(20), nullable=False)
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
    published_date = request.form["published_date"]
    pages = int(request.form["pages"])
    available = "available" in request.form

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


@app.route("/delete/<int:id>")
def delete_book(id):
    book = Book.query.get_or_404(id)

    db.session.delete(book)
    db.session.commit()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
