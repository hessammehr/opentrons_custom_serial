"""Example OpenTrons protocol using the custom serial module."""

from opentrons import protocol_api

# Metadata
metadata = {
    'protocolName': 'Custom Serial Module Example',
    'author': 'OpenTrons Custom Module Developer',
    'description': 'Example protocol demonstrating custom serial module usage',
    'apiLevel': '2.14'
}


def run(protocol: protocol_api.ProtocolContext):
    """Run the example protocol.
    
    Args:
        protocol: OpenTrons protocol context
    """
    # Load the custom serial module
    # Using the model name (recommended)
    custom_module = protocol.load_module('customSerialModuleV1', 1)
    
    # Alternative: using the alias
    # custom_module = protocol.load_module('custom serial module', 1)
    
    # Example labware (if your module supports labware)
    # plate = custom_module.load_labware('custom_plate_96_wellplate_200ul')
    
    # Get module status
    protocol.comment("Getting module status...")
    status = custom_module.get_device_status()
    protocol.comment(f"Module status: {status}")
    
    # Send a custom command
    protocol.comment("Sending custom command to module...")
    response = custom_module.send_command("CUSTOM_MEASUREMENT", parameter1=42, parameter2="test")
    protocol.comment(f"Command response: {response}")
    
    # Example of interacting with the module during protocol execution
    protocol.comment("Starting measurement sequence...")
    
    # Send start measurement command
    custom_module.send_command("START_MEASUREMENT", duration=30)
    
    # Wait for measurement to complete (in real protocol, you might do other things)
    protocol.delay(seconds=30)
    
    # Get measurement results
    results = custom_module.send_command("GET_RESULTS")
    protocol.comment(f"Measurement results: {results}")
    
    # Reset the module
    protocol.comment("Resetting module...")
    custom_module.reset_device()
    
    protocol.comment("Protocol completed successfully!")


# For simulation/testing
if __name__ == "__main__":
    # This would be used for testing the protocol logic
    print("Example protocol for custom serial module")
    print("This protocol demonstrates:")
    print("- Loading a custom serial module")
    print("- Getting module status")
    print("- Sending custom commands")
    print("- Handling responses")
    print("- Resetting the module")