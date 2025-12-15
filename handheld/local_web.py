from quart import Quart
import json
import position
import asyncio
from sensors import SensorCache

class API:
    def __init__(self, pos, beacons):
        if type(pos) is not position.Position:
            return

        if type(beacons) is not SensorCache:
            return

        self.position = pos
        self.beacons = beacons

        # Use webroot for static files instead of /static/
        self.app = Quart(__name__, static_url_path='')

        # Define endpoint handlers within the initializer
        # as we can't do so at compile time unless the
        # Flask instance is made global.
        @self.app.route("/")
        async def index():
            # Serve ./static/index.html as webroot
            return await self.app.send_static_file("index.html")

        @self.app.route("/json", methods=["GET"])
        async def get_position():
            beacons.clear_old_sensors()
            calc_pos = beacons.trilaterate()
            if calc_pos is None:
                return json.dumps({"x": 0, "y": 0, "xm": 0, "ym": 0})
            x = calc_pos.loc_north
            y = calc_pos.loc_east
            if x is None: x = 0
            if y is None: y = 0
            return json.dumps({"x": x * 98.4252, "y": y * 98.4252, "xm": x, "ym": y})

        @self.app.route("/beacons", methods=["GET"])
        async def get_beacons():
            return self.beacons.json()

        print("Webserver Initialized. Visit http://localhost:5000/")

    async def run(self):
        await self.app.run_task()