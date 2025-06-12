#!/bin/bash
# Quick start script for development and testing

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated"
else
    echo "Virtual environment not found. Run ./install.sh first."
    exit 1
fi

# Check if config.py exists
if [ ! -f "config.py" ]; then
    echo "config.py not found. Please configure your settings first."
    exit 1
fi

# Start the application
echo "Starting PLC Bridge..."
echo "Web interface will be available at: http://$(hostname -I | awk '{print $1}'):5000"
echo "Press Ctrl+C to stop"
echo ""

python main.py