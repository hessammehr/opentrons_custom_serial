"""
MicroPython firmware for Raspberry Pi Pico - OpenTrons Custom Serial Module

This firmware demonstrates the JSON command protocol expected by the
OpenTrons custom serial module. It handles basic commands and responds
with JSON formatted messages.

Hardware: Raspberry Pi Pico
Communication: 115200 baud, JSON over USB serial
MicroPython: Version 1.20+

Installation:
1. Flash MicroPython to your Pi Pico
2. Copy this file as main.py to the Pico
3. Connect Pico to OpenTrons Flex via USB
"""

import json
import time
import machine
import sys
from machine import Pin

# Device information
DEVICE_NAME = "Pi Pico Custom Module"
FIRMWARE_VERSION = "1.0.0"
API_VERSION = "1.0"

# Built-in LED for status indication
led = Pin(25, Pin.OUT)

# Status variables
is_connected = False
start_time = time.ticks_ms()
temperature = 25.0
humidity = 50.0

def setup():
    """Initialize the device."""
    global start_time
    start_time = time.ticks_ms()
    led.off()
    
    # Send ready message
    send_response({
        "status": "ready", 
        "message": "Pi Pico Custom Module initialized"
    })

def handle_command(command_dict):
    """Handle incoming command and return response."""
    command = command_dict.get("command", "").upper()
    
    if command == "CONNECT":
        return handle_connect()
    elif command == "DISCONNECT":
        return handle_disconnect()
    elif command == "STATUS":
        return handle_status()
    elif command == "RESET":
        return handle_reset()
    elif command == "GET_VERSION":
        return handle_get_version()
    elif command == "SET_PARAMETER":
        return handle_set_parameter(command_dict)
    elif command == "GET_PARAMETER":
        return handle_get_parameter(command_dict)
    elif command == "CUSTOM_MEASUREMENT":
        return handle_custom_measurement(command_dict)
    elif command == "START_MEASUREMENT":
        return handle_start_measurement(command_dict)
    elif command == "GET_RESULTS":
        return handle_get_results()
    elif command == "BLINK_LED":
        return handle_blink_led(command_dict)
    else:
        return handle_unknown_command(command)

def handle_connect():
    """Handle connect command."""
    global is_connected
    is_connected = True
    led.on()
    return {
        "status": "success",
        "message": f"Connected to {DEVICE_NAME}",
        "data": {
            "device_name": DEVICE_NAME,
            "firmware_version": FIRMWARE_VERSION
        }
    }

def handle_disconnect():
    """Handle disconnect command."""
    global is_connected
    is_connected = False
    led.off()
    return {
        "status": "success",
        "message": f"Disconnected from {DEVICE_NAME}"
    }

def handle_status():
    """Handle status command."""
    global temperature, humidity
    
    # Update uptime
    uptime = time.ticks_diff(time.ticks_ms(), start_time) // 1000
    
    # Simulate some changing values
    temperature = 25.0 + (time.ticks_ms() % 10000) / 1000 - 5
    humidity = 50.0 + (time.ticks_ms() % 20000) / 1000 - 10
    
    return {
        "status": "success",
        "message": "Device status retrieved",
        "data": {
            "connected": is_connected,
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2),
            "uptime": uptime,
            "led_state": led.value()
        }
    }

def handle_reset():
    """Handle reset command."""
    global start_time, temperature, humidity
    
    start_time = time.ticks_ms()
    temperature = 25.0
    humidity = 50.0
    led.off()
    
    return {
        "status": "success",
        "message": f"{DEVICE_NAME} reset successfully"
    }

def handle_get_version():
    """Handle get version command."""
    return {
        "status": "success",
        "message": "Version information retrieved",
        "data": {
            "device_name": DEVICE_NAME,
            "firmware_version": FIRMWARE_VERSION,
            "api_version": API_VERSION,
            "micropython_version": sys.version,
            "platform": "Raspberry Pi Pico"
        }
    }

def handle_set_parameter(command_dict):
    """Handle set parameter command."""
    param_name = command_dict.get("parameter")
    param_value = command_dict.get("value")
    
    if not param_name:
        return {
            "status": "error",
            "message": "Parameter name is required"
        }
    
    # Handle specific parameters
    if param_name == "led_state":
        led_state = param_value in ["true", "1", True, 1]
        led.value(led_state)
        
    return {
        "status": "success",
        "message": f"Parameter '{param_name}' set to '{param_value}'",
        "data": {
            "parameter": param_name,
            "value": param_value
        }
    }

def handle_get_parameter(command_dict):
    """Handle get parameter command."""
    param_name = command_dict.get("parameter")
    
    if not param_name:
        return {
            "status": "error",
            "message": "Parameter name is required"
        }
    
    # Handle specific parameters
    if param_name == "led_state":
        param_value = "true" if led.value() else "false"
    elif param_name == "temperature":
        param_value = round(temperature, 2)
    elif param_name == "humidity":
        param_value = round(humidity, 2)
    else:
        return {
            "status": "error",
            "message": f"Parameter '{param_name}' not found"
        }
    
    return {
        "status": "success",
        "message": f"Parameter '{param_name}' retrieved",
        "data": {
            "parameter": param_name,
            "value": param_value
        }
    }

