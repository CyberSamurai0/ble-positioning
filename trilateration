import math
import numpy as np


#  Beacon positions
#  modify this later
beacons = {
    "A": {"pos": (2, 2)},
    "B": {"pos": (5, 3)},
    "C": {"pos": (4, 6)}
}


# TxPower and path-loss exponent

TxPower = -30  # RSSI at 1 meter (in dBm)
n = 2.0        # have to calcluate this (should be be between 2 to 4)


# RSSI to Distance function

def rssi_to_distance(rssi, tx_power=TxPower, path_loss=n):
    distance = 10 ** ((tx_power - rssi) / (10 * path_loss))
    return distance


# Trilateration function
def trilaterate(beacon_positions, distances):

    (x1, y1), (x2, y2), (x3, y3) = beacon_positions
    d1, d2, d3 = distances

    # Transform to linear equations
    A = 2*(x2 - x1), 2*(y2 - y1)
    B = 2*(x3 - x1), 2*(y3 - y1)
    C = d1**2 - d2**2 + x2**2 - x1**2 + y2**2 - y1**2
    D = d1**2 - d3**2 + x3**2 - x1**2 + y3**2 - y1**2

    # Solve linear system
    M = np.array([[A[0], A[1]],
                  [B[0], B[1]]])
    Y = np.array([C, D])

    try:
        x, y = np.linalg.solve(M, Y)
        return x, y
    except np.linalg.LinAlgError:
        print("Error: Beacons may be collinear or distances invalid")
        return None, None


# MAIN: Example usage
def main():
    # This needs to be modifed
    rssi_readings = {
        "A": -60,
        "B": -35,
        "C": -70
    }

    # Convert RSSI to distances
    distances = []
    beacon_positions = []
    for key in ["A", "B", "C"]:
        rssi = rssi_readings[key]
        d = rssi_to_distance(rssi)
        distances.append(d)
        beacon_positions.append(beacons[key]["pos"])

    # Calculate position
    x, y = trilaterate(beacon_positions, distances)
    print(f"Estimated Position: x = {x:.2f}, y = {y:.2f}")

if __name__ == "__main__":
    main()

