from position import Position
import time

class Sensors:
    def __init__(self):
        self.cache = {}

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
            # If we haven't heard from a beacon in 5s
            if val.time < time.time() - 5:
                to_remove.append(pos)

        for pos in to_remove:
            # Remove the dictionary entry
            del self.cache[pos]

    def get_best_sensors(self):
        # Prioritize recency, then proximity
        # Return three cache objects (position and RSSI)
        return None, None, None

    def trilaterate(self):
        a, b, c = self.get_best_sensors()
        # Retrieve using self.cache[a].rssi

        # Implement algorithm
        pass