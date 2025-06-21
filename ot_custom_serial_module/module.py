"""Custom serial module for OpenTrons Flex."""

import asyncio
import logging
from typing import Any, Dict, Optional, Callable, List
from opentrons.hardware_control.modules.mod_abc import AbstractModule
from opentrons.hardware_control.modules.types import USBPort, ModuleType
from opentrons.hardware_control.execution_manager import ExecutionManager

from .serial_handler import SerialHandler, SerialError

logger = logging.getLogger(__name__)


class CustomSerialModule(AbstractModule):
    """Custom serial communication module for OpenTrons Flex."""
    
    MODULE_TYPE = ModuleType.CUSTOM_SERIAL
    
    def __init__(
        self,
        port: str,
        usb_port: USBPort,
        execution_manager: ExecutionManager,
        hw_control_loop: asyncio.AbstractEventLoop,
        disconnected_callback: Optional[Callable] = None,
        sim_serial_number: Optional[str] = None,
    ):
        """Initialize the custom serial module.
        
        Args:
            port: Serial port path (e.g., '/dev/ttyACM0')
            usb_port: USB port information from OpenTrons
            execution_manager: OpenTrons execution manager
            hw_control_loop: Hardware control event loop
            disconnected_callback: Called when module disconnects
            sim_serial_number: Serial number for simulation mode
        """
        super().__init__(
            port=port,
            usb_port=usb_port,
            execution_manager=execution_manager,
            hw_control_loop=hw_control_loop,
            disconnected_callback=disconnected_callback,
        )
        
        self._is_simulated = port == "virtual"
        self._sim_serial_number = sim_serial_number
        
        # Initialize serial communication
        if not self._is_simulated:
            self._serial_handler = SerialHandler(
                port=port,
                auto_discover=True,
                vid_pid_filter=[(0x2341, 0x0043), (0x2E8A, 0x0005)]  # Arduino Uno, Pi Pico
            )
        else:
            self._serial_handler = None
            
        self._device_info = {
            "model": "Custom Serial Module",
            "version": "1.0.0",
            "serial": self._sim_serial_number or "SIMULATION",
        }
        self._status = "disconnected"
        self._live_data = {}
        
    @classmethod
    async def build(
        cls,
        port: str,
        usb_port: USBPort,
        execution_manager: ExecutionManager,
        hw_control_loop: asyncio.AbstractEventLoop,
        disconnected_callback: Optional[Callable] = None,
        sim_serial_number: Optional[str] = None,
    ) -> "CustomSerialModule":
        """Build and initialize the module.
        
        This is the factory method OpenTrons uses to create module instances.
        """
        module = cls(
            port=port,
            usb_port=usb_port,
            execution_manager=execution_manager,
            hw_control_loop=hw_control_loop,
            disconnected_callback=disconnected_callback,
            sim_serial_number=sim_serial_number,
        )
        
        # Initialize connection if not simulated
        if not module._is_simulated:
            try:
                await module._connect_async()
            except Exception as e:
                logger.error(f"Failed to connect to serial module: {e}")
                module._status = "error"
        else:
            module._status = "connected"
            
        return module
    
    async def _connect_async(self) -> None:
        """Connect to the serial device asynchronously."""
        if self._serial_handler:
            def connect():
                self._serial_handler.connect()
                # Try to get device info
                try:
                    response = self._serial_handler.send_json_command({"command": "STATUS"})
                    if response.get("status") == "success":
                        self._status = "connected"
                        self._live_data.update(response.get("data", {}))
                    else:
                        self._status = "error"
                except Exception as e:
                    logger.warning(f"Could not get device status: {e}")
                    self._status = "connected"  # Still connected, just no status
                    
            await asyncio.get_event_loop().run_in_executor(None, connect)
    
    @property
    def device_info(self) -> Dict[str, Any]:
        """Static device information."""
        return self._device_info.copy()
    
    @property
    def is_simulated(self) -> bool:
        """Check if module is in simulation mode."""
        return self._is_simulated
    
    @property
    def live_data(self) -> Dict[str, Any]:
        """Dynamic module data."""
        return self._live_data.copy()
    
    @property
    def status(self) -> str:
        """Current module status."""
        return self._status
    
    @property
    def model(self) -> str:
        """Module model name."""
        return self._device_info["model"]
    
    @property
    def name(self) -> str:
        """Short module name."""
        return "CustomSerial"
    
    async def deactivate(self) -> None:
        """Deactivate the module."""
        if not self._is_simulated and self._serial_handler:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self._serial_handler.send_json_command, {"command": "DISCONNECT"}
                )
            except Exception as e:
                logger.warning(f"Error during deactivation: {e}")
            finally:
                self._status = "disconnected"
    
    def bootloader(self) -> Callable:
        """Return a callable for firmware uploads."""
        def upload_firmware(firmware_path: str) -> bool:
            """Upload firmware to the device."""
            logger.info(f"Firmware upload requested: {firmware_path}")
            if self._is_simulated:
                logger.info("Simulated firmware upload successful")
                return True
            else:
                logger.warning("Firmware upload not implemented for real hardware")
                return False
        
        return upload_firmware
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.deactivate()
        if not self._is_simulated and self._serial_handler:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self._serial_handler.disconnect
                )
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
    
    # Custom methods for user interaction
    
    async def send_command(self, command: str, **params) -> Dict[str, Any]:
        """Send a command to the connected device.
        
        Args:
            command: Command string to send
            **params: Additional parameters
            
        Returns:
            Response dictionary from the device
        """
        if self._is_simulated:
            return {
                "status": "success",
                "message": f"Simulated command: {command}",
                "data": params
            }
        
        if not self._serial_handler:
            raise SerialError("Module not properly initialized")
        
        cmd_dict = {"command": command}
        if params:
            cmd_dict.update(params)
        
        return await asyncio.get_event_loop().run_in_executor(
            None, self._serial_handler.send_json_command, cmd_dict
        )
    
    async def get_device_status(self) -> Dict[str, Any]:
        """Get current device status."""
        return await self.send_command("STATUS")
    
    async def reset_device(self) -> Dict[str, Any]:
        """Reset the connected device."""
        response = await self.send_command("RESET")
        if response.get("status") == "success":
            self._status = "connected"
        return response
    
    def discover_devices(self) -> List[Dict[str, Any]]:
        """Discover available serial devices."""
        if self._is_simulated:
            return [{"device": "virtual", "description": "Simulated device"}]
        
        if self._serial_handler:
            return self._serial_handler.discover_devices()
        return []