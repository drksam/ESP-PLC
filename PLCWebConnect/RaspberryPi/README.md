# Raspberry Pi PLC Bridge

Complete web-based interface for AutomationDirect CLICK PLCs running on Raspberry Pi with GPIO automation capabilities.

## Features

- **Real-time PLC Monitoring**: Live data display from AutomationDirect CLICK PLCs
- **Custom Automation Scripts**: User-programmable GPIO control and logic
- **Web Interface**: Responsive design accessible from any device
- **Systemd Integration**: Automatic startup and service management
- **Data Logging**: Historical data tracking and analysis
- **Script Management**: Web-based script editor with templates and examples

## Hardware Requirements

- Raspberry Pi 3B+ or newer
- MicroSD card (16GB+ recommended)
- USB-to-Serial adapter or direct serial connection
- AutomationDirect CLICK PLC
- Network connection (Ethernet or WiFi)

## Quick Installation

1. **Download and extract** the RaspberryPi folder to your Pi
2. **Run the installation script**:
   ```bash
   cd RaspberryPi
   ./install.sh
   ```
3. **Configure your PLC settings** in `config.py`
4. **Start the service**:
   ```bash
   sudo systemctl start plc-bridge
   ```

## Manual Installation

### System Dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv python3-dev build-essential
```

### Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### User Permissions
```bash
sudo usermod -a -G dialout $USER
# Log out and back in for changes to take effect
```

## Configuration

Edit `config.py` to match your setup:

```python
# PLC Connection Settings
SERIAL_PORT = '/dev/ttyUSB0'  # or '/dev/ttyAMA0' for GPIO serial
BAUD_RATE = 9600
DEVICE_ADDRESS = 1
MODBUS_METHOD = 'rtu'  # or 'ascii'

# Web Server Settings
WEB_PORT = 5000
DEBUG = False

# GPIO Settings (Raspberry Pi specific)
GPIO_AVAILABLE = True
```

## Hardware Connections

### USB-to-Serial (Recommended)
- Connect USB adapter to Raspberry Pi
- Wire adapter TX to PLC RX
- Wire adapter RX to PLC TX
- Connect common ground
- Update `SERIAL_PORT` to `/dev/ttyUSB0`

### GPIO Serial (Advanced)
- GPIO 14 (TX) to PLC RX
- GPIO 15 (RX) to PLC TX
- Ground connection
- Update `SERIAL_PORT` to `/dev/ttyAMA0`
- Disable console on serial: `sudo raspi-config`

## Service Management

### Start/Stop Service
```bash
sudo systemctl start plc-bridge
sudo systemctl stop plc-bridge
sudo systemctl restart plc-bridge
```

### Check Status
```bash
sudo systemctl status plc-bridge
journalctl -u plc-bridge -f  # Live logs
```

### Enable/Disable Auto-start
```bash
sudo systemctl enable plc-bridge   # Start on boot
sudo systemctl disable plc-bridge  # Disable auto-start
```

## Web Interface

Access the web interface at:
- `http://[PI_IP_ADDRESS]:5000`
- `http://localhost:5000` (local access)

### Main Dashboard
- Real-time PLC data display
- Digital inputs/outputs status
- Data registers monitoring
- Connection status indicators

### Custom Scripts Page
- Create and edit automation scripts
- Enable/disable individual scripts
- View execution results and GPIO states
- Built-in help and examples

## Custom Scripts

The system includes a powerful scripting engine for automation:

### Built-in Examples
- **Status LED Control**: Visual connection indicators
- **Emergency Stop Monitor**: Safety system integration
- **Temperature Alarms**: Threshold monitoring with GPIO outputs
- **Data Logging**: Custom data collection and storage

### Script Development
Scripts have access to:
- PLC data (inputs, outputs, registers)
- GPIO control functions
- PLC write operations (coils and registers)
- Python standard library

Example script:
```python
# Temperature monitoring with alarm
temp_value = plc_data.get('data_registers', {}).get(1, 0)
if temp_value > 750:  # 75.0°C
    gpio.set_pin(18, True)  # Activate alarm LED
    write_coil(10, True)    # Set PLC alarm bit
```

## GPIO Pin Assignments

Default GPIO usage (configurable in scripts):
- **GPIO 18**: Status LED
- **GPIO 19**: Alarm output
- **GPIO 20**: General purpose output 1
- **GPIO 21**: General purpose output 2

Reserve GPIO 14/15 for serial communication if using GPIO serial.

## Troubleshooting

### Service Won't Start
```bash
# Check service status
sudo systemctl status plc-bridge

# View detailed logs
journalctl -u plc-bridge -n 50

# Test manually
source venv/bin/activate
python main.py
```

### Serial Port Issues
```bash
# Check available ports
ls -la /dev/tty*

# Verify user permissions
groups $USER  # Should include 'dialout'

# Test serial connection
sudo minicom -D /dev/ttyUSB0 -b 9600
```

### PLC Communication Problems
1. Verify wiring connections
2. Check PLC Modbus settings
3. Confirm baud rate and device address
4. Test with PLC software first
5. Check for ground loops

### Web Interface Not Accessible
```bash
# Check if service is running
sudo systemctl status plc-bridge

# Verify port is open
sudo netstat -tlnp | grep :5000

# Check firewall settings
sudo ufw status
```

## File Structure

```
RaspberryPi/
├── main.py                 # Main application entry point
├── config.py              # Configuration settings
├── plc_communication.py   # PLC interface module
├── web_server.py          # Flask web server
├── custom_scripts.py      # Script engine and GPIO control
├── requirements.txt       # Python dependencies
├── install.sh            # Automated installation script
├── README.md             # This file
├── static/               # Web assets (CSS, JavaScript)
├── templates/            # HTML templates
└── venv/                 # Virtual environment (created by install)
```

## Performance Optimization

### For Industrial Use
- Set `DEBUG = False` in config.py
- Use wired Ethernet connection
- Configure log rotation
- Monitor system resources

### Memory Management
- Default poll interval: 1 second
- Adjust based on requirements
- Monitor with `htop` or `systemctl status`

## Security Considerations

- Change default web port if needed
- Use firewall rules to restrict access
- Regular system updates
- Secure physical access to Raspberry Pi
- Consider VPN for remote access

## Support and Updates

The system logs all activities to:
- Application log: `plc_web_bridge.log`
- System log: `journalctl -u plc-bridge`

For updates, replace files and restart the service:
```bash
sudo systemctl restart plc-bridge
```

## License

This software is provided for industrial automation applications. Ensure compliance with your local safety regulations and standards.