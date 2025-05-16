"""
Unit tests for the MOJO web interface
"""
import os
import tempfile
import pytest
from mojo_web import create_app
from mojo_web import db as _db

@pytest.fixture
def app():
    """Create and configure a Flask app for testing"""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False
    })
    
    # Create the database and tables
    with app.app_context():
        _db.create_all()
    
    yield app
    
    # Close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app"""
    return app.test_cli_runner()

@pytest.fixture
def db(app):
    """Database fixture for tests"""
    with app.app_context():
        _db.create_all()
        
        yield _db
        
        _db.session.remove()
        _db.drop_all()

def test_dashboard_page(client):
    """Test the dashboard page loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Dashboard' in response.data

def test_templates_page(client):
    """Test the templates page loads successfully"""
    response = client.get('/templates/')
    assert response.status_code == 200
    assert b'Templates' in response.data

def test_campaigns_page(client):
    """Test the campaigns page loads successfully"""
    response = client.get('/campaigns/')
    assert response.status_code == 200
    assert b'Campaigns' in response.data

def test_reports_page(client):
    """Test the reports page loads successfully"""
    response = client.get('/reports/')
    assert response.status_code == 200
    assert b'Reports' in response.data 