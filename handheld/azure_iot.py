import os
import json
from azure.iot.device import IoTHubDeviceClient, Message

class AzureDevice:
    def __init__(self):
        connection_string = os.getenv("AZURE_IOT_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("Mandatory environment variable unset: AZURE_IOT_CONNECTION_STRING")
        self.client = IoTHubDeviceClient.create_from_connection_string(connection_string)

    def send_telemetry(self, pos):
        pass