# BLE Beacons Subsystem
This directory houses the firmware used with XIAO nRF52840 units to support BLE location beaconing.

## Compilation
It is encouraged to use either the Arduino IDE or the [nRF Connect for VS Code](https://marketplace.visualstudio.com/items?itemName=nordic-semiconductor.nrf-connect-extension-pack) extensions to build from source.

## Flashing
Rather than overwrite the included bootloader, this project utilizes the Arduino UF2 bootloader included on the XIAO nRF52840 units. However, nRF Connect outputs `.hex` files. Microsoft's [uf2conv.py](https://github.com/microsoft/uf2/blob/master/utils/uf2conv.py) facilitates easy conversion from the `.hex` format to `.uf2` files.

Two helper scripts have been created to enhance the compilation/flashing workflow.
- Windows users can drag and drop the `.hex` file onto [hex-to-uf2.bat](.\hex-to-uf2.bat).
- Linux users can provide the `.hex` file as an argument of [./hex-to-uf2.sh](.\hex-to-uf2.sh).

## Advertisement Payload Format

| Field                |  Bytes  | Value                                                                                                                      |
|:---------------------|:-------:|----------------------------------------------------------------------------------------------------------------------------|
| Data Length          |    1    | 7 bytes of Manufacturer Data                                                                                               |
| Data Type            |    1    | `0xFF` - Manufacturer Data                                                                                                 |
| Manufacturer ID      |    2    | `0xFFFF` - Test Identifier                                                                                                 |
| Version              |    4    | `'v'` followed by the major, minor, and patch version number                                                               |
| Data Length          |    1    | 7 bytes of Service Data                                                                                                    |
| Data Type            |    1    | `0x16` - Service Data                                                                                                      |
| Service ID           |    2    | `0x1821` - Shorthand ID for Indoor Positioning Service                                                                     |
| Building ID          |    2    | Configured per device                                                                                                      |
| Floor ID             |    1    | Configured per device                                                                                                      |
| Local North Position |    2    | [Half Precision Floating Point](https://en.wikipedia.org/wiki/Half-precision_floating-point_format), configured per device |
| Local East Position  |    2    | [Half Precision Floating Point](https://en.wikipedia.org/wiki/Half-precision_floating-point_format), configured per device |

### Local Position Coordinates
Position values are stored as [16-bit floating point numbers](https://en.wikipedia.org/wiki/Half-precision_floating-point_format) representing the number of feet from the building's origin position. Float16 values can represent the range ±65,504 with a 10-bit fractional component.