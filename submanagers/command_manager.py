import threading
import time
import json

from arkparse.enums import ArkMap
from arkparse.ftp.ark_ftp_client import ArkFtpClient
from arkparse.api.rcon_api import RconApi, GameLogEntry
from .__manager import Manager
from .save_tracker import SaveTracker
from arkparse import Classes

class CommandManager(Manager):

    def __init__(self, rconapi: RconApi, save_tracker: SaveTracker):
        super().__init__(self.__process, "command manager", interval=5)
        self.rcon : RconApi = rconapi
        self.log_handle = self.rcon.subscribe()
        self.save_tracker = save_tracker

    @property
    def nr_of_players(self):
        """Return the number of players currently online."""
        return len(self.rcon.get_active_players())
    
    def retrieve_nr_of_dinos(self, bp: str):
        """Return the number of dinos of a specific blueprint currently online."""
        d_api = self.save_tracker.dino_api
        entities = d_api.get_all_by_class([bp])
        return len(entities)

    def __process(self, interval: int):
        """Periodically fetch new log entries and process them."""
        response = self.rcon.get_new_entries(self.log_handle)

        if response and len(response):
            self._print("New log messages:")
            for entry in response:
                self._print(entry)
                message = entry.message.split(":")[-1].strip()  # Get the actual message part

                # Demo test vote
                if message == "?Test":
                    self.rcon.send_message(f"Test received from {entry.get_player_chat_name()}")
                elif message == "?Giga":
                    if self.nr_of_players < 2:
                        self.rcon.send_message("Not enough players online for that command!")
                    else:
                        nr_of_gigas = self.retrieve_nr_of_dinos(Classes.dinos.giganotosaurus)
                        if nr_of_gigas > 0:
                            self.rcon.send_message(f"There is at least one giga")
                        else:
                            self.rcon.send_message("There are currently no gigas")
                elif message == "?Rhynio":
                    if self.nr_of_players < 2:
                        self.rcon.send_message("Not enough players online for that command!")
                    else:
                        nr_of_rhynios = self.retrieve_nr_of_dinos(Classes.dinos.flyers.rhyniognatha)
                        if nr_of_rhynios > 0:
                            self.rcon.send_message(f"There is at least one rhyniognatha")
                        else:
                            self.rcon.send_message("There are currently no rhyniognathas")
                elif entry.message.startswith("?"):
                    self.rcon.send_message(f"Unknown command: {entry.message}")
