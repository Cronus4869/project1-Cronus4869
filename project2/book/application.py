import os

from flask import Flask, render_template, request
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    # get form information
    user = request.form.get("usrname")
    password = request.form.get("password")

    if db.execute("SELECT usrname FROM users WHERE usrname = :usrname", {"usrname": user}).rowcount == 0:
        db.execute("INSERT INTO users (usrname, password) VALUES (:usrname, :password)", {"usrname": user, "password": password})
        db.execute("INSERT INTO nowusers (usrname) VALUES (:usrname)", {"usrname": user})
        db.commit()
        return render_template("search.html", user=user)

    elif db.execute("SELECT * FROM users WHERE usrname = :usrname and password = :password", {"usrname": user, "password": password}).rowcount == 1:
        db.execute("INSERT INTO nowusers (usrname) VALUES (:usrname)", {"usrname": user})
        db.commit()
        return render_template("search.html", user=user)

    elif db.execute("SELECT * FROM users WHERE usrname = :usrname and password = :password", {"usrname": user, "password": password}).rowcount == 0:
        return render_template("error.html", message="wrong password.")


# @app.route("/logout", method=["POST"])
# def logout():
#     db.execute("DELETE FROM nowusers WHERE usrname = :usrname", {"usrname": usrname})
#     db.commit()
#     return render_template("index.html")

@app.route("/book/<string:user>", methods=["POST"])
def book(user):
    choice = request.form.get("choice")
    book = request.form.get("book")

    if choice == "isbn":
        results = db.execute("SELECT * FROM books WHERE isbn LIKE '%%%s%%'" % book).fetchall()

    elif choice == "title":
        results = db.execute("SELECT * FROM books WHERE title LIKE '%%%s%%'" % book).fetchall()

    elif choice == "author":
        results = db.execute("SELECT * FROM books WHERE author LIKE '%%%s%%'" % book).fetchall()

    else:
        results = db.execute("SELECT * FROM books WHERE year = :year", {"year": book}).fetchall()

    if results is None:
        return render_template("error.html", message="No such book.", user=user)

    return render_template("result.html", results=results, user=user)


@app.route("/book/<book_isbn>/<user>")
def onebook(book_isbn, user):
    res = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_isbn}).fetchone()
    if res is None:
        return render_template("error.html", message="No such book.", user=user)

    reviews = db.execute("SELECT * FROM review WHERE isbn = :isbn", {"isbn": book_isbn}).fetchone()
    if reviews is None:
        return render_template("noreview.html", res=res, user=user)
    else:
        return render_template("onebook.html", res=res, user=user, reviews=reviews)


@app.route("/review/<isbn>/<usrname>", methods=["POST"])
def review(isbn, usrname):
    rating = request.form.get("rating")
    content = request.form.get("content")

    if db.execute("SELECT * FROM review WHERE isbn = :isbn and usrname = :usrname", {"isbn": isbn, "usrname": usrname}).rowcount > 0:
        return render_template("error.html", message="Cannot submit review again.", user=usrname)

    if content:
        db.execute("INSERT INTO review (isbn, usrname, rating, content) VALUES (:isbn, :usrname, :rating, :content)", {"isbn": isbn, "usrname": usrname, "rating": rating, "content": content})
        return render_template("success.html", user=usrname)
    else:
        return render_template("error.html", message="no review need to be add.", user=usrname)


@app.route("/logout/<user>")
def logout(user):
    db.execute("DELETE FROM nowusers WHERE usrname = :usrname", {"usrname": user})
    db.commit()
    return render_template("index.html")

