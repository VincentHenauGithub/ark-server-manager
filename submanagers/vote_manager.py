import threading
import time
import json
from pathlib import Path
from typing import Dict
from uuid import UUID

from arkparse import AsaSave
from arkparse.api.dino_api import DinoApi
from arkparse.enums import ArkMap, ArkStat
from arkparse.object_model.dinos.dino import Dino
from arkparse.ftp.ark_ftp_client import ArkFtpClient
from arkparse.api.rcon_api import RconApi, GameLogEntry
from arkparse.classes.dinos import Dinos
from .__manager import Manager

VOTE_MESSAGES = {
    "Test": "test of the voting system"
}

class VoteManager(Manager):

    def __init__(self, rconapi: RconApi, ftp_config: dict):
        super().__init__(self.__process, "vote manager")
        self.rcon : RconApi = rconapi
        self.log_handle = self.rcon.subscribe()

        self.current_votes = {}
        self.vote_type = None
        self.vote_time_left = 0

        # Track which players have voted, and which tribes have voted
        # self.player_votes: Dict[str, int] -> {playerName: 1 or 0}
        # self.tribe_votes: Dict[str, int] -> {tribeName: 1 or 0}
        self.player_votes = {}
        self.tribe_votes = {}

        self.stop_vote_count = threading.Event()
        self.vote_count_down_thread = threading.Thread(target=self.__vote_count_down_thread)
        self.vote_count_down_thread.start()

        # Re-subscribe in case we want a new handle (unlikely needed but left in place)
        self.log_handle = self.rcon.subscribe()

        # FTP client
        self.ftp = ArkFtpClient.from_config(ftp_config, ArkMap.ABERRATION)

    def stop(self):
        super().stop()
        self.stop_vote_count.set()
        self.vote_count_down_thread.join()

    def is_alive(self):
        return super().is_alive() and self.vote_count_down_thread.is_alive()
    
    def __ue5_to_tribe(self, ue5_id: str):
        """Given a UE5 player ID, return the tribe name (if any)."""
        if not ue5_id:
            return None
        with open("players.json", 'r') as f:
            players = json.load(f)
            if ue5_id in players and "tribe" in players[ue5_id]:
                return players[ue5_id]["tribe"]
        return None
            
    def __get_nr_of_tribes(self):
        """Return how many distinct tribes are recorded in players.json."""
        with open("players.json", 'r') as f:
            players = json.load(f)
            tribes = set()
            for player in players.values():
                if "tribe" in player:
                    tribes.add(player["tribe"])
            return len(tribes)

    def __check_for_vote(self, message: GameLogEntry):
        """Check if this message is a vote command, and register the vote."""
        if message.type == message.EntryType.PLAYER:
            player = message.get_player_chat_name()
            tribe_id = self.__ue5_to_tribe(message.get_player_ue5_id())

            if message.message in ("!VoteYes", "!VoteNo"):
                if self.vote_type is None:
                    self.rcon.send_message(f"@{player}, there is no active vote right now!")
                elif player in self.player_votes:
                    self.rcon.send_message(f"@{player}, you already voted...")
                else:
                    # Record the player's vote
                    if message.message == "!VoteYes":
                        self.player_votes[player] = 1
                        # If the player has a tribe, record that tribe's vote as 'yes'
                        if tribe_id:
                            self.tribe_votes[tribe_id] = 1
                    else:
                        self.player_votes[player] = 0
                        # If the player has a tribe, record that tribe's vote as 'no'
                        if tribe_id:
                            self.tribe_votes[tribe_id] = 0

    def __process(self, interval: int):
        """Periodically fetch new log entries and process them."""
        response = self.rcon.get_new_entries(self.log_handle)

        if response and len(response):
            self._print("New log messages:")
            for entry in response:
                self._print(entry)
                self.__check_for_vote(entry)

                # Demo test vote
                if entry.message == "!StartTestVote":
                    self.start_vote("Test", 60)

                # Example: "[BOT] Is there an alpha reaper?" -> vote type = reaper
                elif entry.type == entry.EntryType.GAME and entry.message.startswith("[BOT] Is there an alpha "):
                    vote_t = entry.message.split("[BOT] Is there an alpha ")[1].split("?")[0]
                    self.start_vote(vote_t, 180)

                # Example: "The highest damage wild dino is X" -> triggers "Dino hunt damage"
                elif entry.type == entry.EntryType.GAME and entry.message.startswith("The highest ") and 'wild' in entry.message:
                    # The third token is typically "damage"/"health"/"oxygen"/etc.
                    vote_stat = entry.message.split(" ")[2]
                    vote_t = "Dino hunt " + vote_stat
                    self.start_vote(vote_t, 180)

                # Admin command: "!AdminAlpha!reaper" -> starts alpha reaper vote
                elif entry.message.startswith("!AdminAlpha!"):
                    vote_t = entry.message.split("!")[-1]
                    self.start_vote(vote_t, 180)

    def __count_votes(self):
        """
        Count votes. Returns a tuple:
         - yes_votes: how many *players* voted yes
         - no_votes: how many *players* voted no
         - yes_tribes: how many distinct tribes have a 'yes' vote
        """
        yes_votes = sum(1 for v in self.player_votes.values() if v == 1)
        no_votes = sum(1 for v in self.player_votes.values() if v == 0)
        # If tribe_votes[tribe] == 1, it means that tribe voted yes.
        # If tribe_votes[tribe] == 0, it means that tribe voted no.
        yes_tribes = sum(1 for v in self.tribe_votes.values() if v == 1)
        return yes_votes, no_votes, yes_tribes

    def __vote_count_down_thread(self):
        """Counts down vote_time_left, sends periodic reminders, and handles the vote result."""
        while not self.stop_vote_count.is_set():
            if self.vote_time_left > 0:
                self.vote_time_left -= 1
                if self.vote_time_left == 0:
                    self.handle_vote_result()
                    # Reset vote state
                    self.vote_type = None
                    self.player_votes = {}
                    self.tribe_votes = {}
                else:
                    # Send periodic reminders
                    if self.vote_time_left % 30 == 0 or (self.vote_time_left % 10 == 0 and self.vote_time_left <= 30):
                        self.rcon.send_message(f"Vote time left: {self.vote_time_left}s")
            time.sleep(1)

    def start_vote(self, vote_type: str, timeout: int, vote_message: str = None):
        """
        Initializes a new vote with the given type and time limit.
        """
        # Reset existing votes and start a new one
        self.vote_type = vote_type
        self.vote_time_left = timeout
        self.player_votes = {}
        self.tribe_votes = {}

        # Announce the vote
        if vote_type in ("reaper", "basilisk", "karkinos"):
            self.rcon.send_message(f"Want to know its location? Vote to reveal it ;) ({timeout}s)")
            self.rcon.send_message("Vote passes if 1 person per tribe votes yes")
        elif vote_type.startswith("Dino hunt"):
            self.rcon.send_message(f"Want its coordinates? Vote to reveal them ({timeout}s)")
            self.rcon.send_message("Vote passes if 2 tribes vote yes")
        elif vote_type in VOTE_MESSAGES:
            self.rcon.send_message(f"Vote started for {VOTE_MESSAGES[vote_type]} ({timeout}s)")
        else:
            self.rcon.send_message(f"Vote started for {vote_type} ({timeout}s)")

        self.rcon.send_message("Type !VoteYes or !VoteNo to vote")

    def __handle_alpha_vote_success(self):
        """When alpha vote passes, reveal the alpha's location on Aberration."""
        bp = None 
        if self.vote_type == "reaper":
            bp = Dinos.alpha_reaper_king
        elif self.vote_type == "basilisk":
            bp = Dinos.alpha_basilisk
        elif self.vote_type == "karkinos":
            bp = Dinos.alpha_karkinos
        else:
            return

        self.ftp.connect()
        save_path = self.ftp.download_save_file(Path.cwd() / "artifacts" / "vote_mngr")
        self.ftp.close()

        save = AsaSave(save_path)
        dino_api = DinoApi(save)
        dinos: Dict[UUID, Dino] = dino_api.get_all_wild_by_class([bp])

        if len(dinos.keys()):
            dino = list(dinos.values())[0]
            coords = dino.location.as_map_coords(ArkMap.ABERRATION)
            self.rcon.send_message(
                f"Vote passed! Alpha {self.vote_type} found at {coords}"
            )
        else:
            self.rcon.send_message(f"Vote passed, but no alpha {self.vote_type} was found!")

    def __handle_dino_hunt_vote_success(self):
        """When a 'Dino hunt' vote passes, show the location of the best wild dino for a given stat."""
        # e.g., self.vote_type = "Dino hunt damage" -> last token is 'damage'
        stat = self.vote_type.split(" ")[-1]

        if stat == "damage":
            e_stat = ArkStat.MELEE_DAMAGE
        elif stat == "health":
            e_stat = ArkStat.HEALTH
        elif stat == "oxygen":
            e_stat = ArkStat.OXYGEN
        else:
            raise ValueError(f"Invalid stat {stat}")

        self.ftp.connect()
        save_path = self.ftp.download_save_file()
        self.ftp.close()

        dino_api = DinoApi(AsaSave(contents=save_path))
        best_dinos = dino_api.get_best_dino_for_stat(stat=e_stat, only_untamed=True)

        if best_dinos:
            dino = best_dinos[0]
            coords = dino.location.as_map_coords(ArkMap.ABERRATION)
            self.rcon.send_message(f"Vote passed! Check {coords}! Happy hunting!")
        else:
            self.rcon.send_message("Vote passed! But no dino found with that stat.")

    def handle_vote_result(self):
        """Called when the vote time runs out. Evaluate the results and announce."""
        yes_votes, no_votes, yes_tribes = self.__count_votes()
        total_tribes = self.__get_nr_of_tribes()  # For logic that needs all tribes

        if self.vote_type == "Test":
            self.rcon.send_message(
                f"Test vote ended. Yes: {yes_votes}, No: {no_votes}, "
                f"{yes_tribes} {'tribe' if yes_tribes == 1 else 'tribes'} voted yes"
            )

        elif self.vote_type in ("reaper", "basilisk", "karkinos"):
            # Passes if every tribe that exists has voted yes 
            # (or if you only want the ones that actually voted, you can adapt logic).
            if yes_tribes == total_tribes and total_tribes > 0:
                self.__handle_alpha_vote_success()
            else:
                self.rcon.send_message("Vote failed! Not all tribes voted yes")

        elif self.vote_type and self.vote_type.startswith("Dino hunt"):
            # Passes if at least 2 distinct tribes said yes
            if yes_tribes >= 2:
                self.__handle_dino_hunt_vote_success()
            else:
                self.rcon.send_message("Vote failed! Not enough tribes voted yes")

        else:
            # Fallback for any other vote type
            self.rcon.send_message(
                f"Vote ended for '{self.vote_type}'. Yes: {yes_votes}, No: {no_votes}, "
                f"{yes_tribes} {'tribe' if yes_tribes == 1 else 'tribes'} voted yes"
            )
