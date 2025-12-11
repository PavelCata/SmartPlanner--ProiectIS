from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import User
from app import db

admin_panel = Blueprint("admin_panel", __name__, url_prefix="/admin")

def is_admin():
    return current_user.is_authenticated and current_user.role == "admin"

@admin_panel.before_request
def protect_panel():
    if not is_admin():
        flash("Acces permis doar adminilor!", "danger")
        return redirect(url_for("home.index"))

@admin_panel.route("/dashboard")
@login_required
def dashboard():
    users = User.query.filter(User.role != "admin").all()
    return render_template("adminPanel.html", users=users)

@admin_panel.route("/ban/<int:user_id>")
@login_required
def ban_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("Utilizatorul a fost sters!", "success")
    return redirect(url_for("admin_panel.dashboard"))

@admin_panel.route("/restrict/<int:user_id>")
@login_required
def restrict_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.restricted = True
        db.session.commit()
        flash("Utilizatorul a fost restrictionat!", "warning")
    return redirect(url_for("admin_panel.dashboard"))

@admin_panel.route("/unrestrict/<int:user_id>")
@login_required
def unrestrict_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.restricted = False
        db.session.commit()
        flash("Utilizatorul a fost deblocat!", "success")
    return redirect(url_for("admin_panel.dashboard"))
