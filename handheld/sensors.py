import numbers
from collections import deque
from position import Position
import time
import json

class SensorCache:
    def __init__(self, expiry_time):
        self.cache = {}

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
        print("record_sensor invoked for", pos.loc_north, pos.loc_east, "with", rssi)
        if type(pos) is not Position:
            return

        key = pos.tup()
        entry = self.cache.get(key)
        if entry is None:
            entry = {
                # Store a history of RSSI values to smooth out fluctuations
                'history': deque(maxlen=5),
                'time': 0,
                'avg_rssi': 0,
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
                print("Skipping Duplicate")
                return

        entry['history'].append(rssi)
        entry['time'] = now

        # Compute average and variance
        vals = list(entry['history'])
        entry['avg_rssi'] = sum(vals) / len(vals)

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
        # Prioritize recency, then proximity
        # Return three cache objects (position and RSSI)

        # TODO implement
        return None, None, None


    def trilaterate(self):
        a, b, c = self.get_best_sensors()
        # Retrieve using self.cache[a].rssi

        # Implement algorithm
        pass

    def json(self):
        assemble = []
        for pos, val in self.cache.items():
            building_id, floor, loc_north, loc_east = pos
            assemble.append({
                "loc_north": loc_north,
                "loc_east": loc_east,
                "building_id": building_id,
                "floor": floor,
                "rssi": val['avg_rssi'],
                "history": list(val['history'])
            })

        return json.dumps(assemble)