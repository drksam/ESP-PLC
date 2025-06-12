"""
Web server module for serving PLC status data
Provides REST API and web interface for PLC monitoring
"""

import json
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response
import os

logger = logging.getLogger(__name__)

class WebServer:
    """Flask-based web server for PLC status display"""
    
    def __init__(self, plc_communicator, config, script_engine=None, script_executor=None):
        self.plc_communicator = plc_communicator
        self.config = config
        self.script_engine = script_engine
        self.script_executor = script_executor
        self.app = Flask(__name__)
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main status page"""
            return render_template('index.html')
        
        @self.app.route('/api/status')
        def api_status():
            """API endpoint for PLC status"""
            try:
                status = self.plc_communicator.get_status()
                return jsonify({
                    'success': True,
                    'data': status,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error getting PLC status: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/coil/<int:address>', methods=['POST'])
        def api_write_coil(address):
            """API endpoint to write coil value"""
            try:
                data = request.get_json()
                if 'value' not in data:
                    return jsonify({'success': False, 'error': 'Missing value parameter'}), 400
                
                value = bool(data['value'])
                success, message = self.plc_communicator.write_coil(address, value)
                
                return jsonify({
                    'success': success,
                    'message': message,
                    'address': address,
                    'value': value,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error writing coil {address}: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/register/<int:address>', methods=['POST'])
        def api_write_register(address):
            """API endpoint to write register value"""
            try:
                data = request.get_json()
                if 'value' not in data:
                    return jsonify({'success': False, 'error': 'Missing value parameter'}), 400
                
                value = int(data['value'])
                success, message = self.plc_communicator.write_register(address, value)
                
                return jsonify({
                    'success': success,
                    'message': message,
                    'address': address,
                    'value': value,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error writing register {address}: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/health')
        def api_health():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'plc_connected': self.plc_communicator.connected,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/download/esp32')
        def download_esp32_files():
            """Download ESP-32 files as a ZIP archive"""
            import zipfile
            import tempfile
            import os
            from flask import send_file
            
            try:
                # Create temporary ZIP file
                temp_dir = tempfile.mkdtemp()
                zip_path = os.path.join(temp_dir, 'ESP32_PLC_Bridge.zip')
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Add all ESP-32 files to ZIP
                    esp32_files = {
                        'boot.py': self._get_boot_py_content(),
                        'config.py': self._get_config_py_content(),
                        'main.py': self._get_main_py_content(),
                        'custom_scripts.py': self._get_custom_scripts_py_content(),
                        'wifi_debug.py': self._get_wifi_debug_py_content(),
                        'README.md': self._get_readme_content()
                    }
                    
                    for filename, content in esp32_files.items():
                        zipf.writestr(filename, content)
                
                return send_file(
                    zip_path,
                    as_attachment=True,
                    download_name='ESP32_PLC_Bridge.zip',
                    mimetype='application/zip'
                )
                
            except Exception as e:
                logger.error(f"Error creating ESP-32 download: {e}")
                return jsonify({'error': 'Failed to create download package'}), 500
        
        # Custom Scripts Routes
        @self.app.route('/scripts')
        def scripts_page():
            """Custom scripts management page"""
            return render_template('scripts.html')
        
        @self.app.route('/api/scripts')
        def api_scripts():
            """Get all custom scripts"""
            if not self.script_engine:
                return jsonify({'success': False, 'error': 'Script engine not available'}), 503
            
            try:
                scripts = {}
                for script_id, script in self.script_engine.scripts.items():
                    scripts[script_id] = {
                        'id': script_id,
                        'name': script['name'],
                        'description': script['description'],
                        'enabled': script['enabled'],
                        'gpio_pins': script['gpio_pins']
                    }
                
                return jsonify({
                    'success': True,
                    'scripts': scripts,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error getting scripts: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/scripts/<script_id>')
        def api_script_detail(script_id):
            """Get detailed script information including code"""
            if not self.script_engine:
                return jsonify({'success': False, 'error': 'Script engine not available'}), 503
            
            try:
                if script_id not in self.script_engine.scripts:
                    return jsonify({'success': False, 'error': 'Script not found'}), 404
                
                script = self.script_engine.scripts[script_id].copy()
                script['id'] = script_id
                
                return jsonify({
                    'success': True,
                    'script': script,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error getting script {script_id}: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/scripts/<script_id>/toggle', methods=['POST'])
        def api_script_toggle(script_id):
            """Toggle script enabled/disabled"""
            if not self.script_engine:
                return jsonify({'success': False, 'error': 'Script engine not available'}), 503
            
            try:
                if script_id not in self.script_engine.scripts:
                    return jsonify({'success': False, 'error': 'Script not found'}), 404
                
                current_state = self.script_engine.scripts[script_id]['enabled']
                new_state = not current_state
                self.script_engine.scripts[script_id]['enabled'] = new_state
                
                return jsonify({
                    'success': True,
                    'script_id': script_id,
                    'enabled': new_state,
                    'message': f"Script {'enabled' if new_state else 'disabled'}",
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error toggling script {script_id}: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/scripts/<script_id>', methods=['PUT'])
        def api_script_update(script_id):
            """Update script code and configuration"""
            if not self.script_engine:
                return jsonify({'success': False, 'error': 'Script engine not available'}), 503
            
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'No data provided'}), 400
                
                if script_id not in self.script_engine.scripts:
                    return jsonify({'success': False, 'error': 'Script not found'}), 404
                
                script = self.script_engine.scripts[script_id]
                
                # Update script properties
                if 'name' in data:
                    script['name'] = data['name']
                if 'description' in data:
                    script['description'] = data['description']
                if 'code' in data:
                    script['code'] = data['code']
                if 'gpio_pins' in data:
                    script['gpio_pins'] = data['gpio_pins']
                if 'enabled' in data:
                    script['enabled'] = bool(data['enabled'])
                
                return jsonify({
                    'success': True,
                    'script_id': script_id,
                    'message': 'Script updated successfully',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error updating script {script_id}: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/scripts', methods=['POST'])
        def api_script_create():
            """Create new custom script"""
            if not self.script_engine:
                return jsonify({'success': False, 'error': 'Script engine not available'}), 503
            
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'No data provided'}), 400
                
                required_fields = ['id', 'name', 'description', 'code']
                for field in required_fields:
                    if field not in data:
                        return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
                
                script_id = data['id']
                if script_id in self.script_engine.scripts:
                    return jsonify({'success': False, 'error': 'Script ID already exists'}), 400
                
                new_script = {
                    'name': data['name'],
                    'description': data['description'],
                    'code': data['code'],
                    'enabled': data.get('enabled', False),
                    'gpio_pins': data.get('gpio_pins', [])
                }
                
                self.script_engine.scripts[script_id] = new_script
                
                return jsonify({
                    'success': True,
                    'script_id': script_id,
                    'message': 'Script created successfully',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error creating script: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/scripts/<script_id>', methods=['DELETE'])
        def api_script_delete(script_id):
            """Delete custom script"""
            if not self.script_engine:
                return jsonify({'success': False, 'error': 'Script engine not available'}), 503
            
            try:
                if script_id not in self.script_engine.scripts:
                    return jsonify({'success': False, 'error': 'Script not found'}), 404
                
                del self.script_engine.scripts[script_id]
                
                # Clean up script state
                if script_id in self.script_engine.script_states:
                    del self.script_engine.script_states[script_id]
                
                return jsonify({
                    'success': True,
                    'script_id': script_id,
                    'message': 'Script deleted successfully',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error deleting script {script_id}: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/scripts/results')
        def api_script_results():
            """Get current script execution results"""
            if not self.script_executor:
                return jsonify({'success': False, 'error': 'Script executor not available'}), 503
            
            try:
                # Get script results from PLC communicator
                results = getattr(self.plc_communicator, 'script_results', {})
                
                return jsonify({
                    'success': True,
                    'results': results,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error getting script results: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/scripts/<script_id>/execute', methods=['POST'])
        def api_script_execute(script_id):
            """Execute a specific script manually"""
            if not self.script_executor:
                return jsonify({'success': False, 'error': 'Script executor not available'}), 503
            
            try:
                if script_id not in self.script_engine.scripts:
                    return jsonify({'success': False, 'error': 'Script not found'}), 404
                
                # Get current PLC data
                plc_data = self.plc_communicator.get_status()
                
                # Execute the script
                result = self.script_executor.execute_script(script_id, plc_data)
                
                return jsonify({
                    'success': True,
                    'script_id': script_id,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error executing script {script_id}: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Not found'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({'error': 'Internal server error'}), 500
    
    def _get_boot_py_content(self):
        """Get boot.py content for ESP-32"""
        return '''"""
