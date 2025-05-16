"""
MOJO WhatsApp Manager Web Application
"""
import os
from flask import Flask, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_apscheduler import APScheduler
from flask_login import LoginManager, current_user

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
scheduler = APScheduler()
login_manager = LoginManager()

def create_app(test_config=None):
    """
    Create and configure the Flask application
    """
    # Create Flask app
    app = Flask(__name__, instance_relative_config=True)
    
    # Load default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'DATABASE_URL', 
            'sqlite:///' + os.path.join(app.instance_path, 'mojo_web.db')
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SCHEDULER_API_ENABLED=True,
        TWILIO_ACCOUNT_SID=os.environ.get('TWILIO_ACCOUNT_SID'),
        TWILIO_AUTH_TOKEN=os.environ.get('TWILIO_AUTH_TOKEN'),
        TWILIO_WHATSAPP_NUMBER=os.environ.get('TWILIO_WHATSAPP_NUMBER'),
        TWILIO_MESSAGING_SERVICE_SID=os.environ.get('TWILIO_MESSAGING_SERVICE_SID'),
        DEFAULT_DB_PATH=os.environ.get('DB_PATH', 'affiliates.db')
    )
    
    # Override with instance config if specified
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    scheduler.init_app(app)
    scheduler.start()
    
    # Configure Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        from mojo_web.models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from mojo_web.routes import dashboard, templates, contacts, campaigns, reports, auth, settings
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(templates.bp)
    app.register_blueprint(contacts.bp) 
    app.register_blueprint(campaigns.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(settings.bp)
    
    # Register CLI commands
    from mojo_web.commands import create_admin_command
    app.cli.add_command(create_admin_command)
    
    # Add authentication to all routes except auth routes
    @app.before_request
    def check_authentication():
        # Skip auth routes and static files
        if request.endpoint and (request.endpoint.startswith('auth.') or request.endpoint.startswith('static')):
            return
            
        # Require authentication for all other routes
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
    
    # Make url_for('index') work
    app.add_url_rule('/', endpoint='index')
    
    return app 