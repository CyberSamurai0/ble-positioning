# Import Built-In Libraries
import machine
import bluetooth

def main():
    # Initialize Bluetooth
    bt = bluetooth.BLE()
    bt.config(gap_name="ESP32")
    
    # Create advertisement payload
    # Flag for General Discoverable Mode and BR/EDR Not Supported
    flags = bytes([0x02, 0x01, 0x06])
    # Complete Local Name
    name = bytes([len("ESP32") + 1, 0x09]) + "ESP32".encode()
    
    # Combine all parts of the advertisement payload
    payload = flags + name
    
    # Set advertisement data
    bt.irq(bt_irq)
    bt.active(True)
    bt.gap_advertise(100000, adv_data=payload)
    
    while True:
        pass
        #machine.idle()


# Bluetooth Event Interrupt Callback
def bt_irq(event, data):
    print(event)
    print(data)


if __name__ == "__main__":
    main()
