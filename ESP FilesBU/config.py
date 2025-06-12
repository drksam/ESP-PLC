"""
ESP-32 Configuration file
Edit these settings for your specific setup before uploading
"""

# WiFi Settings - EDIT THESE VALUES
WIFI_SSID = "Nooyen BrkRoom"
WIFI_PASSWORD = "pigfloors"

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
WIFI_TIMEOUT = 20  # seconds
RESPONSE_TIMEOUT = 100  # milliseconds for Modbus responses