def handle_custom_measurement(command_dict):
    """Handle custom measurement command."""
    param1 = command_dict.get("parameter1", 0)
    param2 = command_dict.get("parameter2", "")
    
    # Simulate some measurement (read ADC, sensor, etc.)
    # Pi Pico has built-in temperature sensor
    sensor_temp = machine.ADC(4)
    reading = sensor_temp.read_u16() * 3.3 / (65535)
    temperature_c = 27 - (reading - 0.706) / 0.001721
    
    return {
        "status": "success",
        "message": "Custom measurement completed",
        "data": {
            "internal_temperature": round(temperature_c, 2),
            "parameter1": param1,
            "parameter2": param2,
            "timestamp": time.ticks_ms()
        }
    }

def handle_start_measurement(command_dict):
    """Handle start measurement command."""
    duration = command_dict.get("duration", 10)
    
    # Blink LED to indicate measurement in progress
    for _ in range(3):
        led.on()
        time.sleep_ms(100)
        led.off()
        time.sleep_ms(100)
    
    return {
        "status": "success",
        "message": "Measurement started",
        "data": {
            "duration": duration,
            "started_at": time.ticks_ms()
        }
    }

def handle_get_results():
    """Handle get results command."""
    # Get internal temperature sensor reading
    sensor_temp = machine.ADC(4)
    reading = sensor_temp.read_u16() * 3.3 / (65535)
    internal_temp = 27 - (reading - 0.706) / 0.001721
    
    return {
        "status": "success",
        "message": "Measurement results retrieved",
        "data": {
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2),
            "internal_temperature": round(internal_temp, 2),
            "uptime": time.ticks_diff(time.ticks_ms(), start_time) // 1000
        }
    }

def handle_blink_led(command_dict):
    """Handle LED blink command (Pi Pico specific)."""
    count = command_dict.get("count", 3)
    delay = command_dict.get("delay", 200)
    
    for i in range(count):
        led.on()
        time.sleep_ms(delay)
        led.off()
        time.sleep_ms(delay)
    
    return {
        "status": "success",
        "message": f"LED blinked {count} times",
        "data": {
            "count": count,
            "delay": delay
        }
    }

def handle_unknown_command(command):
    """Handle unknown command."""
    return {
        "status": "error",
        "message": f"Unknown command: {command}"
    }

def send_response(response):
    """Send JSON response."""
    try:
        json_str = json.dumps(response)
        print(json_str)
    except Exception as e:
        print(json.dumps({
            "status": "error", 
            "message": f"JSON serialization error: {str(e)}"
        }))

def read_command():
    """Read command from serial input."""
    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        line = sys.stdin.readline().strip()
        return line
    return None

def main():
    """Main program loop."""
    setup()
    
    print(f"# {DEVICE_NAME} v{FIRMWARE_VERSION} ready")
    print(f"# Commands: CONNECT, STATUS, CUSTOM_MEASUREMENT, BLINK_LED, etc.")
    
    command_buffer = ""
    
    while True:
        try:
            # Check for incoming data
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                char = sys.stdin.read(1)
                if char == '\n':
                    if command_buffer.strip():
                        try:
                            command_dict = json.loads(command_buffer.strip())
                            response = handle_command(command_dict)
                            send_response(response)
                        except json.JSONDecodeError:
                            send_response({
                                "status": "error",
                                "message": "Invalid JSON format"
                            })
                        except Exception as e:
                            send_response({
                                "status": "error", 
                                "message": f"Command error: {str(e)}"
                            })
                    command_buffer = ""
                else:
                    command_buffer += char
            
            # Small delay to prevent busy waiting
            time.sleep_ms(10)
            
        except KeyboardInterrupt:
            print("\n# Shutting down...")
            led.off()
            break
        except Exception as e:
            send_response({
                "status": "error",
                "message": f"System error: {str(e)}"
            })

# For MicroPython, we need select for non-blocking input
try:
    import select
except ImportError:
    # Fallback for systems without select
    import sys
    
    def simple_main():
        """Simplified main loop without select."""
        setup()
        print(f"# {DEVICE_NAME} v{FIRMWARE_VERSION} ready (simple mode)")
        
        while True:
            try:
                line = input()  # This will block until newline
                if line.strip():
                    try:
                        command_dict = json.loads(line.strip())
                        response = handle_command(command_dict)
                        send_response(response)
                    except json.JSONDecodeError:
                        send_response({
                            "status": "error",
                            "message": "Invalid JSON format"
                        })
            except KeyboardInterrupt:
                print("\n# Shutting down...")
                led.off()
                break
            except EOFError:
                break
    
    main = simple_main

if __name__ == "__main__":
    main()