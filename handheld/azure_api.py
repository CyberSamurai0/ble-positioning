import os
import requests

reg_endpoint = os.getenv("AZURE_REGISTER_URL")
patch_endpoint = os.getenv("AZURE_UPDATE_URL")

# Function to register the current device with the Azure IoT Hub
def register():
    pass

# Function to update the latest telemetry of the current device on Azure IoT Hub
def push(x, y, building_id=None, floor=None):
    # Set Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('AZURE_AUTH_TOKEN')}", # Load this to memory only when we need it
        "X-CNIT-546": True,
    }

    # Build Body
    body = {
        "loc_north": x,
        "loc_east": y,
        "building": building_id,
        "floor": floor
    }

    response = requests.post(patch_endpoint, json=body, headers=headers)
    return response.status_code