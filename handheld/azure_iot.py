import os
import json
from azure.iot.device import IoTHubDeviceClient, Message
from position import Position

class AzureDevice:
    def __init__(self):
        connection_string = os.getenv("AZURE_IOT_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("Mandatory environment variable unset: AZURE_IOT_CONNECTION_STRING")
        self.client = IoTHubDeviceClient.create_from_connection_string(connection_string)
        self.client.connect()
        print("Azure IoT Hub device client connected.")
    
    # Use our position class as a wrapper for building, floor, and coordinate
    def send_telemetry(self, pos):
        if not isinstance(pos, Position): 
            return
        payload = json.dumps({
            "device_id": "handheld-1",
            "building_id": pos.building_id,
            "floor": pos.floor,
            "loc_north": pos.loc_north,
            "loc_east": pos.loc_east
        })
        message = Message(payload)
        message.content_type = "application/json"
        message.content_encoding = "utf-8"
        self.client.send_message(message)
        print(f"Sent telemetry to Azure:\r\n {payload}")
    
    def disconnect_client(self):
        if self.client:
            self.client.disconnect()
            print("Azure IoT Hub device client disconnected.")


def main():
    # Create AzureDevice with no parameters
    device = AzureDevice()
    
    try:
        # Create a sample Position object to send (matching Position class parameter order)
        sample_position = Position(
            loc_north=45.5,
            loc_east=122.3,
            building_id="Building-A",
            floor=3
        )
        
        # Call send_telemetry
        device.send_telemetry(sample_position)
        
    finally:
        # Always disconnect the client
        device.disconnect_client()


if __name__ == "__main__":
    main()