ESP-32 Boot file with upload delay
Place this as boot.py on your ESP-32
"""

import gc
import network
import time
import sys
from machine import Pin

def boot_delay_with_interrupt():
    """5-second boot delay allowing file upload interruption"""
    try:
        led = Pin(2, Pin.OUT)
        print("=" * 50)
        print("ESP-32 PLC Bridge - Boot Sequence")
        print("=" * 50)
        print("Press Ctrl+C within 5 seconds to interrupt boot")
        print("and upload new files...")
        print()
        
        # 5-second countdown with LED indicator
        for countdown in range(5, 0, -1):
            print(f"Starting in {countdown} seconds... (Ctrl+C to interrupt)")
            
            # Blink LED during countdown
            led.on()
            time.sleep(0.5)
            led.off()
            time.sleep(0.5)
            
        print()
        print("Boot delay complete - starting main application")
        print("=" * 50)
        
        # Final startup blink
        for i in range(2):
            led.on()
            time.sleep_ms(100)
            led.off()
            time.sleep_ms(100)
            
    except KeyboardInterrupt:
        print()
        print("=" * 50)
        print("BOOT INTERRUPTED - Ready for file upload")
        print("=" * 50)
        print("You can now upload files using:")
        print("- Thonny IDE")
        print("- ampy command line tool")
        print("- mpfshell")
        print("- WebREPL (if enabled)")
        print()
        print("To resume normal boot, press the EN/RST button")
        print("or power cycle the ESP-32")
        print("=" * 50)
        
        # Keep LED on to indicate upload mode
        try:
            led = Pin(2, Pin.OUT)
            led.on()
        except:
            pass
            
        # Stay in REPL mode for file uploads
        sys.exit()

def blink_startup():
    """Startup LED sequence"""
    try:
        led = Pin(2, Pin.OUT)
        for _ in range(3):
            led.on()
            time.sleep_ms(200)
            led.off()
            time.sleep_ms(200)
    except:
        pass

# Perform boot delay and startup sequence
boot_delay_with_interrupt()

# Enable garbage collection
gc.enable()

# Additional startup blinks
blink_startup()

# Basic memory info
print(f"Free memory: {gc.mem_free()} bytes")

# Disable AP mode temporarily during boot
try:
    ap = network.WLAN(network.AP_IF)
    ap.active(False)
except:
    pass

print("Boot sequence complete. Loading main application...")
print("=" * 50)'''

    def _get_config_py_content(self):
        """Get config.py content for ESP-32"""
        return '''"""
