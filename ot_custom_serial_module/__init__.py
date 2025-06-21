"""
OpenTrons Custom Serial Module

A custom hardware module for OpenTrons Flex that enables serial communication
with Arduino, Pi Pico, and other microcontroller-based devices.
"""

__version__ = "0.1.0"

from .module import CustomSerialModule
from .serial_handler import SerialError

__all__ = [
    "CustomSerialModule",
    "SerialError",
]