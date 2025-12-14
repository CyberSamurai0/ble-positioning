import asyncio
# Use the Bluetooth Low Energy platform Agnostic Klient (BLEAK) library
from bleak import BleakScanner
import tty_color as color
from position import Position
import azure_api as cloud
from local_web import API
from sensors import SensorCache
from numpy import frombuffer, astype
from azure_iot import AzureDevice
import os

DEBUG = False

# TODO LIST
# Test trilateration

async def main():
    print("CNIT 546 BLE Positioning")
    print("")
    print("Scan Results:")

    # Store calculated position value
    pos = Position()

    beacons = SensorCache(5)

    # Create Quart endpoint
    web = API(pos, beacons)
    server_task = asyncio.create_task(web.run())

    # Reference: https://bleak.readthedocs.io/en/latest/api/scanner.html#starting-and-stopping
    stop_event = asyncio.Event()

    # device: https://bleak.readthedocs.io/en/latest/api/index.html#bleak.backends.device.BLEDevice
    # adv_data: https://bleak.readthedocs.io/en/latest/backends/index.html#bleak.backends.scanner.AdvertisementData
    def callback(device, adv_data):
        if device.name != "blepos":
            return


        for uuid, value in adv_data.service_data.items():
            # Check if this is the Indoor Positioning Service
            if uuid[4:8] == "1821" and len(value) == 7:
                building_id = int.from_bytes(value[0:2], byteorder='big')
                floor = value[2]
                # Use numpy float16 type based on big-endian buffer
                # ">f2" : '>' means big endian, 'f' means float, '2' means 2 bytes
                # Once we have float16, convert to native float for more precise math
                loc_north = frombuffer(value[3:5], dtype=">f2")[0].astype(float)
                loc_east = frombuffer(value[5:7], dtype=">f2")[0].astype(float)

                beacons.record_sensor(Position(loc_north, loc_east, building_id, floor), adv_data.rssi)

                if DEBUG:
                    print_adv(device, adv_data, malformed=False)
                return # Anything after this point implies a malformed/nonstandard payload


        # Use this if we want to stop scanning for any reason
        #stop_event.set()

        print(color.red("[!!!] MALFORMED PAYLOAD [!!!]"))
        print_adv(device, adv_data, malformed=True)


    async with BleakScanner(callback) as scanner:
        await stop_event.wait()


def print_adv(device, adv_data, malformed=False):
    # Print MAC Address and the hardcoded friendly name
    print(f"Device: {color.blue(device.address)} ({color.blue(device.name)})")

    print(f"\tLocal Name: {color.green(adv_data.local_name)}")

    # Print the manufacturer's data payload.
    # This traditionally consists of an integer ID assigned to the manufacturer
    # and a bytestring data payload that is static or not service-related.
    # Manufacturer IDs: https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Assigned_Numbers/out/en/Assigned_Numbers.pdf#page=217
    print("\tManufacturer Data: {")
    for manufacturer_id, value in adv_data.manufacturer_data.items():
        print(f"\t\t{color.yellow(hex(manufacturer_id))}: {color.green(value)}")
    print("\t}")


    print("\tService Data: {")
    if malformed:
        for uuid, value in adv_data.service_data.items():
            print(color.yellow(f"\t\t0x{uuid[4:8]}") + ": ", color.green(value))
    else:
        for uuid, value in adv_data.service_data.items():
            print(color.yellow(f"\t\t0x{uuid[4:8]}") + ": {")

            building_id = int.from_bytes(value[0:2], byteorder='big')
            floor = value[2]
            loc_north = frombuffer(value[3:5], dtype=">f2")[0].astype(float)
            loc_east = frombuffer(value[5:7], dtype=">f2")[0].astype(float)

            print(f"\t\t\tBuilding ID: {building_id}")
            print(f"\t\t\tFloor: {floor}")
            print(f"\t\t\tLocal North: {loc_north}")
            print(f"\t\t\tLocal East: {loc_east}")

            print("\t\t}")
    print("\t}")

    print(f"\tRSSI: {color.yellow(adv_data.rssi)}")
    print(f"\tTx Power: {color.yellow(adv_data.tx_power)}")


if __name__ == '__main__':
    asyncio.run(main())