ESP-32 Configuration file
Edit these settings for your specific setup before uploading
"""

# WiFi Settings - EDIT THESE VALUES
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

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
RESPONSE_TIMEOUT = 100  # milliseconds for Modbus responses'''

    def _get_main_py_content(self):
        """Get main.py content for ESP-32"""
        try:
            with open('ESP32_Files/main.py', 'r') as f:
                return f.read()
        except:
            return "# ESP-32 main.py file not found"

    def _get_wifi_debug_py_content(self):
        """Get wifi_debug.py content for ESP-32"""
        try:
            with open('ESP32_Files/wifi_debug.py', 'r') as f:
                return f.read()
        except:
            return "# WiFi debug file not found"

    def _get_custom_scripts_py_content(self):
        """Get custom_scripts.py content for ESP-32"""
        try:
            with open('ESP32_Files/custom_scripts.py', 'r') as f:
                return f.read()
        except:
            return "# Custom scripts file not found"

    def _get_readme_content(self):
        """Get README.md content for ESP-32"""
        try:
            with open('ESP32_Files/README.md', 'r') as f:
                return f.read()
        except:
            return "# ESP-32 PLC Bridge Setup Instructions\n\nFiles ready for upload to ESP-32."

    def run(self):
        """Start the web server"""
        try:
            self.app.run(
                host='0.0.0.0',
                port=self.config.WEB_PORT,
                debug=self.config.DEBUG,
                threaded=True
            )
        except Exception as e:
            logger.error(f"Error starting web server: {e}")
            raise
