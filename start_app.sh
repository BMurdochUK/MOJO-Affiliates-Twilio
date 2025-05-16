#!/bin/bash
# Start MOJO WhatsApp Manager application

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source $DIR/venv/bin/activate

# Show Python version
echo "Using Python: $(which python3)"
echo "Python version: $(python3 --version)"
echo

# Start the application
echo "Starting MOJO WhatsApp Manager..."
python3 $DIR/web.py

# Deactivate virtual environment on exit
deactivate 