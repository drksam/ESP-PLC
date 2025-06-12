"""
Configuration module for PLC Web Bridge
Handles all application configuration parameters
"""

import os
import logging

logger = logging.getLogger(__name__)

class Config:
    """Configuration class with default values and environment variable support"""
    
    def __init__(self):
        # Web Server Configuration
        self.WEB_PORT = int(os.getenv('WEB_PORT', '5000'))
        self.DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
        
        # PLC Communication Configuration
        self.CONNECTION_TYPE = os.getenv('CONNECTION_TYPE', 'serial')  # 'serial' or 'tcp'
        self.SERIAL_PORT = os.getenv('SERIAL_PORT', '/dev/ttyUSB0')  # Default USB-Serial port
        self.BAUD_RATE = int(os.getenv('BAUD_RATE', '9600'))
        self.TIMEOUT = float(os.getenv('TIMEOUT', '3.0'))
        self.DEVICE_ADDRESS = int(os.getenv('DEVICE_ADDRESS', '1'))  # Modbus slave address
        
        # Modbus Configuration
        self.MODBUS_METHOD = os.getenv('MODBUS_METHOD', 'rtu')  # 'rtu' or 'ascii'
        self.PARITY = os.getenv('PARITY', 'N')  # 'N', 'E', 'O'
        self.STOPBITS = int(os.getenv('STOPBITS', '1'))
        self.BYTESIZE = int(os.getenv('BYTESIZE', '8'))
        
        # Data Polling Configuration
        self.POLL_INTERVAL = float(os.getenv('POLL_INTERVAL', '1.0'))  # seconds
        
        # Alternative serial ports for different platforms
        self.AUTO_DETECT_PORT = os.getenv('AUTO_DETECT_PORT', 'True').lower() == 'true'
        
        # Simulation mode for demo when no PLC is connected
        self.SIMULATION_MODE = os.getenv('SIMULATION_MODE', 'True').lower() == 'true'
        
        # Log configuration
        self._log_config()
        
        # Auto-detect serial port if enabled
        if self.AUTO_DETECT_PORT:
            self._auto_detect_serial_port()
    
    def _log_config(self):
        """Log current configuration"""
        logger.info("=== PLC Web Bridge Configuration ===")
        logger.info(f"Web Port: {self.WEB_PORT}")
        logger.info(f"Connection Type: {self.CONNECTION_TYPE}")
        logger.info(f"Serial Port: {self.SERIAL_PORT}")
        logger.info(f"Baud Rate: {self.BAUD_RATE}")
        logger.info(f"Modbus Method: {self.MODBUS_METHOD}")
        logger.info(f"Device Address: {self.DEVICE_ADDRESS}")
        logger.info(f"Poll Interval: {self.POLL_INTERVAL}s")
        logger.info("=====================================")
    
    def _auto_detect_serial_port(self):
        """Auto-detect available serial ports"""
        import glob
        
        # Common serial port patterns for different platforms
        port_patterns = [
            '/dev/ttyUSB*',      # USB-Serial adapters (Linux)
            '/dev/ttyACM*',      # Arduino/USB CDC devices (Linux)
            '/dev/ttyAMA*',      # Raspberry Pi UART (Linux)
            '/dev/cu.usbserial*', # macOS USB-Serial
            '/dev/cu.SLAB_USBtoUART*', # macOS CP2102 adapters
        ]
        
        available_ports = []
        for pattern in port_patterns:
            available_ports.extend(glob.glob(pattern))
        
        if available_ports:
            logger.info(f"Available serial ports: {available_ports}")
            
            # If current port doesn't exist, use the first available
            if self.SERIAL_PORT not in available_ports:
                old_port = self.SERIAL_PORT
                self.SERIAL_PORT = available_ports[0]
                logger.info(f"Auto-detected serial port: {old_port} -> {self.SERIAL_PORT}")
        else:
            logger.warning("No serial ports detected")
    
    def get_connection_info(self):
        """Get connection information as dictionary"""
        return {
            'connection_type': self.CONNECTION_TYPE,
            'serial_port': self.SERIAL_PORT,
            'baud_rate': self.BAUD_RATE,
            'modbus_method': self.MODBUS_METHOD,
            'device_address': self.DEVICE_ADDRESS,
            'timeout': self.TIMEOUT
        }
