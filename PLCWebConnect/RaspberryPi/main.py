#!/usr/bin/env python3
"""
Raspberry Pi PLC Web Bridge - Main Application
Complete system for connecting AutomationDirect CLICK PLCs to web interfaces
"""

import sys
import os
import signal
import threading
import time
import logging
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from config import Config
from plc_communication import PLCCommunicator
from web_server import WebServer
from custom_scripts import create_script_engine, ScriptExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('plc_web_bridge.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class PLCWebBridge:
    """Main application class that manages PLC communication and web server"""
    
    def __init__(self):
        self.config = Config()
        self.running = False
        self.threads = []
        
        # Initialize PLC communicator
        self.plc_communicator = PLCCommunicator(self.config)
        
        # Initialize script engine
        self.script_engine = create_script_engine(self.plc_communicator, self.config)
        self.script_executor = ScriptExecutor(self.script_engine)
        
        # Initialize web server
        self.web_server = WebServer(
            self.plc_communicator, 
            self.config, 
            self.script_engine, 
            self.script_executor
        )
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("PLC Web Bridge initialized successfully")
    
    def start(self):
        """Start the PLC web bridge application"""
        try:
            logger.info("Starting PLC Web Bridge Application")
            
            # Connect to PLC
            if self.plc_communicator.connect():
                logger.info("PLC connection established successfully")
            else:
                logger.warning("PLC connection failed - running in simulation mode")
            
            # Start data polling thread
            logger.info("Starting PLC data polling loop")
            polling_thread = threading.Thread(target=self._data_polling_loop, daemon=True)
            polling_thread.start()
            self.threads.append(polling_thread)
            
            # Start web server
            logger.info(f"Starting web server on port {self.config.WEB_PORT}")
            self.running = True
            self.web_server.run()
            
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            raise
    
    def stop(self):
        """Stop the application gracefully"""
        logger.info("Stopping PLC Web Bridge Application")
        self.running = False
        
        if self.plc_communicator:
            self.plc_communicator.disconnect()
        
        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        logger.info("Application stopped successfully")
    
    def _data_polling_loop(self):
        """Background thread for continuous PLC data polling and script execution"""
        logger.info("PLC data polling loop started")
        
        while self.running:
            try:
                # Poll PLC data
                success = self.plc_communicator.poll_data()
                
                if success:
                    # Execute custom scripts
                    plc_data = self.plc_communicator.get_status()
                    script_results = self.script_executor.execute_all_enabled_scripts(plc_data)
                    
                    # Store script results in PLC communicator for web access
                    self.plc_communicator.script_results = script_results
                    
                # Sleep for the configured poll interval
                time.sleep(self.config.POLL_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)

def main():
    """Main function"""
    try:
        logger.info("AutomationDirect CLICK PLC Web Interface Starting...")
        
        # Create and start the application
        app = PLCWebBridge()
        app.start()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()