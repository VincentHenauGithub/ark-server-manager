from arkparse.api.rcon_api import RconApi
from .__manager import Manager

class ChatLogger(Manager):

    def __init__(self, rconapi: RconApi):
        super().__init__(self.__process, "chat logger", 0.5)
        self.rcon : RconApi = rconapi
        self.log_handle = self.rcon.subscribe()

    def __process(self, interval: int):
        """Periodically fetch new log entries and process them."""
        response = self.rcon.get_new_entries(self.log_handle)

        if response and len(response):
            self._print("New log messages:")
            for entry in response:
                self._print(entry)