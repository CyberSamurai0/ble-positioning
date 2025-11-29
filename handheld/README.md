# Handheld
This subsystem was written in Python to maximize portability.

### Setup
1. Download a Python execution environment.
2. Run `pip install -r requirements.txt`
3. Appropriately set the following environment variables:
    1. `AZURE_AUTH_TOKEN` - Signed JWT
    2. `AZURE_REGISTER_URL` - Azure IoT Hub endpoint URL for registering the current device
    3. `AZURE_UPDATE_URL` - Azure IoT Hub endpoint URL for providing updated telemetry
4. Run `python main.py`
5. Review instantaneous scan results