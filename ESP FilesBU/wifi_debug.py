"""
Access Point Setup Instructions for ESP-32 PLC Bridge
This file explains how to use the AP fallback feature
"""

# The ESP-32 PLC Bridge now has automatic WiFi Access Point fallback mode.
# When it cannot connect to the configured WiFi network, it automatically
# creates its own WiFi Access Point for configuration.

# HOW IT WORKS:
# 1. ESP-32 tries to connect to WIFI_SSID from config.py
# 2. If connection fails, it starts an Access Point
# 3. Connect to the AP with your phone/computer
# 4. Visit the configuration portal to select a network
# 5. ESP-32 switches to normal WiFi mode once connected

# ACCESS POINT DETAILS:
# - Network Name: ESP32-PLC-Setup (configurable in config.py)
# - Password: plcsetup123 (configurable in config.py)
# - IP Address: 192.168.4.1
# - Configuration URL: http://192.168.4.1

# LED STATUS INDICATORS:
# - Steady ON: Connected to WiFi in station mode
# - Slow blink (every 2 seconds): Access Point mode active
# - Fast double blink: WiFi disconnected, attempting reconnection

# TO CONFIGURE WIFI:
# 1. Connect your device to "ESP32-PLC-Setup" WiFi network
# 2. Open web browser and go to http://192.168.4.1
# 3. Select your WiFi network from the list
# 4. Enter the password if required
# 5. Click "Connect to WiFi"
# 6. ESP-32 will switch to station mode and connect

# The configuration portal includes:
# - Network scanner showing available WiFi networks
# - Signal strength indicators
# - Security type indicators (locked/unlocked icons)
# - Real-time connection status
# - Automatic redirect once connected

print("Access Point mode is built into main.py - no separate debug needed")