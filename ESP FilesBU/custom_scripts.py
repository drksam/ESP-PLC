"""
ESP-32 Custom Script System - Optimized for MicroPython
Lightweight automation scripts for GPIO control and Modbus operations
"""

import gc
import time
from machine import Pin

class ESP32GPIOController:
    """Lightweight GPIO controller for ESP-32"""
    
    def __init__(self):
        self.pins = {}
        self.pin_states = {}
        
    def setup_pin(self, pin_num, mode="output"):
        """Setup a GPIO pin"""
        try:
            if mode == "output":
                self.pins[pin_num] = Pin(pin_num, Pin.OUT)
            else:
                self.pins[pin_num] = Pin(pin_num, Pin.IN)
            self.pin_states[pin_num] = {"mode": mode, "value": False}
            return True
        except Exception as e:
            print(f"GPIO setup error pin {pin_num}: {e}")
            return False
    
    def set_pin(self, pin_num, value):
        """Set GPIO pin state"""
        try:
            if pin_num in self.pins:
                if value:
                    self.pins[pin_num].on()
                else:
                    self.pins[pin_num].off()
                self.pin_states[pin_num]["value"] = value
                return True
            return False
        except Exception as e:
            print(f"GPIO set error pin {pin_num}: {e}")
            return False
    
    def get_pin(self, pin_num):
        """Get GPIO pin state"""
        try:
            if pin_num in self.pins:
                value = self.pins[pin_num].value()
                self.pin_states[pin_num]["value"] = bool(value)
                return bool(value)
            return False
        except Exception as e:
            print(f"GPIO read error pin {pin_num}: {e}")
            return False
    
    def get_pin_states(self):
        """Get all pin states"""
        return self.pin_states.copy()

