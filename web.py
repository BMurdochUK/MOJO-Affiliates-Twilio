#!/usr/bin/env python3
"""
MOJO WhatsApp Manager Web Interface

This file starts the web interface for MOJO WhatsApp Manager.
The command-line functionality is still accessible through the original scripts.
"""
import os
import datetime
from werkzeug.middleware.proxy_fix import ProxyFix
from mojo_web import create_app

# Create Flask app
app = create_app()

# Add middleware for handling proxies
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Add current year to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

# Create directory for logo storage
@app.before_first_request
def setup_dirs():
    os.makedirs(os.path.join(app.static_folder, 'img'), exist_ok=True)

if __name__ == '__main__':
    print("Starting MOJO WhatsApp Manager Web Interface...")
    print("")
    print("IMPORTANT: Before first use, run the following command to create an admin user:")
    print("flask create-admin --username mojo-admin --password Letmein99#123")
    print("")
    print("Note: CLI functionality is still accessible through the original scripts.")
    print("Open http://localhost:5000 in your browser")
    print("")
    print("Default login credentials:")
    print("Username: mojo-admin")
    print("Password: Letmein99#123")
    print("")
    app.run(host='0.0.0.0', port=5000, debug=True) 