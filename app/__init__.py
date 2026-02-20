from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from whitenoise import WhiteNoise
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    csrf.init_app(app)

    # Configure WhiteNoise for static files
    # Only if not in debug mode (Flask serves static files in debug)
    if not app.debug:
        app.wsgi_app = WhiteNoise(app.wsgi_app, root=os.path.join(os.path.dirname(__file__), 'static'), prefix='static/')

    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app

app = create_app()
