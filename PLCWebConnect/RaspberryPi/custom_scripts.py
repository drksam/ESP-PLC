"""
Custom Script System for PLC Web Bridge
Allows user-programmable GPIO control and Modbus bit manipulation
"""

import time
import logging
from typing import Dict, Any, List, Callable
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScriptEngine:
    """Engine for executing user-defined automation scripts"""
    
    def __init__(self, plc_communicator, config):
        self.plc = plc_communicator
        self.config = config
        self.scripts = {}
        self.script_states = {}
        self.running_scripts = set()
        
        # GPIO simulation for non-GPIO platforms
        try:
            import RPi.GPIO as GPIO
            self.gpio_available = True
            GPIO.setmode(GPIO.BCM)
            logger.info("GPIO library initialized successfully")
        except ImportError:
            self.gpio_available = False
            logger.warning("GPIO library not available - using simulation mode")
        
        # Load default scripts
        self.load_default_scripts()
    
    def load_default_scripts(self):
        """Load default example scripts"""
        
        # Example 1: GPIO Output Control
        self.scripts["gpio_output_example"] = {
            "name": "GPIO Output Example",
            "description": "Controls GPIO pin 18 based on PLC input X001",
            "enabled": False,
            "gpio_pins": [18],
            "code": """
# GPIO Output Control Example
# Monitors PLC input X001 and controls GPIO pin 18

def execute(plc_data, gpio, script_state):
    # Get PLC input status
    x001_status = plc_data.get('input_status', {}).get('X001', False)
    
    # Control GPIO pin 18 based on X001
    if x001_status:
        gpio.set_pin(18, True)
        return {"status": "GPIO 18 ON - X001 active"}
    else:
        gpio.set_pin(18, False)
        return {"status": "GPIO 18 OFF - X001 inactive"}
"""
        }
        
        # Example 2: Modbus Bit Manipulation
        self.scripts["modbus_bit_example"] = {
            "name": "Modbus Bit Control",
            "description": "Sets PLC coil Y005 when X002 and X003 are both active",
            "enabled": False,
            "gpio_pins": [],
            "code": """
# Modbus Bit Control Example
# Logic: Y005 = X002 AND X003

def execute(plc_data, gpio, script_state):
    # Get input statuses
    x002 = plc_data.get('input_status', {}).get('X002', False)
    x003 = plc_data.get('input_status', {}).get('X003', False)
    
    # Calculate output
    y005_value = x002 and x003
    
    # Write to PLC coil
    if gpio.write_coil(5, y005_value):
        return {"status": f"Y005 = {y005_value} (X002={x002}, X003={x003})"}
    else:
        return {"status": "Failed to write Y005", "error": True}
"""
        }
        
        # Example 3: Timer-based Control
        self.scripts["timer_example"] = {
            "name": "Timer Control",
            "description": "Toggles GPIO pin 19 every 5 seconds",
            "enabled": False,
            "gpio_pins": [19],
            "code": """
# Timer Control Example
# Toggles GPIO pin 19 every 5 seconds

def execute(plc_data, gpio, script_state):
    current_time = time.time()
    
    # Initialize timer if not exists
    if 'last_toggle' not in script_state:
        script_state['last_toggle'] = current_time
        script_state['pin_state'] = False
    
    # Check if 5 seconds have passed
    if current_time - script_state['last_toggle'] >= 5.0:
        # Toggle pin state
        script_state['pin_state'] = not script_state['pin_state']
        gpio.set_pin(19, script_state['pin_state'])
        script_state['last_toggle'] = current_time
        
        return {"status": f"GPIO 19 toggled to {script_state['pin_state']}"}
    else:
        remaining = 5.0 - (current_time - script_state['last_toggle'])
        return {"status": f"Next toggle in {remaining:.1f}s"}
"""
        }
        
        # Example 4: Data Register Monitoring
        self.scripts["register_monitor"] = {
            "name": "Data Register Monitor",
            "description": "Monitors DS001 and triggers GPIO when value exceeds 100",
            "enabled": False,
            "gpio_pins": [20],
            "code": """
# Data Register Monitor Example
# Triggers GPIO 20 when DS001 > 100

def execute(plc_data, gpio, script_state):
    # Get data register value
    ds001_value = plc_data.get('data_registers', {}).get('DS001', 0)
    
    # Check threshold
    if ds001_value > 100:
        gpio.set_pin(20, True)
        return {"status": f"Alert! DS001 = {ds001_value} (GPIO 20 ON)"}
    else:
        gpio.set_pin(20, False)
        return {"status": f"DS001 = {ds001_value} (Normal)"}
"""
        }

