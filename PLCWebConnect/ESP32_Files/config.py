"""
ESP-32 Configuration file
Edit these settings for your specific setup before uploading
"""

# WiFi Settings - EDIT THESE VALUES
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# Access Point Settings (fallback when WiFi fails)
AP_SSID = "ESP32-PLC-Setup"
AP_PASSWORD = "plcsetup123"  # At least 8 characters
AP_CHANNEL = 1
AP_MAX_CLIENTS = 4

# Hardware Pin Configuration
UART_TX_PIN = 17  # GPIO17 - Connect to PLC RX
UART_RX_PIN = 16  # GPIO16 - Connect to PLC TX
STATUS_LED_PIN = 2  # Built-in LED
UART_PORT = 2  # Use UART2

# PLC Communication Settings
BAUD_RATE = 9600  # Match your PLC settings
DEVICE_ADDRESS = 1  # Modbus slave address of PLC
UART_TIMEOUT = 1000  # milliseconds

# Web Server Settings
WEB_PORT = 80
POLL_INTERVAL = 2.0  # seconds between PLC polls

# System Settings
MAX_RETRIES = 3
WIFI_TIMEOUT = 15  # seconds to try connecting to WiFi
RESPONSE_TIMEOUT = 100  # milliseconds for Modbus responses

# Access Point Network Configuration
AP_IP = "192.168.4.1"
AP_SUBNET = "255.255.255.0"
AP_GATEWAY = "192.168.4.1"
AP_DNS = "192.168.4.1"