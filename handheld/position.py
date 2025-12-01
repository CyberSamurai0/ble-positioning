class Position:
    def __init__(self, loc_north=0, loc_east=0, building_id=0, floor=0):
        self.loc_north = loc_north
        self.loc_east = loc_east
        self.building_id = building_id
        self.floor = floor

    # Return the Position class as a dictionary
    def dict(self):
        return {
            "loc_north": self.loc_north,
            "loc_east": self.loc_east,
            "building_id": self.building_id,
            "floor": self.floor,
        }

    # Return the Position class as a tuple
    def tup(self):
        return self.building_id, self.floor, self.loc_north, self.loc_east