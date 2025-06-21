"""Mock hardware simulator for development and testing."""

import json
import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MockSerialDevice:
    """Mock serial device for testing without hardware."""
    
    def __init__(self, device_name: str = "MockDevice", firmware_version: str = "1.0.0"):
        """Initialize mock device.
        
        Args:
            device_name: Name of the mock device
            firmware_version: Firmware version to report
        """
        self.device_name = device_name
        self.firmware_version = firmware_version
        self.is_connected = False
        self.parameters = {}
        self.status_data = {
            "temperature": 25.0,
            "humidity": 50.0,
            "uptime": 0,
        }
        self._start_time = time.time()
    
    def handle_command(self, command_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming command and return response.
        
        Args:
            command_dict: Command dictionary from JSON
            
        Returns:
            Response dictionary
        """
        command = command_dict.get("command", "").upper()
        
        if command == "CONNECT":
            return self._handle_connect()
        elif command == "DISCONNECT":
            return self._handle_disconnect()
        elif command == "STATUS":
            return self._handle_status()
        elif command == "RESET":
            return self._handle_reset()
        elif command == "GET_VERSION":
            return self._handle_get_version()
        elif command == "SET_PARAMETER":
            return self._handle_set_parameter(command_dict)
        elif command == "GET_PARAMETER":
            return self._handle_get_parameter(command_dict)
        else:
            return self._handle_unknown_command(command)
    
    def _handle_connect(self) -> Dict[str, Any]:
        """Handle connect command."""
        self.is_connected = True
        return {
            "status": "success",
            "message": f"Connected to {self.device_name}",
            "data": {
                "device_name": self.device_name,
                "firmware_version": self.firmware_version
            }
        }
    
    def _handle_disconnect(self) -> Dict[str, Any]:
        """Handle disconnect command."""
        self.is_connected = False
        return {
            "status": "success",
            "message": f"Disconnected from {self.device_name}"
        }
    
    def _handle_status(self) -> Dict[str, Any]:
        """Handle status command."""
        # Update uptime
        self.status_data["uptime"] = int(time.time() - self._start_time)
        
        # Simulate some changing values
        self.status_data["temperature"] = 25.0 + (time.time() % 10) - 5
        self.status_data["humidity"] = 50.0 + (time.time() % 20) - 10
        
        return {
            "status": "success",
            "message": "Device status retrieved",
            "data": {
                "connected": self.is_connected,
                **self.status_data
            }
        }
    
    def _handle_reset(self) -> Dict[str, Any]:
        """Handle reset command."""
        self.parameters.clear()
        self._start_time = time.time()
        self.status_data["uptime"] = 0
        
        return {
            "status": "success",
            "message": f"{self.device_name} reset successfully"
        }
    
    def _handle_get_version(self) -> Dict[str, Any]:
        """Handle get version command."""
        return {
            "status": "success",
            "message": "Version information retrieved",
            "data": {
                "device_name": self.device_name,
                "firmware_version": self.firmware_version,
                "api_version": "1.0",
                "build_date": "2024-01-01"
            }
        }
    
    def _handle_set_parameter(self, command_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Handle set parameter command."""
        param_name = command_dict.get("parameter")
        param_value = command_dict.get("value")
        
        if not param_name:
            return {
                "status": "error",
                "message": "Parameter name is required"
            }
        
        self.parameters[param_name] = param_value
        
        return {
            "status": "success",
            "message": f"Parameter '{param_name}' set to '{param_value}'",
            "data": {
                "parameter": param_name,
                "value": param_value
            }
        }
    
    def _handle_get_parameter(self, command_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get parameter command."""
        param_name = command_dict.get("parameter")
        
        if not param_name:
            return {
                "status": "error",
                "message": "Parameter name is required"
            }
        
        if param_name not in self.parameters:
            return {
                "status": "error",
                "message": f"Parameter '{param_name}' not found"
            }
        
        return {
            "status": "success",
            "message": f"Parameter '{param_name}' retrieved",
            "data": {
                "parameter": param_name,
                "value": self.parameters[param_name]
            }
        }
    
    def _handle_unknown_command(self, command: str) -> Dict[str, Any]:
        """Handle unknown command."""
        return {
            "status": "error",
            "message": f"Unknown command: {command}"
        }


class MockSerialHandler:
    """Mock serial handler that simulates serial communication."""
    
    def __init__(self, mock_device: Optional[MockSerialDevice] = None):
        """Initialize mock serial handler.
        
        Args:
            mock_device: MockSerialDevice instance to use
        """
        self.mock_device = mock_device or MockSerialDevice()
        self.is_connected = False
    
    def connect(self) -> None:
        """Simulate connection."""
        self.is_connected = True
        logger.info("Mock serial connection established")
    
    def disconnect(self) -> None:
        """Simulate disconnection."""
        self.is_connected = False
        logger.info("Mock serial connection closed")
    
    def send_json_command(self, command_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON command to mock device.
        
        Args:
            command_dict: Command dictionary
            
        Returns:
            Response dictionary from mock device
        """
        if not self.is_connected:
            return {
                "status": "error",
                "message": "Not connected to device"
            }
        
        logger.debug(f"Mock device received command: {command_dict}")
        response = self.mock_device.handle_command(command_dict)
        logger.debug(f"Mock device response: {response}")
        
        return response