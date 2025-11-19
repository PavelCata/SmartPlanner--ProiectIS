from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

home_bp = Blueprint("home", __name__)

@home_bp.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect("/login")
    return redirect(url_for("tasks.view_tasks"))

 