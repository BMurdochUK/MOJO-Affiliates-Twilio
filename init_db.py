#!/usr/bin/env python3
"""
Database initialization script for MOJO WhatsApp Manager
"""
import os
import sys

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from mojo_web import create_app, db
from mojo_web.models import User

def init_db():
    """Initialize the database"""
    # Create app context
    app = create_app()
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='mojo-admin').first()
        if not admin:
            admin = User(username='mojo-admin')
            admin.set_password('Letmein99#123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully.")
        else:
            print("Admin user already exists.")
        
        print("Database initialization complete.")

if __name__ == "__main__":
    init_db() 