class ESP32ScriptEngine:
    """Lightweight script engine for ESP-32"""
    
    def __init__(self, modbus_client=None):
        self.gpio = ESP32GPIOController()
        self.modbus = modbus_client
        self.scripts = {}
        self.enabled_scripts = set()
        self.load_default_scripts()
        
        # Setup common GPIO pins
        self.gpio.setup_pin(2, "output")   # Built-in LED
        self.gpio.setup_pin(4, "output")   # General purpose
        self.gpio.setup_pin(5, "output")   # General purpose
        
    def load_default_scripts(self):
        """Load essential scripts for ESP-32"""
        
        # Status LED blinker
        self.scripts["status_led"] = {
            "name": "Status LED Blinker",
            "description": "Blinks built-in LED based on PLC connection",
            "enabled": True,
            "code": """
# Status LED control
if plc_data.get('connected', False):
    # Slow blink when connected
    if time.ticks_ms() % 2000 < 1000:
        gpio.set_pin(2, True)
    else:
        gpio.set_pin(2, False)
else:
    # Fast blink when disconnected
    if time.ticks_ms() % 500 < 250:
        gpio.set_pin(2, True)
    else:
        gpio.set_pin(2, False)
"""
        }
        
        # Emergency stop monitor
        self.scripts["emergency_stop"] = {
            "name": "Emergency Stop Monitor",
            "description": "Monitors emergency stop button and activates safety outputs",
            "enabled": False,
            "code": """
# Emergency stop logic
emergency_input = plc_data.get('digital_inputs', {}).get(1, False)
if not emergency_input:  # Emergency stop pressed (normally closed)
    # Turn off all outputs
    for addr in range(1, 9):
        if write_coil:
            write_coil(addr, False)
    # Activate alarm output
    gpio.set_pin(4, True)
else:
    gpio.set_pin(4, False)
"""
        }
        
        # Temperature alarm
        self.scripts["temp_alarm"] = {
            "name": "Temperature Alarm",
            "description": "Temperature monitoring with GPIO alarm output",
            "enabled": False,
            "code": """
# Temperature alarm (assuming register 1 is temperature)
temp_value = plc_data.get('data_registers', {}).get(1, 0)
if temp_value > 750:  # 75.0 degrees (assuming 0.1 degree resolution)
    gpio.set_pin(5, True)  # Activate alarm
    print(f"Temperature alarm: {temp_value/10}°C")
elif temp_value < 700:  # Hysteresis
    gpio.set_pin(5, False)
"""
        }
        
        # Add enabled scripts to the set
        for script_id, script in self.scripts.items():
            if script.get("enabled", False):
                self.enabled_scripts.add(script_id)
    
    def execute_script(self, script_id, plc_data):
        """Execute a single script safely"""
        if script_id not in self.scripts or script_id not in self.enabled_scripts:
            return {"success": False, "error": "Script not found or disabled"}
        
        script = self.scripts[script_id]
        result = {
            "script_id": script_id,
            "success": False,
            "error": None,
            "execution_time": 0
        }
        
        start_time = time.ticks_ms()
        
        try:
            # Create safe execution environment
            script_globals = {
                "plc_data": plc_data,
                "gpio": self.gpio,
                "time": time,
                "print": print,
                "write_coil": self._write_coil_wrapper,
                "write_register": self._write_register_wrapper
            }
            
            # Execute script code
            exec(script["code"], script_globals)
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            print(f"Script {script_id} error: {e}")
        
        result["execution_time"] = time.ticks_diff(time.ticks_ms(), start_time)
        return result
    
    def execute_enabled_scripts(self, plc_data):
        """Execute all enabled scripts"""
        results = {}
        
        for script_id in list(self.enabled_scripts):  # Create copy to avoid modification during iteration
            if script_id in self.scripts:
                results[script_id] = self.execute_script(script_id, plc_data)
        
        # Memory cleanup
        gc.collect()
        
        return {
            "results": results,
            "gpio_states": self.gpio.get_pin_states(),
            "memory_free": gc.mem_free(),
            "timestamp": time.ticks_ms()
        }
    
    def _write_coil_wrapper(self, address, value):
        """Safe wrapper for PLC coil writing"""
        if self.modbus:
            try:
                return self.modbus.write_coil(address, value)
            except Exception as e:
                print(f"Modbus write coil error: {e}")
                return False
        return False
    
    def _write_register_wrapper(self, address, value):
        """Safe wrapper for PLC register writing"""
        if self.modbus:
            try:
                return self.modbus.write_register(address, value)
            except Exception as e:
                print(f"Modbus write register error: {e}")
                return False
        return False
    
    def enable_script(self, script_id):
        """Enable a script"""
        if script_id in self.scripts:
            self.scripts[script_id]["enabled"] = True
            self.enabled_scripts.add(script_id)
            return True
        return False
    
    def disable_script(self, script_id):
        """Disable a script"""
        if script_id in self.scripts:
            self.scripts[script_id]["enabled"] = False
            self.enabled_scripts.discard(script_id)
            return True
        return False
    
    def get_script_info(self, script_id):
        """Get script information"""
        if script_id in self.scripts:
            script = self.scripts[script_id].copy()
            script["enabled"] = script_id in self.enabled_scripts
            return script
        return None
    
    def get_all_scripts(self):
        """Get all script information"""
        result = {}
        for script_id, script in self.scripts.items():
            script_info = script.copy()
            script_info["enabled"] = script_id in self.enabled_scripts
            result[script_id] = script_info
        return result

def create_script_engine(modbus_client=None):
    """Factory function to create script engine"""
    return ESP32ScriptEngine(modbus_client)

# Usage example:
"""
# In your main ESP-32 application:
from custom_scripts import create_script_engine

# Create script engine
script_engine = create_script_engine(modbus_client)

# In your main loop:
plc_data = {
    'connected': True,
    'digital_inputs': {1: True, 2: False},
    'data_registers': {1: 720}  # Temperature example
}

# Execute scripts
results = script_engine.execute_enabled_scripts(plc_data)
print(f"Free memory: {results['memory_free']} bytes")
"""