# ESP-32 Web Interface Troubleshooting Guide

## How the ESP-32 Web Interface Works

The ESP-32 runs a complete web server directly on the microcontroller. When it connects to your WiFi network, it hosts a web interface at its IP address on port 80.

### Expected Behavior:
1. ESP-32 connects to your WiFi network
2. Web server starts automatically on port 80
3. Access the interface at `http://[ESP32_IP_ADDRESS]` (no port number needed)
4. If WiFi connection fails, ESP-32 creates its own access point for configuration

## Finding Your ESP-32 IP Address

### Method 1: Serial Monitor
Connect to the ESP-32 via serial terminal and look for messages like:
```
[INFO] WiFi connected successfully
[INFO] IP address: 192.168.1.100
[INFO] PLC monitor started on http://192.168.1.100
```

### Method 2: Router Admin Panel
1. Log into your WiFi router's admin interface
2. Look for connected devices
3. Find device named "ESP32" or with MAC starting with ESP32 prefix

### Method 3: Network Scanner
Use a network scanning tool like:
- `nmap -sn 192.168.1.0/24` (Linux/Mac)
- Advanced IP Scanner (Windows)
- Fing mobile app

## Common Issues and Solutions

### Issue 1: ESP-32 Connects to WiFi but Web Interface Not Accessible

**Symptoms:**
- ESP-32 shows WiFi connected in serial output
- Cannot access web interface at ESP-32 IP address

**Solutions:**
1. **Check the correct URL format:**
   - Correct: `http://192.168.1.100` (no port number)
   - Incorrect: `http://192.168.1.100:5000` (ESP-32 uses port 80)

2. **Verify ESP-32 is actually connected:**
   ```
   # From serial monitor, look for:
   [INFO] WiFi connected successfully
   [INFO] IP address: X.X.X.X
   [INFO] PLC monitor started on http://X.X.X.X
   ```

3. **Test basic connectivity:**
   - Ping the ESP-32 IP: `ping 192.168.1.100`
   - If ping fails, there's a network connectivity issue

4. **Check firewall settings:**
   - Temporarily disable computer firewall
   - Check router firewall settings

### Issue 2: ESP-32 Won't Connect to WiFi

**Symptoms:**
- ESP-32 creates access point "ESP32-PLC-Setup"
- Never connects to your WiFi network

**Solutions:**
1. **Check WiFi credentials in config.py:**
   ```python
   WIFI_SSID = "YourActualNetworkName"
   WIFI_PASSWORD = "YourActualPassword"
   ```

2. **Common WiFi issues:**
   - WiFi network is 5GHz only (ESP-32 needs 2.4GHz)
   - Special characters in password
   - Hidden network (ESP-32 may have trouble)
   - WPA3 encryption (try WPA2)

3. **Use the configuration portal:**
   - Connect to "ESP32-PLC-Setup" WiFi
   - Go to `http://192.168.4.1`
   - Configure WiFi through web interface

### Issue 3: Web Server Starts but Pages Don't Load

**Symptoms:**
- Can ping ESP-32 IP address
- Browser times out or shows connection refused

**Solutions:**
1. **Check web server startup in serial output:**
   ```
   [INFO] PLC monitor started on http://X.X.X.X
   ```

2. **Memory issues:**
   - ESP-32 may be running out of memory
   - Look for memory-related errors in serial output

3. **Try different browsers or devices:**
   - Test from phone, tablet, different computer
   - Clear browser cache

## Step-by-Step Debugging Process

### Step 1: Verify Hardware Setup
1. ESP-32 is powered and running
2. Status LED shows connection status:
   - Steady ON = Connected to WiFi
   - Slow blink = Access Point mode
   - Fast blink = Trying to connect

### Step 2: Check Serial Output
Connect via serial terminal (115200 baud) and look for:
```
[INFO] WiFi connecting to: YourNetworkName
[INFO] WiFi connected successfully
[INFO] IP address: 192.168.1.100
[INFO] PLC monitor started on http://192.168.1.100
```

### Step 3: Test Network Connectivity
```bash
# Test if ESP-32 is reachable
ping 192.168.1.100

# Test if port 80 is open
telnet 192.168.1.100 80
# or
nc -zv 192.168.1.100 80
```

### Step 4: Access Web Interface
1. Open browser to `http://[ESP32_IP]`
2. Should see PLC monitoring interface
3. If it loads, you're successfully connected!

## WiFi Configuration Portal

If the ESP-32 can't connect to your WiFi, it automatically creates an access point:

1. **Connect to ESP-32 Access Point:**
   - Network: "ESP32-PLC-Setup"
   - Password: "plcsetup123"

2. **Open Configuration Portal:**
   - Go to: `http://192.168.4.1`
   - You'll see available WiFi networks
   - Select your network and enter password

3. **ESP-32 will restart and connect to your WiFi**

## Advanced Troubleshooting

### Check ESP-32 Web Server Code
The web server runs on port 80 and handles these endpoints:
- `/` - Main PLC monitoring page
- `/api/status` - JSON data endpoint
- `/config` - WiFi configuration (AP mode only)

### Memory Management
ESP-32 has limited memory. If experiencing issues:
1. Restart the ESP-32
2. Check for memory leaks in serial output
3. Consider reducing poll interval in config.py

### Network Isolation
Some networks isolate devices:
1. Try connecting from same network segment
2. Check router AP isolation settings
3. Test with mobile hotspot

## Getting Help

### Information to Collect:
1. ESP-32 serial output during startup
2. Your WiFi network type (WPA2, frequency)
3. ESP-32 IP address (if it gets one)
4. Error messages from browser
5. Network topology (router model, etc.)

### Serial Output Example (Successful):
```
[INFO] ESP-32 PLC Bridge Starting
[INFO] WiFi connecting to: MyNetwork
[INFO] WiFi connected successfully
[INFO] IP address: 192.168.1.100
[INFO] Starting web server
[INFO] PLC monitor started on http://192.168.1.100
[INFO] Free memory: 45672 bytes
```

The key point is that **the ESP-32 runs everything locally** - no Raspberry Pi needed. Once connected to WiFi, access the web interface directly at the ESP-32's IP address.