class GPIOController:
    """GPIO controller with simulation fallback"""
    
    def __init__(self, gpio_available=False):
        self.gpio_available = gpio_available
        self.pin_states = {}
        
        if gpio_available:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
        else:
            logger.info("GPIO simulation mode active")
    
    def setup_pin(self, pin: int, mode: str = "output"):
        """Setup a GPIO pin"""
        if self.gpio_available:
            if mode.lower() == "output":
                self.GPIO.setup(pin, self.GPIO.OUT)
            else:
                self.GPIO.setup(pin, self.GPIO.IN)
        
        self.pin_states[pin] = {"mode": mode, "value": False}
        logger.info(f"GPIO pin {pin} configured as {mode}")
    
    def set_pin(self, pin: int, value: bool):
        """Set GPIO pin state"""
        if pin not in self.pin_states:
            self.setup_pin(pin, "output")
        
        if self.gpio_available:
            self.GPIO.output(pin, value)
        
        self.pin_states[pin]["value"] = value
        logger.info(f"GPIO pin {pin} set to {value}")
    
    def get_pin(self, pin: int) -> bool:
        """Get GPIO pin state"""
        if pin not in self.pin_states:
            return False
        
        if self.gpio_available and self.pin_states[pin]["mode"] == "input":
            return self.GPIO.input(pin)
        
        return self.pin_states[pin]["value"]
    
    def write_coil(self, address: int, value: bool) -> bool:
        """Write to PLC coil via script engine's PLC communicator"""
        # This will be called through the script engine
        return True
    
    def get_pin_states(self) -> Dict[int, Dict]:
        """Get all pin states"""
        return self.pin_states.copy()

class ScriptExecutor:
    """Executes user scripts safely"""
    
    def __init__(self, script_engine):
        self.engine = script_engine
        self.gpio = GPIOController(script_engine.gpio_available)
        
        # Enhanced GPIO controller with PLC write capability
        self.gpio.write_coil = self._write_coil_wrapper
        self.gpio.write_register = self._write_register_wrapper
    
    def _write_coil_wrapper(self, address: int, value: bool) -> bool:
        """Wrapper for PLC coil writing"""
        try:
            return self.engine.plc.write_coil(address, value)
        except Exception as e:
            logger.error(f"Failed to write coil {address}: {e}")
            return False
    
    def _write_register_wrapper(self, address: int, value: int) -> bool:
        """Wrapper for PLC register writing"""
        try:
            return self.engine.plc.write_register(address, value)
        except Exception as e:
            logger.error(f"Failed to write register {address}: {e}")
            return False
    
    def execute_script(self, script_id: str, plc_data: Dict) -> Dict[str, Any]:
        """Execute a single script"""
        if script_id not in self.engine.scripts:
            return {"error": f"Script {script_id} not found"}
        
        script = self.engine.scripts[script_id]
        
        if not script.get("enabled", False):
            return {"status": "Script disabled"}
        
        try:
            # Setup GPIO pins if needed
            for pin in script.get("gpio_pins", []):
                if pin not in self.gpio.pin_states:
                    self.gpio.setup_pin(pin, "output")
            
            # Get or create script state
            if script_id not in self.engine.script_states:
                self.engine.script_states[script_id] = {}
            
            script_state = self.engine.script_states[script_id]
            
            # Create execution environment
            exec_globals = {
                "time": time,
                "logger": logger,
                "__builtins__": {
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "max": max,
                    "min": min,
                    "abs": abs,
                    "round": round,
                }
            }
            
            # Execute the script code
            exec(script["code"], exec_globals)
            
            # Call the execute function
            if "execute" in exec_globals:
                result = exec_globals["execute"](plc_data, self.gpio, script_state)
                
                # Add script info to result
                if isinstance(result, dict):
                    result["script_name"] = script["name"]
                    result["script_id"] = script_id
                    result["timestamp"] = time.time()
                
                return result
            else:
                return {"error": "Script must define an 'execute' function"}
                
        except Exception as e:
            logger.error(f"Script execution error in {script_id}: {e}")
            return {
                "error": f"Script execution failed: {str(e)}",
                "script_id": script_id,
                "timestamp": time.time()
            }
    
    def execute_all_enabled_scripts(self, plc_data: Dict) -> Dict[str, Any]:
        """Execute all enabled scripts"""
        results = {}
        
        for script_id, script in self.engine.scripts.items():
            if script.get("enabled", False):
                results[script_id] = self.execute_script(script_id, plc_data)
        
        # Add GPIO states to results
        results["gpio_states"] = self.gpio.get_pin_states()
        
        return results

def create_script_engine(plc_communicator, config):
    """Factory function to create script engine"""
    return ScriptEngine(plc_communicator, config)

# Example of how to use the script system:
"""
# In your main application:
script_engine = create_script_engine(plc_communicator, config)
executor = ScriptExecutor(script_engine)

# In your polling loop:
plc_data = plc_communicator.get_status()
script_results = executor.execute_all_enabled_scripts(plc_data)

# The results contain:
# - Individual script outputs
# - GPIO pin states
# - Error information
# - Execution timestamps
"""