# ESP-32 PLC Bridge with WiFi AP Fallback

This folder contains all files for your ESP-32 PLC monitoring system with automatic WiFi Access Point fallback. The system automatically creates a configuration portal when WiFi connection fails.

## Required Files (Upload in Order)

1. **boot.py** - System startup script (upload first)
2. **config.py** - Configuration settings (edit before upload)
3. **main.py** - Main application with AP fallback
4. **wifi_debug.py** - AP setup instructions and reference

## Key Features

### Automatic WiFi Fallback
- Tries to connect to configured WiFi network
- Falls back to Access Point mode if connection fails
- Provides web-based WiFi configuration portal
- Automatically switches back to station mode when connected

### LED Status Indicators
- **Steady ON:** Connected to WiFi (station mode)
- **Slow blink:** Access Point mode active
- **Fast double blink:** WiFi disconnected, attempting reconnection

## Setup Instructions

### 1. Flash MicroPython Firmware
```bash
# Install esptool
pip install esptool

# Erase flash
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash

# Flash firmware (recommended: v1.22.2)
esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 ESP32_GENERIC-20240602-v1.22.2.bin
```

### 2. Edit Configuration
**IMPORTANT: Edit `config.py` before uploading**

```python
# WiFi Settings (optional - can configure via AP mode)
WIFI_SSID = "YourNetworkName"
WIFI_PASSWORD = "YourNetworkPassword"

# Access Point Settings (customize if needed)
AP_SSID = "ESP32-PLC-Setup"
AP_PASSWORD = "plcsetup123"

# PLC Settings
BAUD_RATE = 9600  # Match your PLC
DEVICE_ADDRESS = 1  # Modbus slave address
```

### 3. Upload Files
**Important: The ESP-32 now includes a 5-second boot delay that allows interrupting the startup to upload new files.**

Using **Thonny IDE** (recommended):
1. Install Thonny from https://thonny.org/
2. Go to Tools → Options → Interpreter
3. Select "MicroPython (ESP-32)"
4. Choose your ESP-32 port
5. Upload files: boot.py, config.py, main.py, custom_scripts.py, wifi_debug.py

**Boot Delay Feature:**
- After powering on or resetting, the ESP-32 displays a 5-second countdown
- Press Ctrl+C during countdown to interrupt boot and upload files
- LED blinks during countdown, stays solid when in upload mode
- Press EN/RST button to resume normal operation

Using **ampy** (command line):
```bash
pip install adafruit-ampy
# ESP-32 will show countdown - press Ctrl+C to interrupt if needed
ampy --port /dev/ttyUSB0 put boot.py
ampy --port /dev/ttyUSB0 put config.py
ampy --port /dev/ttyUSB0 put main.py
ampy --port /dev/ttyUSB0 put custom_scripts.py
ampy --port /dev/ttyUSB0 put wifi_debug.py
```

### 4. WiFi Configuration

#### Option A: Pre-configure (Traditional)
Edit WIFI_SSID and WIFI_PASSWORD in config.py before uploading.

#### Option B: Use Access Point (Recommended)
1. Leave default values in config.py
2. Upload files and power on ESP-32
3. Connect to "ESP32-PLC-Setup" WiFi network (password: plcsetup123)
4. Open browser and go to http://192.168.4.1
5. Select your WiFi network from the scan results
6. Enter password and click "Connect to WiFi"
7. ESP-32 automatically switches to station mode

### 5. Hardware Connections

#### Method 1: Direct Serial (Simple)
```
ESP-32 Pin → PLC Port
GPIO17 (TX) → RX
GPIO16 (RX) → TX
GND        → GND
```

#### Method 2: RS-485 (Industrial)
```
ESP-32 → MAX485 → PLC
GPIO17 → DI      
GPIO16 → RO      
3.3V   → VCC     
GND    → GND     
         A ←----→ A (Terminal +)
         B ←----→ B (Terminal -)
```

### 6. PLC Configuration
Set your AutomationDirect CLICK PLC to:
- **Protocol:** Modbus RTU
- **Baud Rate:** 9600 (match config.py)
- **Data Bits:** 8
- **Parity:** None
- **Stop Bits:** 1
- **Slave Address:** 1 (match config.py)

## WiFi Configuration Portal

When in Access Point mode, the configuration portal provides:

