import numbers
from collections import deque
from position import Position
import time
import json
import numpy as np
from kalman import Kalman1D

TX_POWER = -66
PATH_LOSS = 1.61085143652

def convert_rssi_to_distance(rssi, tx_power=TX_POWER, path_loss=PATH_LOSS):
    return 10 ** ((tx_power - rssi) / (10 * path_loss))

# With the current floorplan, 1ft=30px
# First convert to feet, then to pixels
def meters_to_px(meters):
    return meters * 98.4252

# Divide by 30 and then 3.28084
def px_to_meters(px):
    return px / 98.4252


class SensorCache:
    def __init__(self, expiry_time, on_trilaterate):
        self.cache = {}
        self.on_trilaterate = on_trilaterate

        if not isinstance(expiry_time, numbers.Number):
            expiry_time = 0

        # Configure the time in seconds to wait before removing a beacon from the cache.
        # This time is used to gauge whether a beacon is no longer in range or has fallen
        # offline. Currently, every beacon should transmit at least once per second.
        # However, we may sometimes lose incoming advertisements. Adjust as needed.
        # If set to 0, do not remove old sensors from the cache. This will make best-fit
        # selection more costly.
        self.expiry_time = expiry_time
        # Minimum time (seconds) between appending identical samples for the same sensor
        # This helps deduplicate rapid duplicate callbacks (advertisement + scan response)
        self._min_append_interval = 0.02


    def record_sensor(self, pos, rssi):
        if type(pos) is not Position:
            return

        key = pos.tup()
        entry = self.cache.get(key)
        if entry is None:
            entry = {
                # Store a history of RSSI values to smooth out fluctuations
                'history': deque(maxlen=10),
                'time': 0,
                'avg_rssi': 0,
                'distance': 0,
                'kalman': Kalman1D()
            }

        now = time.time()

        # If the most recent recorded RSSI is identical, and we recorded it
        # very recently, skip appending to avoid duplicates coming from
        # advertisement + scan-response or duplicated callbacks.
        last_val = entry['history'][-1] if entry['history'] else None
        if last_val is not None and last_val == rssi:
            if (now - entry['time']) < self._min_append_interval:
                # skip duplicate
                entry['time'] = now
                self.cache[key] = entry
                return

        entry['history'].append(rssi)
        entry['time'] = now

        filtered_rssi = entry['kalman'].update(rssi)
        entry['avg_rssi'] = filtered_rssi

        min_d = 0  # meters
        max_d = 10.0
#        entry['distance'] = convert_rssi_to_distance(filtered_rssi)
        dist = convert_rssi_to_distance(filtered_rssi)
        entry['distance'] = max(min_d, min(max_d, dist))

        # Update the cache
        self.cache[key] = entry


    def clear_old_sensors(self):
        # Avoid concurrent modification
        to_remove = []
        for pos, val in self.cache.items():
            # If we haven't heard from a beacon in the expiry time
            if self.expiry_time != 0 and val['time'] < time.time() - self.expiry_time:
                to_remove.append(pos)

        for pos in to_remove:
            # Remove the dictionary entry
            del self.cache[pos]

    def get_best_sensors(self):
        sensors = [(val['distance'], pos) for pos, val in self.cache.items()]
        # Sort by distance (lowest first)
        sensors.sort(key=lambda x: x[0])

        # Get up to three positions, padding with None if fewer than three
        best = [pos for _, pos in sensors[:3]]
        while len(best) < 3:
            best.append(None)

        return best

    def trilaterate(self):
        a, b, c = self.get_best_sensors()
        # Retrieve using self.cache[a].rssi

        p = list()

        # Implement algorithm
        for pos in self.get_best_sensors():
            if not pos:
                continue
            _, _, loc_north, loc_east = pos
            val = self.cache[pos]
            #p.append([loc_north, loc_east, val['distance']])
            p.append([px_to_meters(loc_north), px_to_meters(loc_east), val['distance']])

        # Make sure we have minimum number of beacons
        if len(p) < 3:
            return None

        A = 2 * (p[1][0] - p[0][0]), 2 * (p[1][1] - p[0][1])
        B = 2 * (p[2][0] - p[0][0]), 2 * (p[2][1] - p[0][1])
        C = p[0][2]**2 - p[1][2]**2 + p[1][0]**2 - p[0][0]**2 + p[1][1]**2 - p[0][1]**2
        D = p[0][2]**2 - p[2][2]**2 + p[2][0]**2 - p[0][0]**2 + p[2][1]**2 - p[0][1]**2

        M = np.array([[A[0], A[1]],
                      [B[0], B[1]]])
        Y = np.array([C, D])

        try:
            x, y = np.linalg.solve(M, Y)
            building_id, floor, _, _ = a # Extract from best pos tuple
            calc_pos = Position(x, y, building_id, floor)
            self.on_trilaterate(calc_pos)
            return calc_pos
        except np.linalg.LinAlgError:
            print("Error: Beacons may be collinear or distances invalid")
            return None


    def json(self):
        assemble = []
        for pos, val in self.cache.items():
            building_id, floor, loc_north, loc_east = pos
            assemble.append({
                "loc_north": loc_north,
                "loc_east": loc_east,
                "building_id": building_id,
                "floor": floor,
                "avg_rssi": val['avg_rssi'],
                "history": list(val['history']),
                "distance": val['distance']
            })

        return json.dumps(assemble)