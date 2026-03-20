from flask import Flask

from .config import Config
from .routes.api import api_bp
from .routes.web import web_bp


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_class)

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
