from quart import Quart
import json
import position
import asyncio

class API:
    def __init__(self, pos):
        if type(pos) is not position.Position:
            return

        self.position = pos
        self.app = Quart(__name__)

        # Define endpoint handlers within the initializer
        # as we can't do so at compile time unless the
        # Flask instance is made global.
        @self.app.route("/")
        async def index():
            return "hi"

        @self.app.route("/json", methods=["GET"])
        async def get_position():
            return self.position.dict()

        print("Webserver Initialized. Visit https://localhost:5000/")

    async def run(self):
        await self.app.run_task()