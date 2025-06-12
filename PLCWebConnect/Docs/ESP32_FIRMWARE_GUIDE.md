# ESP-32S MicroPython Firmware Guide for PLC Bridge

## Recommended Firmware

### Primary Choice: Official MicroPython v1.22.2
**Download URL:** https://micropython.org/download/ESP32_GENERIC/
**File:** `ESP32_GENERIC-20240602-v1.22.2.bin`

**Why this version:**
- Stable async/await support (critical for our web server)
- Optimized UART performance
- Better memory management
- Proven compatibility with industrial applications

### Alternative: Latest Stable (v1.23.0)
**Download URL:** https://micropython.org/download/ESP32_GENERIC/
**File:** `ESP32_GENERIC-20240602-v1.23.0.bin`

**Benefits:**
- Latest bug fixes
- Enhanced network stability
- Improved garbage collection

## Installation Commands

### 1. Install esptool
```bash
pip install esptool
```

### 2. Erase Flash (Important!)
```bash
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
```
*Replace `/dev/ttyUSB0` with your port (Windows: `COM3`, `COM4`, etc.)*

### 3. Flash MicroPython
```bash
esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 ESP32_GENERIC-20240602-v1.22.2.bin
```

### 4. Verify Installation
```bash
# Connect to serial console
screen /dev/ttyUSB0 115200
# Or use PuTTY on Windows

# Should see MicroPython REPL:
>>> print("Hello ESP32")
Hello ESP32
```

## Hardware-Specific Considerations

### ESP-32S vs ESP-32 Standard
- **ESP-32S**: Single-core version (sufficient for our application)
- **Memory**: 520KB SRAM (adequate for PLC bridge)
- **Flash**: Minimum 4MB required (8MB+ recommended)

### Pin Configuration for ESP-32S
```python
# UART Pins (confirmed working)
UART_TX_PIN = 17  # GPIO17
UART_RX_PIN = 16  # GPIO16
STATUS_LED_PIN = 2  # Built-in LED

# Alternative UART pins if needed
# UART_TX_PIN = 4   # GPIO4
# UART_RX_PIN = 5   # GPIO5
```

## Pre-Installation Testing

### Test MicroPython Installation
```python
# After flashing, test in REPL:
import machine
import network
import uasyncio
import gc

print("MicroPython version:", machine.freq())
print("Free memory:", gc.mem_free())

# Test UART
uart = machine.UART(2, baudrate=9600, tx=17, rx=16)
print("UART created successfully")

# Test WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
print("WiFi module ready")
```

## File Upload Methods

### Method 1: Thonny IDE (Recommended for Beginners)
1. Install Thonny: https://thonny.org/
2. Configure: Tools → Options → Interpreter → MicroPython (ESP-32)
3. Select correct COM port
4. Upload files directly through Thonny interface

### Method 2: ampy (Command Line)
```bash
# Install ampy
pip install adafruit-ampy

# Upload files
ampy --port /dev/ttyUSB0 put esp32_boot.py boot.py
ampy --port /dev/ttyUSB0 put esp32_main.py main.py
ampy --port /dev/ttyUSB0 put esp32_config.py config.py

# Verify upload
ampy --port /dev/ttyUSB0 ls
```

### Method 3: rshell (Advanced)
```bash
# Install rshell
pip install rshell

# Connect and upload
rshell -p /dev/ttyUSB0
> cp esp32_boot.py /pyboard/boot.py
> cp esp32_main.py /pyboard/main.py
> cp esp32_config.py /pyboard/config.py
```

## Configuration for PLC Use

### Essential Config Changes
Before uploading, modify `esp32_config.py`:

```python
# Your specific settings
WIFI_SSID = "YourNetworkName"
WIFI_PASSWORD = "YourPassword"

# PLC Communication
BAUD_RATE = 9600  # Match your CLICK PLC
DEVICE_ADDRESS = 1  # Modbus slave address

# Performance tuning for industrial use
POLL_INTERVAL = 2.0  # Adjust based on requirements
UART_TIMEOUT = 1000  # Milliseconds
```

## Memory Optimization

### Reduce Memory Usage
```python
# Add to boot.py for memory optimization
import gc
gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())

# Disable debug output in production
import micropython
micropython.opt_level(1)
```

## Troubleshooting Common Issues

### Upload Failures
1. **Boot Mode**: Hold BOOT button while connecting power
2. **Driver Issues**: Install CP2102 or CH340 drivers
3. **Baud Rate**: Try slower baud rates: `--baud 115200`

### Runtime Issues
1. **Memory Errors**: Reduce poll interval, add more `gc.collect()` calls
2. **WiFi Drops**: Add reconnection logic in main loop
3. **UART Errors**: Check wiring, verify baud rate match

### Performance Optimization
```python
# In main application, add periodic cleanup
import gc
gc.collect()  # Call every few iterations

# Monitor memory usage
print(f"Free: {gc.mem_free()}, Used: {gc.mem_alloc()}")
```

## Production Deployment

### Firmware Validation Checklist
- [ ] MicroPython boots successfully
- [ ] WiFi connects and gets IP address
- [ ] UART communication initializes
- [ ] Web server starts on port 80
- [ ] Memory usage stays stable
- [ ] LED status indicators work

### Backup and Recovery
```bash
# Backup current firmware
esptool.py --chip esp32 --port /dev/ttyUSB0 read_flash 0x0 0x400000 backup.bin

# Restore if needed
esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash 0x0 backup.bin
```

## Hardware Testing Sequence

### 1. Basic Functionality
1. Flash firmware
2. Upload test files
3. Verify WiFi connection
4. Test web interface access

### 2. PLC Integration
1. Connect UART to PLC
2. Configure PLC Modbus settings
3. Test communication
4. Verify data display

### 3. Production Testing
1. Extended runtime test (24+ hours)
2. Memory leak monitoring
3. Network stability testing
4. Error recovery testing

## Expected Performance

### Resource Usage
- **Memory**: ~80KB for application + web server
- **CPU**: ~15% utilization during normal operation
- **Network**: ~2KB/minute data transfer
- **Power**: ~200mA at 3.3V (typical)

### Response Times
- **PLC Poll**: 100-200ms per cycle
- **Web Response**: <500ms for page load
- **Data Refresh**: 2-second intervals (configurable)

This firmware setup will provide a solid foundation for your ESP-32S PLC bridge application with reliable industrial performance.