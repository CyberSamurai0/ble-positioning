# Use the Bluetooth Low Energy platform Agnostic Klient (BLEAK) library
import asyncio
from bleak import BleakScanner
import tty_color as color

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
        print(f"Device: {color.blue(device.address)} ({color.blue(device.name)})")

        print("\tManufacturer Data: {")
        for manufacturer_id, value in adv_data.manufacturer_data.items():
            print(f"\t\t{color.yellow(manufacturer_id)}: {color.green(value)}")
        print("\t}")

        # print(f"\tPlatform Data: ({adv_data.platform_data})")

        print(f"\tService Data: {adv_data.service_data}")
        # print("\tService Data:")
        # for key, value in adv_data.service_data.items():
        #     print(color.green(f"\t\t\"{key}\"") + ":", color.green(value))
        # print("\t")

        #print(f"\tPayload: \x1b[32m{adv_data.manufacturer_data}\x1b[0m")
        print(f"\tRSSI: \x1b[33m{adv_data.rssi}\x1b[0m")
        print(f"\tTx Power: \x1b[33m{adv_data.tx_power}\x1b[0m")
        # print(adv_data)


    async with BleakScanner(callback) as scanner:
        await stop_event.wait()


if __name__ == '__main__':
    asyncio.run(main())