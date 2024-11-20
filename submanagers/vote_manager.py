from arkparse.api.rcon_api import RconApi
from __manager import Manager

class VoteManager(Manager):

    def __init__(self, rconapi: RconApi):
        super().__init__(self.__process, "vote manager")
        self.rcon : RconApi = rconapi
    
    def __process(self, interval: int):
        response = self.rcon.update_game_log()

        if response and len(response):
            print("New log messages:")
            for entry in response:
                print(entry)

            print("\nFull log:")
            for entry in self.rcon.game_log:
                print(entry)