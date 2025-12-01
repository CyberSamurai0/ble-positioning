import numbers

from position import Position
import time

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


    def record_sensor(self, pos, rssi):
        if type(pos) is not Position:
            return

        self.cache[pos.tup()] = {
            'rssi': rssi,
            'time': time.time(),
        }


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

        #
        return None, None, None


    def trilaterate(self):
        a, b, c = self.get_best_sensors()
        # Retrieve using self.cache[a].rssi

        # Implement algorithm
        pass