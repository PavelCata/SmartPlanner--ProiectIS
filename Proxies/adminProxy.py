from functools import wraps
from flask_login import current_user
from flask import redirect, url_for, flash
from models import User
import logging
from datetime import datetime

logging.basicConfig(
    filename='admin_actions.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def restriction_proxy(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            user = User.query.get(current_user.id)
            if user and user.restricted:
                flash("Contul tau este restrictionat. Nu poti efectua aceasta actiune!!", "danger")
                return redirect(url_for("home.index"))
        return f(*args, **kwargs)
    return decorated_function

def admin_only_proxy(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("Acces permis doar adminilor!", "danger")
            return redirect(url_for("home.index"))
        return f(*args, **kwargs)
    return decorated_function

def admin_audit_proxy(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        log_entry = (f"ADMIN: {current_user.username} a executat {f.__name__} "
                     f"pentru ID: {kwargs.get('user_id') or (args[0] if args else 'N/A')}")
        logging.info(log_entry)
        return response
    return decorated_function