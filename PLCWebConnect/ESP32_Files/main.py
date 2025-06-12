"""
ESP-32 MicroPython PLC Bridge with WiFi AP Fallback
Features automatic fallback to Access Point mode with captive portal
"""

import network
import socket
import json
import time
import machine
import gc
from machine import UART, Pin
import ujson
import uasyncio as asyncio
import sys
from config import *
try:
    from custom_scripts import create_script_engine
    SCRIPTS_AVAILABLE = True
except ImportError:
    SCRIPTS_AVAILABLE = False
    print_log("Custom scripts not available", "WARNING")

# Operating modes
MODE_STA = "STA"  # Station mode (connected to WiFi)
MODE_AP = "AP"    # Access Point mode (configuration portal)

def print_log(message, level="INFO"):
    """Simple logging without dependencies"""
    print(f"[{level}] {message}")

def blink_pattern(led, count=1, on_time=200, off_time=200):
    """LED blink pattern for status indication"""
    for _ in range(count):
        led.on()
        time.sleep_ms(on_time)
        led.off()
        time.sleep_ms(off_time)

class ModbusRTU:
    """Simplified Modbus RTU implementation"""
    
    def __init__(self, uart):
        self.uart = uart
        
    def crc16(self, data):
        """Calculate Modbus CRC16"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc
    
    def build_request(self, slave_id, function_code, start_addr, count):
        """Build Modbus RTU request"""
        request = bytearray([slave_id, function_code])
        request.extend(start_addr.to_bytes(2, 'big'))
        request.extend(count.to_bytes(2, 'big'))
        
        crc = self.crc16(request)
        request.extend(crc.to_bytes(2, 'little'))
        return request
    
    def read_coils(self, slave_id, start_addr, count):
        """Read coils (function code 1)"""
        try:
            request = self.build_request(slave_id, 0x01, start_addr, count)
            self.uart.write(request)
            time.sleep_ms(100)
            
            response = self.uart.read()
            if response and len(response) >= 5:
                if response[0] == slave_id and response[1] == 0x01:
                    byte_count = response[2]
                    data_bytes = response[3:3+byte_count]
                    
                    bits = []
                    for byte_val in data_bytes:
                        for i in range(8):
                            if len(bits) < count:
                                bits.append(bool(byte_val & (1 << i)))
                    return bits[:count]
            return None
        except Exception as e:
            print_log(f"Error reading coils: {e}", "ERROR")
            return None
    
    def read_discrete_inputs(self, slave_id, start_addr, count):
        """Read discrete inputs (function code 2)"""
        try:
            request = self.build_request(slave_id, 0x02, start_addr, count)
            self.uart.write(request)
            time.sleep_ms(100)
            
            response = self.uart.read()
            if response and len(response) >= 5:
                if response[0] == slave_id and response[1] == 0x02:
                    byte_count = response[2]
                    data_bytes = response[3:3+byte_count]
                    
                    bits = []
                    for byte_val in data_bytes:
                        for i in range(8):
                            if len(bits) < count:
                                bits.append(bool(byte_val & (1 << i)))
                    return bits[:count]
            return None
        except Exception as e:
            print_log(f"Error reading inputs: {e}", "ERROR")
            return None
    
    def read_holding_registers(self, slave_id, start_addr, count):
        """Read holding registers (function code 3)"""
        try:
            request = self.build_request(slave_id, 0x03, start_addr, count)
            self.uart.write(request)
            time.sleep_ms(100)
            
            response = self.uart.read()
            if response and len(response) >= 5:
                if response[0] == slave_id and response[1] == 0x03:
                    byte_count = response[2]
                    if len(response) >= 3 + byte_count + 2:
                        registers = []
                        for i in range(0, byte_count, 2):
                            reg_val = (response[3+i] << 8) | response[3+i+1]
                            registers.append(reg_val)
                        return registers
            return None
        except Exception as e:
            print_log(f"Error reading registers: {e}", "ERROR")
            return None

class ESP32PLCBridge:
    """Main ESP-32 PLC Bridge class with AP fallback"""
    
    def __init__(self):
        self.status_led = Pin(STATUS_LED_PIN, Pin.OUT)
        self.operating_mode = MODE_STA
        self.wifi_credentials = None
        
        # Network interfaces
        self.sta_if = network.WLAN(network.STA_IF)
        self.ap_if = network.WLAN(network.AP_IF)
        
        # Initialize UART for PLC communication
        try:
            self.uart = UART(
                UART_PORT,
                baudrate=BAUD_RATE,
                tx=UART_TX_PIN,
                rx=UART_RX_PIN,
                timeout=UART_TIMEOUT
            )
            self.modbus = ModbusRTU(self.uart)
            print_log("UART initialized successfully")
        except Exception as e:
            print_log(f"UART initialization failed: {e}", "ERROR")
            self.uart = None
            self.modbus = None
        
        # PLC data storage
        self.plc_data = {
            'connected': False,
            'last_update': 0,
            'communication_errors': 0,
            'digital_inputs': {},
            'digital_outputs': {},
            'input_status': {},
            'coil_status': {},
            'data_registers': {},
            'system_info': {
                'device': 'ESP-32 PLC Bridge',
                'plc_model': 'AutomationDirect CLICK',
                'mode': self.operating_mode,
                'uart_port': UART_PORT,
                'baud_rate': BAUD_RATE
            }
        }
        
        # Initialize script engine if available
        self.script_engine = None
        if SCRIPTS_AVAILABLE:
            try:
                self.script_engine = create_script_engine(self.modbus)
                print_log("Custom scripts initialized", "INFO")
            except Exception as e:
                print_log(f"Script engine init failed: {e}", "ERROR")
        
        self.running = False
    
    def try_wifi_connection(self):
        """Attempt to connect to configured WiFi"""
        if WIFI_SSID == "YOUR_WIFI_SSID" or not WIFI_SSID:
            print_log("No WiFi credentials configured", "WARN")
            return False
        
        print_log(f"Attempting WiFi connection to {WIFI_SSID}")
        
        # Activate station interface
        self.sta_if.active(True)
        
        # Connect to network
        self.sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
        
        # Wait for connection
        timeout = WIFI_TIMEOUT
        while not self.sta_if.isconnected() and timeout > 0:
            blink_pattern(self.status_led, 1, 100, 100)
            time.sleep(1)
            timeout -= 1
        
        if self.sta_if.isconnected():
            ip_info = self.sta_if.ifconfig()
            print_log(f"WiFi connected! IP: {ip_info[0]}")
            self.operating_mode = MODE_STA
            self.plc_data['system_info']['mode'] = MODE_STA
            self.plc_data['system_info']['ip_address'] = ip_info[0]
            
            # Steady LED for successful connection
            self.status_led.on()
            return True
        else:
            print_log("WiFi connection failed", "WARN")
            return False
    
    def start_access_point(self):
        """Start Access Point mode for WiFi configuration"""
        print_log("Starting Access Point mode")
        
        # Deactivate station mode
        self.sta_if.active(False)
        
        # Configure and activate Access Point
        self.ap_if.active(True)
        self.ap_if.config(
            essid=AP_SSID,
            password=AP_PASSWORD,
            channel=AP_CHANNEL,
            max_clients=AP_MAX_CLIENTS
        )
        
        # Configure IP settings
        self.ap_if.ifconfig((AP_IP, AP_SUBNET, AP_GATEWAY, AP_DNS))
        
        self.operating_mode = MODE_AP
        self.plc_data['system_info']['mode'] = MODE_AP
        self.plc_data['system_info']['ip_address'] = AP_IP
        
        print_log(f"Access Point started: {AP_SSID}")
        print_log(f"Connect to {AP_SSID} and visit http://{AP_IP}")
        
        # Blinking LED pattern for AP mode
        blink_pattern(self.status_led, 3, 200, 200)
        return True
    
    def scan_networks(self):
        """Scan for available WiFi networks"""
        try:
            if not self.sta_if.active():
                self.sta_if.active(True)
                time.sleep(1)
            
            networks = self.sta_if.scan()
            network_list = []
            
            for net in networks:
                ssid = net[0].decode('utf-8')
                rssi = net[3]
                auth = net[4]
                
                # Filter out empty SSIDs and duplicates
                if ssid and not any(n['ssid'] == ssid for n in network_list):
                    network_list.append({
                        'ssid': ssid,
                        'rssi': rssi,
                        'auth': auth,
                        'secure': auth > 0
                    })
            
            # Sort by signal strength
            network_list.sort(key=lambda x: x['rssi'], reverse=True)
            return network_list[:20]  # Return top 20 networks
            
        except Exception as e:
            print_log(f"Network scan failed: {e}", "ERROR")
            return []
    
    def save_wifi_credentials(self, ssid, password):
        """Save WiFi credentials and attempt connection"""
        self.wifi_credentials = {'ssid': ssid, 'password': password}
        
        # Try connecting with new credentials
        print_log(f"Attempting connection to {ssid}")
        
        self.sta_if.active(True)
        self.sta_if.connect(ssid, password)
        
        # Wait for connection
        timeout = 15
        while not self.sta_if.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
        
        if self.sta_if.isconnected():
            print_log("New WiFi connection successful!")
            
            # Switch to station mode
            self.ap_if.active(False)
            self.operating_mode = MODE_STA
            
            ip_info = self.sta_if.ifconfig()
            self.plc_data['system_info']['mode'] = MODE_STA
            self.plc_data['system_info']['ip_address'] = ip_info[0]
            
            self.status_led.on()
            return True
        else:
            print_log("New WiFi connection failed", "ERROR")
            return False
    
    def poll_plc_data(self):
        """Poll data from PLC"""
        if not self.modbus:
            return False
            
        try:
            # Read digital inputs (X000-X015)
            inputs = self.modbus.read_discrete_inputs(DEVICE_ADDRESS, 0, 16)
            if inputs:
                self.plc_data['input_status'] = {
                    f'X{i:03d}': inputs[i] for i in range(len(inputs))
                }
                self.plc_data['digital_inputs'] = {
                    i+1: inputs[i] for i in range(len(inputs))
                }
                self.plc_data['connected'] = True
            
            # Read digital outputs/coils (Y000-Y015)
            coils = self.modbus.read_coils(DEVICE_ADDRESS, 0, 16)
            if coils:
                self.plc_data['coil_status'] = {
                    f'Y{i:03d}': coils[i] for i in range(len(coils))
                }
                self.plc_data['digital_outputs'] = {
                    i+1: coils[i] for i in range(len(coils))
                }
            
            # Read holding registers (DS001-DS010)
            registers = self.modbus.read_holding_registers(DEVICE_ADDRESS, 0, 10)
            if registers:
                self.plc_data['data_registers'] = {
                    f'DS{i+1:03d}': registers[i] for i in range(len(registers))
                }
                # Also provide numbered format for scripts
                for i, val in enumerate(registers):
                    self.plc_data['data_registers'][i+1] = val
            
            self.plc_data['last_update'] = time.time()
            
            # Execute custom scripts if available
            if self.script_engine and inputs:
                try:
                    script_results = self.script_engine.execute_enabled_scripts(self.plc_data)
                    self.plc_data['script_results'] = script_results
                except Exception as e:
                    print_log(f"Script execution error: {e}", "ERROR")
            
            if inputs or coils or registers:
                return True
            else:
                self.plc_data['communication_errors'] += 1
                return False
                
        except Exception as e:
            print_log(f"PLC polling error: {e}", "ERROR")
            self.plc_data['communication_errors'] += 1
            self.plc_data['connected'] = False
            return False
    
    def create_config_portal_html(self):
        """Create HTML for WiFi configuration portal"""
        networks = self.scan_networks()
        
        network_options = ""
        for net in networks:
            security = "🔒" if net['secure'] else "🔓"
            signal_bars = "📶" if net['rssi'] > -60 else "📶" if net['rssi'] > -70 else "📶"
            network_options += f'''
                <div class="network-item" onclick="selectNetwork('{net['ssid']}', {str(net['secure']).lower()})">
                    <div class="network-name">{security} {net['ssid']}</div>
                    <div class="network-signal">{signal_bars} {net['rssi']}dBm</div>
                </div>
            '''
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESP-32 PLC Bridge - WiFi Setup</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f0f0f0; }}
        .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{ color: #333; margin-bottom: 10px; }}
        .header p {{ color: #666; }}
        .section {{ margin-bottom: 25px; }}
        .section h3 {{ color: #333; margin-bottom: 15px; }}
        .network-list {{ max-height: 300px; overflow-y: auto; border: 1px solid #ddd; border-radius: 5px; }}
        .network-item {{ padding: 15px; border-bottom: 1px solid #eee; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }}
        .network-item:hover {{ background: #f8f9fa; }}
        .network-item.selected {{ background: #007bff; color: white; }}
        .network-name {{ font-weight: bold; }}
        .network-signal {{ font-size: 12px; color: #666; }}
        .network-item.selected .network-signal {{ color: #ccc; }}
        .form-group {{ margin-bottom: 15px; }}
        .form-group label {{ display: block; margin-bottom: 5px; font-weight: bold; color: #333; }}
        .form-group input {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }}
        .btn {{ background: #007bff; color: white; padding: 12px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%; }}
        .btn:hover {{ background: #0056b3; }}
        .btn:disabled {{ background: #ccc; cursor: not-allowed; }}
        .status {{ padding: 10px; margin: 15px 0; border-radius: 5px; text-align: center; }}
        .status.success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
        .status.error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        .hidden {{ display: none; }}
        .refresh-btn {{ background: #28a745; margin-bottom: 15px; }}
        .refresh-btn:hover {{ background: #218838; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 ESP-32 PLC Bridge</h1>
            <p>WiFi Configuration Portal</p>
        </div>
        
        <div class="section">
            <h3>📡 Available Networks</h3>
            <button class="btn refresh-btn" onclick="refreshNetworks()">🔄 Refresh Networks</button>
            <div class="network-list" id="networkList">
                {network_options}
            </div>
        </div>
        
        <div class="section">
            <h3>🔑 WiFi Credentials</h3>
            <form id="wifiForm" onsubmit="connectWifi(event)">
                <div class="form-group">
                    <label for="ssid">Network Name (SSID):</label>
                    <input type="text" id="ssid" name="ssid" required>
                </div>
                <div class="form-group" id="passwordGroup">
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password">
                </div>
                <button type="submit" class="btn" id="connectBtn">🔗 Connect to WiFi</button>
            </form>
        </div>
        
        <div id="status" class="status hidden"></div>
        
        <div class="section">
            <h3>ℹ️ Device Information</h3>
            <p><strong>Device:</strong> ESP-32 PLC Bridge</p>
            <p><strong>Access Point:</strong> {AP_SSID}</p>
            <p><strong>IP Address:</strong> {AP_IP}</p>
            <p><strong>Free Memory:</strong> {gc.mem_free()} bytes</p>
        </div>
    </div>
    
    <script>
        let selectedNetwork = null;
        
        function selectNetwork(ssid, secure) {{
            // Remove previous selection
            document.querySelectorAll('.network-item').forEach(item => {{
                item.classList.remove('selected');
            }});
            
            // Select clicked network
            event.currentTarget.classList.add('selected');
            selectedNetwork = {{ssid: ssid, secure: secure}};
            
            // Fill form
            document.getElementById('ssid').value = ssid;
            
            // Show/hide password field
            const passwordGroup = document.getElementById('passwordGroup');
            if (secure) {{
                passwordGroup.style.display = 'block';
                document.getElementById('password').required = true;
            }} else {{
                passwordGroup.style.display = 'none';
                document.getElementById('password').required = false;
                document.getElementById('password').value = '';
            }}
        }}
        
        function refreshNetworks() {{
            window.location.reload();
        }}
        
        function showStatus(message, type) {{
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = 'status ' + type;
            status.classList.remove('hidden');
        }}
        
        function connectWifi(event) {{
            event.preventDefault();
            
            const ssid = document.getElementById('ssid').value;
            const password = document.getElementById('password').value;
            const connectBtn = document.getElementById('connectBtn');
            
            if (!ssid) {{
                showStatus('Please select or enter a network name', 'error');
                return;
            }}
            
            connectBtn.disabled = true;
            connectBtn.textContent = '🔄 Connecting...';
            showStatus('Attempting to connect to ' + ssid + '...', 'info');
            
            fetch('/connect', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ssid: ssid, password: password}})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    showStatus('Connected successfully! Switching to station mode...', 'success');
                    setTimeout(() => {{
                        window.location.href = 'http://' + data.ip;
                    }}, 3000);
                }} else {{
                    showStatus('Connection failed: ' + data.error, 'error');
                    connectBtn.disabled = false;
                    connectBtn.textContent = '🔗 Connect to WiFi';
                }}
            }})
            .catch(error => {{
                showStatus('Connection error: ' + error, 'error');
                connectBtn.disabled = false;
                connectBtn.textContent = '🔗 Connect to WiFi';
            }});
        }}
    </script>
</body>
</html>'''
        return html
    
    def create_plc_monitor_html(self):
        """Create HTML for PLC monitoring interface"""
        # Digital inputs
        inputs_html = ""
        for i in range(16):
            addr = f'X{i:03d}'
            value = self.plc_data['input_status'].get(addr, False)
            class_name = "io-on" if value else "io-off"
            status = "ON" if value else "OFF"
            inputs_html += f'<div class="io-item {class_name}">{addr}<br>{status}</div>'
        
        # Digital outputs
        outputs_html = ""
        for i in range(16):
            addr = f'Y{i:03d}'
            value = self.plc_data['coil_status'].get(addr, False)
            class_name = "io-on" if value else "io-off"
            status = "ON" if value else "OFF"
            outputs_html += f'<div class="io-item {class_name}">{addr}<br>{status}</div>'
        
        # Data registers
        registers_html = ""
        for i in range(10):
            addr = f'DS{i+1:03d}'
            value = self.plc_data['data_registers'].get(addr, 0)
            registers_html += f'<div class="register-item"><strong>{addr}</strong><br>{value}</div>'
        
        # Status
        status_class = "connected" if self.plc_data['connected'] else "disconnected"
        connection_status = "Connected" if self.plc_data['connected'] else "Disconnected"
        
        # Last update
        last_update = self.plc_data['last_update']
        if last_update:
            update_str = f"{int(time.time() - last_update)}s ago"
        else:
            update_str = "Never"
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESP-32 PLC Monitor</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .header {{ background: #007bff; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; text-align: center; }}
        .mode-badge {{ background: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 15px; font-size: 12px; }}
        .status {{ display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }}
        .status-card {{ background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); flex: 1; min-width: 200px; text-align: center; }}
        .connected {{ color: #28a745; }}
        .disconnected {{ color: #dc3545; }}
        .data-section {{ background: white; padding: 20px; border-radius: 5px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .io-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 10px; margin-top: 15px; }}
        .io-item {{ padding: 12px; border: 2px solid #ddd; border-radius: 5px; text-align: center; font-size: 12px; font-weight: bold; }}
        .io-on {{ background: #d4edda; border-color: #28a745; color: #155724; }}
        .io-off {{ background: #f8d7da; border-color: #dc3545; color: #721c24; }}
        .registers-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 10px; margin-top: 15px; }}
        .register-item {{ padding: 15px; background: #f8f9fa; border-radius: 5px; text-align: center; border: 1px solid #e9ecef; }}
        .refresh-btn {{ background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-bottom: 20px; }}
        .refresh-btn:hover {{ background: #0056b3; }}
        .config-btn {{ background: #ffc107; color: #212529; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-left: 10px; }}
        .config-btn:hover {{ background: #e0a800; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔌 ESP-32 PLC Monitor</h1>
            <p>AutomationDirect CLICK PLC Interface</p>
            <span class="mode-badge">Mode: {self.operating_mode} | IP: {self.plc_data['system_info'].get('ip_address', 'Unknown')}</span>
        </div>
        
        <div style="text-align: center; margin-bottom: 20px;">
            <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Data</button>
            <button class="config-btn" onclick="window.open('/config', '_blank')">⚙️ WiFi Config</button>
        </div>
        
        <div class="status">
            <div class="status-card">
                <h4>Connection Status</h4>
                <div class="{status_class}">{connection_status}</div>
            </div>
            <div class="status-card">
                <h4>Communication Errors</h4>
                <div>{self.plc_data['communication_errors']}</div>
            </div>
            <div class="status-card">
                <h4>Last Update</h4>
                <div>{update_str}</div>
            </div>
            <div class="status-card">
                <h4>Free Memory</h4>
                <div>{gc.mem_free()} bytes</div>
            </div>
        </div>
        
        <div class="data-section">
            <h3>📥 Digital Inputs (X000-X015)</h3>
            <div class="io-grid">
                {inputs_html}
            </div>
        </div>
        
        <div class="data-section">
            <h3>📤 Digital Outputs (Y000-Y015)</h3>
            <div class="io-grid">
                {outputs_html}
            </div>
        </div>
        
        <div class="data-section">
            <h3>📊 Data Registers (DS001-DS010)</h3>
            <div class="registers-grid">
                {registers_html}
            </div>
        </div>
    </div>
</body>
</html>'''
        return html
    
    async def handle_client(self, reader, writer):
        """Handle HTTP client requests"""
        try:
            request = await reader.read(2048)
            request_str = request.decode('utf-8')
            
            # Parse request path
            if 'GET /' in request_str and 'GET /config' not in request_str and 'GET /api' not in request_str:
                # Main PLC monitor page
                if self.operating_mode == MODE_AP:
                    html_content = self.create_config_portal_html()
                else:
                    html_content = self.create_plc_monitor_html()
                
                response = f"""HTTP/1.1 200 OK\r
