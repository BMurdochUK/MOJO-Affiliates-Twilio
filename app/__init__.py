import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_apscheduler import APScheduler

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
scheduler = APScheduler()

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Default configuration
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'mojo_manager.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SCHEDULER_API_ENABLED=True
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize database
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize scheduler
    scheduler.init_app(app)
    scheduler.start()

    # Register blueprints
    from app.routes import dashboard, templates, messages, reports, settings
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(templates.bp)
    app.register_blueprint(messages.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(settings.bp)

    # Make url_for('index') work
    app.add_url_rule('/', endpoint='index')

    return app 