from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin
from config import Config
from flask_login import current_user

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
    from routes.friends import friends_bp
    from routes.notifications import notifications_bp

    app.register_blueprint(auth)
    app.register_blueprint(logout_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(friends_bp)
    app.register_blueprint(notifications_bp)

    @app.context_processor
    def inject_notifications():
        from models import Notification
        if current_user.is_authenticated:
            notifs = Notification.query.filter_by(user_id=current_user.id, seen=False).all()
        else:
            notifs = []

        return {"notifications": notifs}
    return app

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