Content-Type: text/html\r
Connection: close\r
\r
{html_content}"""
            
            elif 'GET /config' in request_str:
                # WiFi configuration page (always show portal)
                html_content = self.create_config_portal_html()
                response = f"""HTTP/1.1 200 OK\r
Content-Type: text/html\r
Connection: close\r
\r
{html_content}"""
            
            elif 'GET /api/status' in request_str:
                # JSON API response
                response_data = {
                    'success': True,
                    'mode': self.operating_mode,
                    'data': self.plc_data,
                    'timestamp': time.time(),
                    'free_memory': gc.mem_free()
                }
                
                response = f"""HTTP/1.1 200 OK\r
Content-Type: application/json\r
Connection: close\r
\r
{ujson.dumps(response_data)}"""
            
            elif 'GET /api/networks' in request_str:
                # Network scan API
                networks = self.scan_networks()
                response_data = {
                    'success': True,
                    'networks': networks
                }
                
                response = f"""HTTP/1.1 200 OK\r
Content-Type: application/json\r
Connection: close\r
\r
{ujson.dumps(response_data)}"""
            
            elif 'POST /connect' in request_str:
                # WiFi connection endpoint
                try:
                    # Extract JSON data from POST body
                    body_start = request_str.find('\r\n\r\n') + 4
                    json_data = ujson.loads(request_str[body_start:])
                    
                    ssid = json_data.get('ssid', '')
                    password = json_data.get('password', '')
                    
                    if ssid:
                        success = self.save_wifi_credentials(ssid, password)
                        if success:
                            ip_address = self.sta_if.ifconfig()[0]
                            response_data = {
                                'success': True,
                                'message': 'Connected successfully',
                                'ip': ip_address
                            }
                        else:
                            response_data = {
                                'success': False,
                                'error': 'Failed to connect to network'
                            }
                    else:
                        response_data = {
                            'success': False,
                            'error': 'SSID is required'
                        }
                    
                except Exception as e:
                    response_data = {
                        'success': False,
                        'error': f'Invalid request: {str(e)}'
                    }
                
                response = f"""HTTP/1.1 200 OK\r
