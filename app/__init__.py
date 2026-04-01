from flask import Flask
from config import Config
from app.extensions import db, login_manager, csrf
from app.models import User


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.auth import auth
    from app.main import main
    from app.librarian import librarian

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(librarian)

    with app.app_context():
        db.create_all()

    return app
