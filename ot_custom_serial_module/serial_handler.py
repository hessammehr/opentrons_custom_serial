"""Serial communication handler for custom hardware modules."""

import json
import time
import logging
from typing import Any, Dict, Optional, Union, List
import serial
import serial.tools.list_ports
from threading import Lock, Event
from contextlib import contextmanager

class SerialError(Exception):
    """Base exception for serial module errors."""
    pass

logger = logging.getLogger(__name__)


class SerialHandler:
    """Handles serial communication with custom hardware modules."""
    
    DEFAULT_BAUDRATE = 115200
    DEFAULT_TIMEOUT = 5.0
    DEFAULT_WRITE_TIMEOUT = 2.0
    
    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = DEFAULT_TIMEOUT,
        write_timeout: float = DEFAULT_WRITE_TIMEOUT,
        auto_discover: bool = True,
        vid_pid_filter: Optional[List[tuple]] = None,
    ) -> None:
        """Initialize serial handler.
        
        Args:
            port: Serial port path (e.g., '/dev/ttyACM0'). If None, will auto-discover.
            baudrate: Serial communication baud rate.
            timeout: Read timeout in seconds.
            write_timeout: Write timeout in seconds.
            auto_discover: Whether to auto-discover devices if port is None.
            vid_pid_filter: List of (vendor_id, product_id) tuples for device filtering.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.write_timeout = write_timeout
        self.auto_discover = auto_discover
        self.vid_pid_filter = vid_pid_filter or []
        
        self._serial: Optional[serial.Serial] = None
        self._lock = Lock()
        self._connected = Event()
        
    @property
    def is_connected(self) -> bool:
        """Check if the serial connection is active."""
        return self._connected.is_set() and self._serial is not None and self._serial.is_open
    
    def discover_devices(self) -> List[Dict[str, Any]]:
        """Discover available serial devices.
        
        Returns:
            List of device information dictionaries.
        """
        devices = []
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            device_info = {
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid,
                'vid': port.vid,
                'pid': port.pid,
                'serial_number': port.serial_number,
                'manufacturer': port.manufacturer,
                'product': port.product,
            }
            
            # Apply VID/PID filter if specified
            if self.vid_pid_filter:
                if any((port.vid, port.pid) == (vid, pid) for vid, pid in self.vid_pid_filter):
                    devices.append(device_info)
            else:
                devices.append(device_info)
                
        return devices
    
    def auto_discover_port(self) -> Optional[str]:
        """Auto-discover the best matching serial port.
        
        Returns:
            The device path of the best matching port, or None if not found.
        """
        devices = self.discover_devices()
        
        if not devices:
            logger.warning("No serial devices found during auto-discovery")
            return None
            
        # If we have VID/PID filters, prefer those matches
        if self.vid_pid_filter:
            for device in devices:
                if any((device['vid'], device['pid']) == (vid, pid) for vid, pid in self.vid_pid_filter):
                    logger.info(f"Auto-discovered device: {device['device']} ({device['description']})")
                    return device['device']
        
        # Otherwise, return the first available device
        device = devices[0]
        logger.info(f"Auto-discovered device: {device['device']} ({device['description']})")
        return device['device']
    
    def connect(self) -> None:
        """Establish serial connection."""
        with self._lock:
            if self.is_connected:
                logger.debug("Already connected to serial device")
                return
                
            # Auto-discover port if not specified
            if not self.port and self.auto_discover:
                self.port = self.auto_discover_port()
                
            if not self.port:
                raise SerialError("No serial port specified and auto-discovery failed")
                
            try:
                self._serial = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=self.timeout,
                    write_timeout=self.write_timeout,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                )
                
                # Wait a moment for the connection to stabilize
                time.sleep(0.1)
                
                # Clear any stale data in buffers
                self._serial.reset_input_buffer()
                self._serial.reset_output_buffer()
                
                self._connected.set()
                logger.info(f"Connected to serial device on {self.port}")
                
            except serial.SerialException as e:
                raise SerialError(f"Failed to connect to {self.port}: {e}")
    
    def disconnect(self) -> None:
        """Close serial connection."""
        with self._lock:
            if self._serial and self._serial.is_open:
                try:
                    self._serial.close()
                    logger.info(f"Disconnected from serial device on {self.port}")
                except Exception as e:
                    logger.warning(f"Error during disconnect: {e}")
                finally:
                    self._connected.clear()
                    self._serial = None
    
    @contextmanager
    def connection(self):
        """Context manager for serial connection."""
        self.connect()
        try:
            yield self
        finally:
            self.disconnect()
    
    def write_raw(self, data: bytes) -> None:
        """Write raw bytes to serial port.
        
        Args:
            data: Raw bytes to send.
        """
        if not self.is_connected:
            raise SerialError("Not connected to serial device")
            
        try:
            with self._lock:
                bytes_written = self._serial.write(data)
                if bytes_written != len(data):
                    raise SerialError(f"Failed to write all data. Expected {len(data)}, wrote {bytes_written}")
                self._serial.flush()
                
        except (serial.SerialTimeoutException, serial.SerialException) as e:
            raise SerialError(f"Serial write error: {e}")
    
    def read_raw(self, size: int = 1) -> bytes:
        """Read raw bytes from serial port.
        
        Args:
            size: Number of bytes to read.
            
        Returns:
            Raw bytes read from the port.
        """
        if not self.is_connected:
            raise SerialError("Not connected to serial device")
            
        try:
            with self._lock:
                data = self._serial.read(size)
                if not data:
                    raise SerialError("Read timeout")
                return data
                
        except serial.SerialException as e:
            raise SerialError(f"Serial read error: {e}")
    
    def write_line(self, message: str, encoding: str = 'utf-8') -> None:
        """Write a line of text to serial port.
        
        Args:
            message: Text message to send.
            encoding: Text encoding to use.
        """
        line = f"{message}\n"
        self.write_raw(line.encode(encoding))
    
    def read_line(self, encoding: str = 'utf-8') -> str:
        """Read a line of text from serial port.
        
        Args:
            encoding: Text encoding to use.
            
        Returns:
            Line read from the port, with newline stripped.
        """
        if not self.is_connected:
            raise SerialCommunicationError("Not connected to serial device")
            
        try:
            with self._lock:
                line = self._serial.readline()
                if not line:
                    raise SerialError("Read timeout")
                return line.decode(encoding).rstrip('\r\n')
                
        except (UnicodeDecodeError, serial.SerialException) as e:
            raise SerialError(f"Serial read error: {e}")
    
    def send_command(self, command: str, **kwargs) -> str:
        """Send a command and wait for response.
        
        Args:
            command: Command string to send.
            **kwargs: Additional parameters to include in command.
            
        Returns:
            Response string from the device.
        """
        if kwargs:
            # Build command with parameters
            cmd_dict = {'command': command, **kwargs}
            cmd_json = json.dumps(cmd_dict)
            self.write_line(cmd_json)
        else:
            self.write_line(command)
            
        return self.read_line()
    
    def send_json_command(self, command_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON command and parse JSON response.
        
        Args:
            command_dict: Command dictionary to send as JSON.
            
        Returns:
            Parsed response dictionary.
        """
        cmd_json = json.dumps(command_dict)
        self.write_line(cmd_json)
        
        response_line = self.read_line()
        try:
            return json.loads(response_line)
        except json.JSONDecodeError as e:
            raise SerialError(f"Failed to parse JSON response: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.disconnect()
        except Exception:
            pass