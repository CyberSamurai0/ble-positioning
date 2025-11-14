# BLE Beacons Subsystem
This directory houses the firmware used with XIAO nRF52840 units to support BLE location beaconing.

## Compilation
It is encouraged to use either the Arduino IDE or the [nRF Connect for VS Code](https://marketplace.visualstudio.com/items?itemName=nordic-semiconductor.nrf-connect-extension-pack) extensions to build from source.

## Flashing
Rather than overwrite the included bootloader, this project utilizes the Arduino UF2 bootloader included on the XIAO nRF52840 units. However, nRF Connect outputs `.hex` files. Microsoft's [uf2conv.py](https://github.com/microsoft/uf2/blob/master/utils/uf2conv.py) facilitates easy conversion from the `.hex` format to `.uf2` files.

Two helper scripts have been created to enhance the compilation/flashing workflow.
- Windows users can drag and drop the `.hex` file onto [hex-to-uf2.bat](.\hex-to-uf2.bat).
- Linux users can provide the `.hex` file as an argument of [./hex-to-uf2.sh](.\hex-to-uf2.sh).