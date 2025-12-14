import asyncio
import math
import numpy as np
from bleak import BleakScanner

# ---------------- Kalman Filter ---------------- #
class Kalman1D:
    def __init__(self, Q=0.01, R=4.0):
        self.Q = Q
        self.R = R
        self.x = None
        self.P = 1.0

    def update(self, measurement):
        if self.x is None:
            self.x = measurement
            return self.x

        self.P += self.Q
        K = self.P / (self.P + self.R)
        self.x = self.x + K * (measurement - self.x)
        self.P = (1 - K) * self.P
        return self.x


# ---------------- BLE RSSI Collection ---------------- #
async def collect_rssi_samples(mac, num_samples=40, scan_time=1.0):
    samples = []

    def detection_callback(device, advertisement_data):
        if device.address.lower() == mac.lower():
            if advertisement_data.rssi is not None:
                samples.append(advertisement_data.rssi)
                print(f"RSSI {len(samples)}: {advertisement_data.rssi} dBm")

    scanner = BleakScanner(detection_callback)
    await scanner.start()

    # Keep scanning until we get enough samples
    while len(samples) < num_samples:
        await asyncio.sleep(scan_time)  # scan in short intervals

    await scanner.stop()

    # Optionally drop first N readings
    if len(samples) > 15:
        samples = samples[15:]

    return samples


def smooth_rssi(samples):
    kf = Kalman1D()
    return [kf.update(r) for r in samples]


# ---------------- TX Power @ 1m ---------------- #
async def calibrate_tx_power(mac):
    confirm = input("\nAre you exactly 1 meter away? (y/n): ").lower()
    if confirm != 'y':
        print("❌ TX power calibration must be done at 1 meter.")
        exit()

    samples = await collect_rssi_samples(mac)
    smoothed = smooth_rssi(samples)
    tx_power = np.mean(smoothed)

    print("\n✅ TX Power Calibration Complete")
    print("TX Power (RSSI @ 1m):", round(tx_power, 2), "dBm")

    return tx_power


# ---------------- Path Loss Exponent @ 2–5m ---------------- #
async def calibrate_path_loss(mac, tx_power):
    distances = [2, 3, 4, 5]
    n_values = {}

    print("\n📏 Path Loss Exponent Calibration\n")

    for d in distances:
        input(f"➡️ Move to {d} meters and press Enter...")

        samples = await collect_rssi_samples(mac)
        smoothed = smooth_rssi(samples)
        avg_rssi = np.mean(smoothed)

        n = (tx_power - avg_rssi) / (10 * math.log10(d))
        n_values[d] = n

        print(f"Distance: {d} m")
        print(f"Avg RSSI: {round(avg_rssi, 2)} dBm")
        print(f"Estimated n: {round(n, 3)}\n")

    n_avg = np.mean(list(n_values.values()))
    return n_avg, n_values


# ---------------- Main ---------------- #
async def main():
    print("\n📡 BLE RSSI Calibration Tool\n")

    mac = input("Enter BLE MAC address (AA:BB:CC:DD:EE:FF): ").strip()

    tx_power = await calibrate_tx_power(mac)
    n_avg, n_map = await calibrate_path_loss(mac, tx_power)

    print("\n🎯 Final Calibration Results")
    print("---------------------------")
    print("TX Power (RSSI @ 1m):", round(tx_power, 2), "dBm")

    for d, n in n_map.items():
        print(f"n @ {d} m:", round(n, 3))

    print("Average Path Loss Exponent n:", round(n_avg, 3))


if __name__ == "__main__":
    asyncio.run(main())
