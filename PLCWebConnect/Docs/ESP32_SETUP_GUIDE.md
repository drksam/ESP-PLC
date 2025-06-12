# ESP-32 PLC Bridge Setup Guide

## Hardware Requirements

### ESP-32 Development Board
- Any ESP-32 development board (NodeMCU-32S, WROOM-32, etc.)
- USB cable for programming
- Breadboard or PCB for connections

### PLC Connection Hardware
- RS-485 to TTL converter module (MAX485 or similar)
- OR USB-to-Serial adapter (if PLC supports direct serial)
- Jumper wires
- 120Ω termination resistor (for RS-485)

## Wiring Connections

### Method 1: RS-485 Connection (Recommended for industrial use)
```
ESP-32          MAX485 Module       AutomationDirect CLICK PLC
GPIO17 (TX) --> DI (Data Input)     
GPIO16 (RX) --> RO (Receiver Out)   
GPIO5       --> RE/DE (Control)     
3.3V        --> VCC                 
GND         --> GND                 
                A   <-------------> A (Terminal +)
                B   <-------------> B (Terminal -)
```

### Method 2: Direct Serial Connection (if PLC supports)
```
ESP-32          PLC Serial Port
GPIO17 (TX) --> RX
GPIO16 (RX) --> TX
GND         --> GND
```

## Software Setup

### 1. Install MicroPython on ESP-32
1. Download latest MicroPython firmware from https://micropython.org/download/esp32/
2. Install esptool: `pip install esptool`
3. Erase flash: `esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash`
4. Flash MicroPython: `esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 esp32-*.bin`

### 2. Upload Code Files
Use a tool like Thonny, ampy, or rshell to upload these files to your ESP-32:

**Required Files:**
- `boot.py` (from esp32_boot.py)
- `main.py` (from esp32_main.py)
- `config.py` (from esp32_config.py)

### 3. Configure WiFi and PLC Settings
Edit the configuration in `esp32_config.py`:

```python
# WiFi Settings
WIFI_SSID = "YourWiFiNetwork"
WIFI_PASSWORD = "YourWiFiPassword"

# PLC Settings
BAUD_RATE = 9600  # Match your PLC settings
DEVICE_ADDRESS = 1  # Modbus slave address
```

## PLC Configuration

### AutomationDirect CLICK PLC Settings
1. **Communication Port Setup:**
   - Baud Rate: 9600 (or match ESP-32 config)
   - Data Bits: 8
   - Parity: None
   - Stop Bits: 1
   - Protocol: Modbus RTU

2. **Modbus Slave Configuration:**
   - Enable Modbus Slave mode
   - Set Slave Address (default: 1)
   - Configure data mapping:
     - Coils (Y): Digital outputs
     - Discrete Inputs (X): Digital inputs
     - Holding Registers (DS): Data storage

## Operation

### Starting the System
1. Power on ESP-32
2. LED will blink during WiFi connection
3. LED stays on when connected
4. Access web interface at ESP-32's IP address

### Web Interface Features
- **Real-time PLC data display**
- **Digital I/O status monitoring**
- **Data register values**
- **Connection status indicators**
- **Mobile-friendly responsive design**

### API Endpoints
- `GET /` - Web interface
- `GET /api/status` - JSON data API

### Memory Management
- Automatic garbage collection
- Optimized for ESP-32's limited RAM
- Efficient data structures for PLC data

## Troubleshooting

### WiFi Connection Issues
- Verify SSID and password
- Check WiFi signal strength
- Monitor LED blinking pattern

### PLC Communication Problems
- Verify wiring connections
- Check baud rate matching
- Confirm Modbus slave address
- Test with PLC programming software first

### Memory Issues
- Restart ESP-32 if memory errors occur
- Monitor free memory in web interface
- Reduce poll interval if needed

### Performance Optimization
- Adjust `POLL_INTERVAL` in config
- Use appropriate UART timeout values
- Enable only required PLC data points

## Advanced Configuration

### Custom Data Mapping
Modify the polling functions to read specific PLC addresses:

```python
# Read specific input range
inputs = self.modbus.read_discrete_inputs(slave_id, start_addr, count)

# Read specific register range  
registers = self.modbus.read_holding_registers(slave_id, start_addr, count)
```

### Adding Write Functionality
Extend the web interface to include write capabilities:
- Coil writing (digital outputs)
- Register writing (analog outputs)
- Form-based control interface

### Security Considerations
- Change default WiFi credentials
- Use WPA2/WPA3 encryption
- Consider VPN for remote access
- Implement authentication if needed

## Production Deployment

### Enclosure Requirements
- IP-rated enclosure for industrial environment
- Proper ventilation for ESP-32
- DIN rail mounting options
- Cable strain relief

### Power Supply
- 5V/3.3V regulated supply
- Isolation from PLC power systems
- Backup power consideration
- EMI/EMC compliance

### Maintenance
- Regular firmware updates
- Monitor memory usage
- Log communication errors
- Backup configuration files

## Support and Resources

### Documentation
- ESP-32 MicroPython docs: https://docs.micropython.org/en/latest/esp32/
- AutomationDirect manuals: https://www.automationdirect.com/
- Modbus specification: https://modbus.org/

### Development Tools
- Thonny IDE (recommended for beginners)
- VS Code with MicroPython extensions
- ampy for file transfer
- PuTTY/screen for serial monitoring