Content-Type: application/json\r
Connection: close\r
\r
{ujson.dumps(response_data)}"""
            
            else:
                # 404 Not Found
                response = """HTTP/1.1 404 Not Found\r
Content-Type: text/html\r
Connection: close\r
\r
<html><body><h1>404 Not Found</h1></body></html>"""
            
            await writer.awrite(response.encode('utf-8'))
            await writer.aclose()
            
        except Exception as e:
            print_log(f"Client handling error: {e}", "ERROR")
            try:
                await writer.aclose()
            except:
                pass
    
    async def start_web_server(self):
        """Start the web server"""
        server = await asyncio.start_server(
            self.handle_client, 
            '0.0.0.0', 
            WEB_PORT
        )
        
        if self.operating_mode == MODE_AP:
            print_log(f"Configuration portal started on http://{AP_IP}")
        else:
            ip_address = self.plc_data['system_info'].get('ip_address', 'Unknown')
            print_log(f"PLC monitor started on http://{ip_address}")
        
        async with server:
            await server.serve_forever()
    
    async def plc_polling_task(self):
        """Background task for PLC data polling"""
        while self.running:
            try:
                self.poll_plc_data()
                gc.collect()  # Memory management
                await asyncio.sleep(POLL_INTERVAL)
            except Exception as e:
                print_log(f"Polling task error: {e}", "ERROR")
                await asyncio.sleep(5)
    
    async def status_led_task(self):
        """Background task for status LED indication"""
        while self.running:
            try:
                if self.operating_mode == MODE_AP:
                    # Slow blink in AP mode
                    blink_pattern(self.status_led, 1, 500, 1500)
                elif self.operating_mode == MODE_STA and self.sta_if.isconnected():
                    # Steady on when connected
                    self.status_led.on()
                    await asyncio.sleep(2)
                else:
                    # Fast blink when disconnected
                    blink_pattern(self.status_led, 2, 100, 100)
                    await asyncio.sleep(1)
            except Exception as e:
                print_log(f"Status LED task error: {e}", "ERROR")
                await asyncio.sleep(5)
    
    async def run(self):
        """Main application runner"""
        print_log("ESP-32 PLC Bridge starting...")
        print_log(f"Free memory: {gc.mem_free()} bytes")
        
        # Try WiFi connection first
        wifi_connected = self.try_wifi_connection()
        
        if not wifi_connected:
            # Fall back to Access Point mode
            self.start_access_point()
        
        self.running = True
        
        # Start main application tasks
        tasks = [
            asyncio.create_task(self.start_web_server()),
            asyncio.create_task(self.plc_polling_task()),
            asyncio.create_task(self.status_led_task())
        ]
        
        try:
            print_log("All tasks started - entering main loop")
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print_log("Received shutdown signal")
            self.running = False
        except Exception as e:
            print_log(f"Main application error: {e}", "ERROR")
            self.running = False
        
        print_log("ESP-32 PLC Bridge shutting down")

# Main execution
async def main():
    bridge = ESP32PLCBridge()
    await bridge.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application stopped")