### Network Scanner
- Lists all available WiFi networks
- Shows signal strength indicators
- Displays security status (locked/unlocked icons)
- Sorts networks by signal strength

### Easy Configuration
- Click network to select
- Password field appears automatically for secured networks
- Real-time connection feedback
- Automatic redirect to normal operation

### Portal Features
- Responsive design for mobile devices
- Network refresh capability
- Connection status monitoring
- Error messages for failed connections

## Web Interface

### Station Mode (Normal Operation)
- **URL:** `http://[ESP-32-IP-Address]`
- Real-time PLC data display
- System status monitoring
- WiFi configuration button (opens portal in new tab)

### Access Point Mode (Configuration)
- **URL:** `http://192.168.4.1`
- WiFi network selection
- Password entry
- Connection testing

### API Endpoints
- `/api/status` - JSON status data
- `/api/networks` - Available WiFi networks
- `/config` - Configuration portal
- `/connect` - WiFi connection endpoint

## Troubleshooting

### Boot Delay and File Upload Issues
1. **Can't interrupt boot**: Ensure serial connection is active before powering on
2. **Boot delay not showing**: Check serial monitor is connected and configured correctly
3. **Files won't upload during delay**: Press Ctrl+C immediately when countdown starts
4. **Stuck in upload mode**: Press EN/RST button or power cycle to resume normal boot
5. **LED behavior**:
   - Blinking during countdown: Normal boot delay
   - Solid on: Upload mode active
   - Quick flashes: Normal startup sequence

### Access Point Not Visible
1. Verify ESP-32 is powered and running
2. Look for "ESP32-PLC-Setup" network
3. Check LED is blinking slowly (AP mode indicator)
4. Try restarting ESP-32

### Cannot Connect to Portal
1. Ensure connected to ESP32-PLC-Setup network
2. Try http://192.168.4.1 in browser
3. Clear browser cache
4. Try different browser or incognito mode

### WiFi Connection Fails
1. Verify password is correct
2. Check network security type compatibility
3. Ensure network is in range
4. Try restarting router

### PLC Communication Issues
1. Verify wiring connections
2. Check PLC Modbus settings
3. Confirm baud rate matches
4. Test with PLC software first

## Configuration Settings

### WiFi Access Point
```python
AP_SSID = "ESP32-PLC-Setup"      # Network name
AP_PASSWORD = "plcsetup123"       # Network password (8+ chars)
AP_CHANNEL = 1                    # WiFi channel
AP_MAX_CLIENTS = 4                # Max connected devices
```

### Hardware Pins
```python
UART_TX_PIN = 17     # GPIO17 - to PLC RX
UART_RX_PIN = 16     # GPIO16 - to PLC TX  
STATUS_LED_PIN = 2   # Built-in LED
UART_PORT = 2        # UART2
```

### Performance Tuning
```python
POLL_INTERVAL = 2.0      # Seconds between PLC polls
WEB_PORT = 80           # Web server port
WIFI_TIMEOUT = 15       # WiFi connection timeout
UART_TIMEOUT = 1000     # Modbus timeout (ms)
```

## Advanced Features

### Automatic Mode Switching
- Seamless transition between AP and station modes
- Preserves PLC connection during WiFi changes
- Background monitoring of WiFi status
- Automatic reconnection attempts

### Memory Management
- Garbage collection optimization
- Memory usage monitoring
- Efficient network scanning
- Resource cleanup on mode changes

### Custom Scripts System
- GPIO control for automation tasks
- User-programmable logic execution
- PLC data integration and manipulation
- Status LED control and alarm outputs
- Memory-efficient script execution
- Built-in safety and error handling

**Example Scripts Included:**
- Status LED blinker based on PLC connection
- Emergency stop monitor with safety outputs
- Temperature alarm with GPIO alerts
- Customizable automation workflows

### Error Recovery
- Automatic WiFi reconnection
- PLC communication retry logic
- Web server restart capability
- LED status indication for diagnostics

## Support

The system is designed for plug-and-play operation in industrial environments:

1. **Initial Setup:** Use Access Point mode for easy WiFi configuration
2. **Normal Operation:** Automatic station mode with PLC monitoring
3. **Troubleshooting:** LED indicators and web interface diagnostics
4. **Maintenance:** Remote configuration and monitoring capabilities

No USB connection or terminal access required for normal operation.