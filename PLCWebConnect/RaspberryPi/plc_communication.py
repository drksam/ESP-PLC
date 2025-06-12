"""
PLC Communication module for AutomationDirect CLICK PLC
Supports Modbus RTU/ASCII communication via Serial/USB
"""

import time
import logging
import threading
from datetime import datetime
import os
import random
import math

try:
    from pymodbus.client import ModbusSerialClient
    from pymodbus.exceptions import ModbusException, ConnectionException
    MODBUS_AVAILABLE = True
except ImportError:
    MODBUS_AVAILABLE = False
    logging.warning("pymodbus not available. Install with: pip install pymodbus pyserial")

logger = logging.getLogger(__name__)

class PLCCommunicator:
    """Handles communication with AutomationDirect CLICK PLC"""
    
    def __init__(self, config):
        self.config = config
        self.client = None
        self.connected = False
        self.last_data = {}
        self.last_update = None
        self.connection_lock = threading.Lock()
        self.simulation_mode = config.SIMULATION_MODE
        self.simulation_counter = 0
        
        # PLC status data structure
        self.plc_status = {
            'connected': False,
            'last_update': None,
            'communication_errors': 0,
            'data_registers': {},
            'coil_status': {},
            'input_status': {},
            'system_info': {
                'plc_model': 'AutomationDirect CLICK' + (' (Simulation)' if self.simulation_mode else ''),
                'communication_type': config.MODBUS_METHOD,
                'baud_rate': config.BAUD_RATE,
                'device_address': config.DEVICE_ADDRESS
            }
        }
    
    def connect(self):
        """Establish connection to the PLC"""
        # Check if simulation mode is enabled
        if self.simulation_mode:
            logger.info("Starting PLC simulation mode")
            self.connected = True
            self.plc_status['connected'] = True
            return True
            
        if not MODBUS_AVAILABLE:
            logger.error("Modbus library not available. Cannot connect to PLC.")
            return False
            
        try:
            with self.connection_lock:
                # Create Modbus client based on configuration
                if self.config.CONNECTION_TYPE.lower() == 'serial':
                    if MODBUS_AVAILABLE:
                        self.client = ModbusSerialClient(
                            port=self.config.SERIAL_PORT,
                            baudrate=self.config.BAUD_RATE,
                            timeout=self.config.TIMEOUT,
                            parity=self.config.PARITY,
                            stopbits=self.config.STOPBITS,
                            bytesize=self.config.BYTESIZE
                        )
                    else:
                        return False
                else:
                    logger.error(f"Unsupported connection type: {self.config.CONNECTION_TYPE}")
                    return False
                
                # Attempt to connect
                if self.client:
                    self.connected = self.client.connect()
                    
                    if self.connected:
                        logger.info(f"Successfully connected to PLC on {self.config.SERIAL_PORT}")
                        self.plc_status['connected'] = True
                        
                        # Test communication with a simple read
                        test_result = self._test_communication()
                        if not test_result:
                            logger.warning("PLC connection established but communication test failed")
                            
                        return True
                    else:
                        logger.error("Failed to establish PLC connection")
                        return False
                else:
                    return False
                    
        except Exception as e:
            logger.error(f"Error connecting to PLC: {e}")
            self.connected = False
            self.plc_status['connected'] = False
            return False
    
    def disconnect(self):
        """Disconnect from the PLC"""
        try:
            with self.connection_lock:
                if self.client and self.connected:
                    self.client.close()
                    self.connected = False
                    self.plc_status['connected'] = False
                    logger.info("Disconnected from PLC")
        except Exception as e:
            logger.error(f"Error disconnecting from PLC: {e}")
    
    def _test_communication(self):
        """Test PLC communication with a simple read operation"""
        try:
            # Try to read a single coil (address 0)
            result = self.client.read_coils(0, 1, unit=self.config.DEVICE_ADDRESS)
            if not result.isError():
                logger.info("PLC communication test successful")
                return True
            else:
                logger.error(f"PLC communication test failed: {result}")
                return False
        except Exception as e:
            logger.error(f"PLC communication test error: {e}")
            return False
    
    def poll_data(self):
        """Poll data from the PLC"""
        if not self.connected:
            logger.warning("Cannot poll data - PLC not connected")
            return False
        
        # Handle simulation mode
        if self.simulation_mode:
            return self._simulate_plc_data()
        
        if not self.client:
            logger.warning("Cannot poll data - No PLC client available")
            return False
        
        try:
            with self.connection_lock:
                # Read coils (digital outputs) - addresses 0-15
                if MODBUS_AVAILABLE:
                    coil_result = self.client.read_coils(0, 16, slave=self.config.DEVICE_ADDRESS)
                    if not coil_result.isError():
                        self.plc_status['coil_status'] = {
                            f'Y{i:03d}': bool(coil_result.bits[i]) for i in range(len(coil_result.bits))
                        }
                    
                    # Read discrete inputs (digital inputs) - addresses 0-15
                    input_result = self.client.read_discrete_inputs(0, 16, slave=self.config.DEVICE_ADDRESS)
                    if not input_result.isError():
                        self.plc_status['input_status'] = {
                            f'X{i:03d}': bool(input_result.bits[i]) for i in range(len(input_result.bits))
                        }
                    
                    # Read holding registers (analog/data registers) - addresses 0-9
                    register_result = self.client.read_holding_registers(0, 10, slave=self.config.DEVICE_ADDRESS)
                    if not register_result.isError():
                        self.plc_status['data_registers'] = {
                            f'DS{i+1:03d}': register_result.registers[i] for i in range(len(register_result.registers))
                        }
                
                # Update status
                self.plc_status['last_update'] = datetime.now().isoformat()
                self.last_update = time.time()
                
                logger.debug("PLC data polling completed successfully")
                return True
                
        except Exception as e:
            if MODBUS_AVAILABLE:
                logger.error(f"Modbus communication error: {e}")
            else:
                logger.error(f"Communication error: {e}")
            self.plc_status['communication_errors'] += 1
            return False
    
    def _simulate_plc_data(self):
        """Generate simulated PLC data for demonstration"""
        self.simulation_counter += 1
        current_time = time.time()
        
        # Simulate digital inputs with some patterns
        input_status = {}
        for i in range(16):
            # Create some interesting patterns
            if i < 4:
                # Toggle every few seconds
                input_status[f'X{i:03d}'] = (self.simulation_counter // (i + 2)) % 2 == 0
            elif i < 8:
                # Random states
                input_status[f'X{i:03d}'] = random.random() > 0.7
            else:
                # Mostly off with occasional on
                input_status[f'X{i:03d}'] = random.random() > 0.9
        
        # Simulate digital outputs (some follow inputs, some are independent)
        coil_status = {}
        for i in range(16):
            if i < 4:
                # Mirror some inputs
                coil_status[f'Y{i:03d}'] = input_status.get(f'X{i:03d}', False)
            elif i < 8:
                # Toggle patterns
                coil_status[f'Y{i:03d}'] = (self.simulation_counter // (i - 2)) % 2 == 0
            else:
                # Random states
                coil_status[f'Y{i:03d}'] = random.random() > 0.8
        
        # Simulate data registers with various patterns
        data_registers = {}
        for i in range(10):
            if i == 0:
                # Counter
                data_registers[f'DS{i+1:03d}'] = self.simulation_counter % 1000
            elif i == 1:
                # Sine wave (temperature simulation)
                data_registers[f'DS{i+1:03d}'] = int(200 + 50 * math.sin(current_time / 10))
            elif i == 2:
                # Random value (pressure)
                data_registers[f'DS{i+1:03d}'] = int(random.uniform(100, 500))
            elif i == 3:
                # Saw tooth pattern
                data_registers[f'DS{i+1:03d}'] = (self.simulation_counter * 5) % 1000
            else:
                # Various random patterns
                data_registers[f'DS{i+1:03d}'] = int(random.uniform(0, 65535))
        
        # Update the PLC status
        self.plc_status.update({
            'input_status': input_status,
            'coil_status': coil_status,
            'data_registers': data_registers,
            'last_update': datetime.now().isoformat()
        })
        
        self.last_update = time.time()
        logger.debug("Simulated PLC data generated successfully")
        return True
    
    def get_status(self):
        """Get current PLC status and data"""
        # Add connection age information
        if self.last_update:
            age_seconds = time.time() - self.last_update
            self.plc_status['data_age_seconds'] = round(age_seconds, 1)
            self.plc_status['data_fresh'] = age_seconds < (self.config.POLL_INTERVAL * 2)
        
        return self.plc_status.copy()
    
    def write_coil(self, address, value):
        """Write to a single coil (digital output)"""
        if not self.connected or not self.client:
            return False, "PLC not connected"
        
        try:
            with self.connection_lock:
                result = self.client.write_coil(address, value, unit=self.config.DEVICE_ADDRESS)
                if not result.isError():
                    logger.info(f"Successfully wrote coil {address}: {value}")
                    return True, "Success"
                else:
                    logger.error(f"Failed to write coil {address}: {result}")
                    return False, str(result)
        except Exception as e:
            logger.error(f"Error writing coil {address}: {e}")
            return False, str(e)
    
    def write_register(self, address, value):
        """Write to a single holding register"""
        if not self.connected or not self.client:
            return False, "PLC not connected"
        
        try:
            with self.connection_lock:
                result = self.client.write_register(address, value, unit=self.config.DEVICE_ADDRESS)
                if not result.isError():
                    logger.info(f"Successfully wrote register {address}: {value}")
                    return True, "Success"
                else:
                    logger.error(f"Failed to write register {address}: {result}")
                    return False, str(result)
        except Exception as e:
            logger.error(f"Error writing register {address}: {e}")
            return False, str(e)
