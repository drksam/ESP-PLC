#!/usr/bin/env python3
"""
Raspberry Pi PLC Bridge Diagnostics Tool
Comprehensive system testing and validation
"""

import os
import sys
import subprocess
import serial
import time
import socket
from pathlib import Path

def run_command(cmd):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def check_python_environment():
    """Check Python and virtual environment"""
    print("=== Python Environment ===")
    
    # Python version
    print(f"Python version: {sys.version}")
    
    # Virtual environment
    venv_path = Path("venv")
    if venv_path.exists():
        print("✓ Virtual environment found")
    else:
        print("✗ Virtual environment missing - run ./install.sh")
    
    # Required packages
    try:
        import flask
        import pymodbus
        import serial
        print("✓ Required Python packages installed")
    except ImportError as e:
        print(f"✗ Missing package: {e}")

def check_system_dependencies():
    """Check system packages and permissions"""
    print("\n=== System Dependencies ===")
    
    # GPIO libraries
    success, _, _ = run_command("python3 -c 'import RPi.GPIO'")
    if success:
        print("✓ RPi.GPIO available")
    else:
        print("✗ RPi.GPIO not available (install with: pip install RPi.GPIO)")
    
    # User groups
    success, output, _ = run_command("groups")
    if "dialout" in output:
        print("✓ User in dialout group")
    else:
        print("✗ User not in dialout group - run: sudo usermod -a -G dialout $USER")

def check_serial_ports():
    """Check available serial ports"""
    print("\n=== Serial Ports ===")
    
    # List available ports
    success, output, _ = run_command("ls -la /dev/tty*")
    usb_ports = [line for line in output.split('\n') if 'ttyUSB' in line or 'ttyAMA' in line]
    
    if usb_ports:
        print("Available serial ports:")
        for port in usb_ports:
            print(f"  {port}")
    else:
        print("No USB serial ports found")
    
    # Test default port
    try:
        port = "/dev/ttyUSB0"
        ser = serial.Serial(port, 9600, timeout=1)
        ser.close()
        print(f"✓ Can access {port}")
    except Exception as e:
        print(f"✗ Cannot access {port}: {e}")

def check_network():
    """Check network connectivity"""
    print("\n=== Network ===")
    
    # Get IP addresses
    success, output, _ = run_command("hostname -I")
    if success and output:
        ips = output.split()
        print(f"IP addresses: {', '.join(ips)}")
    else:
        print("No network connection")
    
    # Check if port 5000 is available
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 5000))
        sock.close()
        if result == 0:
            print("⚠ Port 5000 is in use")
        else:
            print("✓ Port 5000 available")
    except Exception as e:
        print(f"✗ Network test failed: {e}")

def check_service_status():
    """Check systemd service status"""
    print("\n=== Service Status ===")
    
    # Check if service exists
    success, output, _ = run_command("systemctl list-unit-files | grep plc-bridge")
    if success and output:
        print("✓ plc-bridge service installed")
        
        # Check service status
        success, output, _ = run_command("systemctl is-active plc-bridge")
        print(f"Service status: {output}")
        
        # Check if enabled
        success, output, _ = run_command("systemctl is-enabled plc-bridge")
        print(f"Auto-start: {output}")
    else:
        print("✗ plc-bridge service not installed")

def check_configuration():
    """Check configuration files"""
    print("\n=== Configuration ===")
    
    config_file = Path("config.py")
    if config_file.exists():
        print("✓ config.py found")
        
        # Try to import and validate
        try:
            sys.path.insert(0, str(Path.cwd()))
            import config
            cfg = config.Config()
            print(f"  Serial port: {cfg.SERIAL_PORT}")
            print(f"  Baud rate: {cfg.BAUD_RATE}")
            print(f"  Web port: {cfg.WEB_PORT}")
            print(f"  PLC address: {cfg.DEVICE_ADDRESS}")
        except Exception as e:
            print(f"✗ Configuration error: {e}")
    else:
        print("✗ config.py not found")

def check_gpio_hardware():
    """Check GPIO hardware availability"""
    print("\n=== GPIO Hardware ===")
    
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        
        # Test a safe GPIO pin
        test_pin = 18
        GPIO.setup(test_pin, GPIO.OUT)
        GPIO.output(test_pin, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(test_pin, GPIO.LOW)
        GPIO.cleanup()
        
        print("✓ GPIO hardware functional")
    except Exception as e:
        print(f"✗ GPIO test failed: {e}")

def check_log_files():
    """Check log files and permissions"""
    print("\n=== Log Files ===")
    
    log_file = Path("plc_web_bridge.log")
    if log_file.exists():
        size = log_file.stat().st_size
        print(f"✓ Application log exists ({size} bytes)")
    else:
        print("Application log not created yet")
    
    # Check systemd logs
    success, output, _ = run_command("journalctl -u plc-bridge --no-pager -n 5")
    if success and output:
        print("✓ Systemd logs accessible")
    else:
        print("No systemd logs found")

def test_modbus_simulation():
    """Test Modbus functionality in simulation mode"""
    print("\n=== Modbus Test ===")
    
    try:
        sys.path.insert(0, str(Path.cwd()))
        from config import Config
        from plc_communication import PLCCommunicator
        
        config = Config()
        plc = PLCCommunicator(config)
        
        # Test simulation mode
        status = plc.get_status()
        if status and 'connected' in status:
            print("✓ PLC communication module functional")
        else:
            print("✗ PLC communication test failed")
            
    except Exception as e:
        print(f"✗ Modbus test error: {e}")

def run_comprehensive_test():
    """Run all diagnostic tests"""
    print("Raspberry Pi PLC Bridge Diagnostics")
    print("=" * 50)
    
    check_python_environment()
    check_system_dependencies()
    check_serial_ports()
    check_network()
    check_service_status()
    check_configuration()
    check_gpio_hardware()
    check_log_files()
    test_modbus_simulation()
    
    print("\n" + "=" * 50)
    print("Diagnostics complete")
    print("\nRecommendations:")
    print("1. Fix any ✗ items shown above")
    print("2. Ensure PLC is connected and configured")
    print("3. Test with: ./start.sh")
    print("4. Access web interface at: http://[PI-IP]:5000")

if __name__ == "__main__":
    run_comprehensive_test()