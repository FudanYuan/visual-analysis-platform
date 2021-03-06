from flask import Flask, redirect
from flask_sqlalchemy import SQLAlchemy
from config import config

db = SQLAlchemy()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)

    @app.route('/')
    def index():
        return redirect('/index')

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint, url_prefix='/main')
    from .index import main as index_blueprint
    app.register_blueprint(index_blueprint, url_prefix='/index')


    return app
