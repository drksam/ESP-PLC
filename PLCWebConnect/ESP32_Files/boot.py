"""
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
print("=" * 50)