#!/bin/bash
# MOJO WhatsApp Manager Setup Script

echo "Setting up MOJO WhatsApp Manager..."

# Check if Python and pip are installed
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is required but could not be found. Please install Python 3 and try again."
    exit 1
fi

if ! command -v pip3 &> /dev/null
then
    echo "pip3 is required but could not be found. Please install pip3 and try again."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Create instance directory
echo "Creating instance directory..."
mkdir -p instance

# Initialize the database
echo "Initializing the database..."
export FLASK_APP=web.py
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Create admin user
echo "Creating admin user..."
flask create-admin --username mojo-admin --password Letmein99#123

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p reports
mkdir -p temp
mkdir -p mojo_web/static/img

echo "Setup complete!"
echo ""
echo "To start the application, run:"
echo "source venv/bin/activate"
echo "python web.py"
echo ""
echo "Then visit http://localhost:5000 in your browser"
echo ""
echo "Login with:"
echo "Username: mojo-admin"
echo "Password: Letmein99#123" 