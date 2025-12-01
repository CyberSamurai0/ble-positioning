# Use the Bluetooth Low Energy platform Agnostic Klient (BLEAK) library
import asyncio
from bleak import BleakScanner
import tty_color as color
import position
import azure_api as cloud
from local_web import API
from sensors import SensorCache


async def main():
    print("CNIT 546 BLE Positioning")
    print("")
    print("Scan Results:")

    # Store calculated position value
    pos = position.Position()

    sensors = SensorCache(5)

    # Create Quart endpoint
    web = API(pos)
    server_task = asyncio.create_task(web.run())

    # Reference: https://bleak.readthedocs.io/en/latest/api/scanner.html#starting-and-stopping
    stop_event = asyncio.Event()

    # device: https://bleak.readthedocs.io/en/latest/api/index.html#bleak.backends.device.BLEDevice
    # adv_data: https://bleak.readthedocs.io/en/latest/backends/index.html#bleak.backends.scanner.AdvertisementData
    def callback(device, adv_data):
        if device.name != "blepos":
            return

        #stop_event.set()

        # Print MAC Address and the hardcoded friendly name
        print(f"Device: {color.blue(device.address)} ({color.blue(device.name)})")

        print(f"\tLocal Name: {color.green(adv_data.local_name)}")

        # Print the manufacturer's data payload.
        # This traditionally consists of an integer ID assigned to the manufacturer
        # and a bytestring data payload. UTF-8 decoding tends to error :(
        # Manufacturer IDs: https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Assigned_Numbers/out/en/Assigned_Numbers.pdf#page=217
        print("\tManufacturer Data: {")
        for manufacturer_id, value in adv_data.manufacturer_data.items():
            print(f"\t\t{color.yellow(hex(manufacturer_id))}: {color.green(value)}")
        print("\t}")

        # This is an unstable field and probably does not need to be used.
        # print(f"\tPlatform Data: ({adv_data.platform_data})")

        # So far, this field is empty on all received packets. That may not hold
        # true once we dive into testing!
        # print(f"\tService Data: {adv_data.service_data}")
        print("\tService Data: {")
        for uuid, value in adv_data.service_data.items():
            print(color.yellow(f"\t\t0x{uuid[4:8]}") + ":", color.green(value))
        print("\t}")

        #print(f"\tPayload: \x1b[32m{adv_data.manufacturer_data}\x1b[0m")
        print(f"\tRSSI: \x1b[33m{adv_data.rssi}\x1b[0m")
        #print(f"\tTx Power: \x1b[33m{adv_data.tx_power}\x1b[0m")
        # print(adv_data)


    async with BleakScanner(callback) as scanner:
        await stop_event.wait()


if __name__ == '__main__':
    asyncio.run(main())