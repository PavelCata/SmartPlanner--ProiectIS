from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, current_user
from app import db, bcrypt
from models import User

auth = Blueprint("auth", __name__)

@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"].lower()
        password = request.form["password"]
        confirm = request.form["confirm"]
        secret_code = request.form.get("secret_code", "").strip()


        if password != confirm:
            flash("Parolele nu coincid!", "danger")
            return redirect(url_for("auth.register"))

        user_exists = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if user_exists:
            flash("Username sau email deja folosit!", "warning")
            return redirect(url_for("auth.register"))

        if secret_code:
            if secret_code == "c0ds3cre7d34dm1n":
                role = "admin"
            else:
                flash("Cod admin incorect!", "danger")
                return redirect(url_for("auth.register"))
        else:
            role = "user"

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(username=username, email=email, password_hash=hashed, role=role)

        db.session.add(user)
        db.session.commit()

        flash("Cont creat! Te poti loga.", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    if request.method == "POST":
        user_input = request.form["user_input"].strip()
        password = request.form["password"]

        user = User.query.filter(
            (User.username == user_input) | (User.email == user_input)
        ).first()

        if not user:
            flash("Username sau email inexistent!", "danger")
            return redirect(url_for("auth.login"))

        if not bcrypt.check_password_hash(user.password_hash, password):
            flash("Parola incorecta!", "danger")
            return redirect(url_for("auth.login"))

        login_user(user)

        if user.role == "admin":
            flash("Autentificat ca ADMIN!", "success")
        else:
            flash("Autentificat ca USER!", "success")

        return redirect(url_for("home.index"))

    return render_template("login.html")
