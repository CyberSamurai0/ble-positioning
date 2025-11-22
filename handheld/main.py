# Use the Bluetooth Low Energy platform Agnostic Klient (BLEAK) library
import asyncio
from bleak import BleakScanner

async def main():
    print("CNIT 546 BLE Positioning")
    print("")
    print("Scan Results:")

    # Reference: https://bleak.readthedocs.io/en/latest/api/scanner.html#starting-and-stopping
    stop_event = asyncio.Event()

    # device: https://bleak.readthedocs.io/en/latest/api/index.html#bleak.backends.device.BLEDevice
    # adv_data: https://bleak.readthedocs.io/en/latest/backends/index.html#bleak.backends.scanner.AdvertisementData
    def callback(device, adv_data):
        stop_event.set()


    async with BleakScanner(callback) as scanner:
        await stop_event.wait()


if __name__ == '__main__':
    asyncio.run(main())