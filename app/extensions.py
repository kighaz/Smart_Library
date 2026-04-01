from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Bitte melde dich an, um diese Seite zu besuchen.'
login_manager.login_message_category = 'warning'
csrf = CSRFProtect()
