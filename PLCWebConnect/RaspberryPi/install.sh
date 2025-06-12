#!/bin/bash
# Raspberry Pi PLC Bridge Installation Script

set -e  # Exit on any error

echo "=========================================="
echo "PLC Bridge Installation for Raspberry Pi"
echo "=========================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root for security reasons."
   echo "Please run as a regular user. The script will prompt for sudo when needed."
   exit 1
fi

# Update system packages
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and pip if not already installed
echo "Installing Python dependencies..."
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install system dependencies for GPIO and serial communication
echo "Installing system dependencies..."
sudo apt install -y build-essential

# Create virtual environment
echo "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment and install Python packages
echo "Installing Python packages..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Add user to dialout group for serial port access
echo "Adding user to dialout group for serial port access..."
sudo usermod -a -G dialout $USER

# Create systemd service file
echo "Creating systemd service..."
sudo tee /etc/systemd/system/plc-bridge.service > /dev/null <<EOF
[Unit]
Description=PLC Bridge Web Interface
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable plc-bridge.service

# Create log rotation configuration
echo "Setting up log rotation..."
sudo tee /etc/logrotate.d/plc-bridge > /dev/null <<EOF
$(pwd)/plc_web_bridge.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF

echo "=========================================="
echo "Installation completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Log out and log back in (or reboot) for group changes to take effect"
echo "2. Edit config.py to match your PLC settings"
echo "3. Connect your PLC to the Raspberry Pi via serial/USB"
echo "4. Start the service: sudo systemctl start plc-bridge"
echo "5. Check status: sudo systemctl status plc-bridge"
echo "6. View logs: journalctl -u plc-bridge -f"
echo ""
echo "Web interface will be available at:"
echo "- http://$(hostname -I | awk '{print $1}'):5000"
echo "- http://localhost:5000 (local access)"
echo ""
echo "To start manually (for testing):"
echo "source venv/bin/activate && python main.py"