from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin
from config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    from routes.login_register import auth
    from routes.logout import logout_bp
    from routes.home import home_bp
    from routes.task import tasks_bp   


    app.register_blueprint(auth)
    app.register_blueprint(logout_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(tasks_bp)   

    return app


@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
