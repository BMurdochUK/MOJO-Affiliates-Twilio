# MOJO WhatsApp Manager Deployment Guide

This guide provides instructions for deploying the MOJO WhatsApp Manager web interface locally for testing.

## Local Deployment

1. Make sure you have Python 3.6+ installed on your system
2. Run the setup script:
   ```bash
   ./setup.sh
   ```
   This will:
   - Create a virtual environment
   - Install all dependencies
   - Initialize the database
   - Create an admin user
   - Create necessary directories

3. Start the web server:
   ```bash
   source venv/bin/activate
   python web.py
   ```

4. Access the web interface by opening a browser and navigating to:
   ```
   http://localhost:5000
   ```

5. Log in with the default credentials:
   - Username: mojo-admin
   - Password: Letmein99#123

## Security Notes

- The default credentials should be changed in a production environment
- In production, the SECRET_KEY should be set to a random value
- Use HTTPS in production environments to protect authentication credentials
- Remove debug mode in production by setting debug=False in web.py

## Production Deployment

For production deployment, consider using:
- Gunicorn or uWSGI as the WSGI server
- Nginx or Apache as a reverse proxy
- Supervisor for process management
- Environment variables for configuration

Example production command:
```bash
gunicorn -w 4 -b 127.0.0.1:8000 'web:app'
```

Then configure Nginx to proxy requests to this address. 