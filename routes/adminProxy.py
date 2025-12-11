from functools import wraps
from flask_login import current_user
from flask import redirect, url_for, flash

class AdminProxy:
    def __init__(self, real_function):
        self.real = real_function

    def __call__(self, *args, **kwargs):
        if current_user.role != "admin":
            flash("Acces permis doar adminilor!", "danger")
            return redirect(url_for("home.index"))
        return self.real(*args, **kwargs)