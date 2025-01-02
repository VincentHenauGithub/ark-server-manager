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
from arkparse.ftp.ark_ftp_client import ArkFtpClient, ArkMap
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
        self.stop_vote_count = threading.Event()
        self.vote_count_down_thread = threading.Thread(target=self.__vote_count_down_thread)
        self.vote_count_down_thread.start()
        self.log_handle = self.rcon.subscribe()
        self.ftp = ArkFtpClient.from_config(ftp_config, ArkMap.ABERRATION)

    def stop(self):
        super().stop()
        self.stop_vote_count.set()
        self.vote_count_down_thread.join()

    def is_alive(self):
        return super().is_alive() and self.vote_count_down_thread.is_alive()
    
    def __ue5_to_tribe(self, ue5_id: str):
        with open("players.json", 'r') as f:
            players = json.load(f)
            if ue5_id in players:
                return players[ue5_id]["tribe"]
            
    def __get_nr_of_tribes(self):
        with open("players.json", 'r') as f:
            players = json.load(f)
            tribes = set()
            for player in players.values():
                if "tribe" in player:
                    tribes.add(player["tribe"])
            return len(tribes)

    def __check_for_vote(self, message: GameLogEntry):
        if message.type == message.EntryType.PLAYER:
            player = message.get_player_chat_name()

            if message.message == "!VoteYes" or message.message == "!VoteNo":
                if self.vote_type is None:
                    self.rcon.send_message(f"@{player}, what are you trying to vote for?")
                elif player in self.player_votes:
                    self.rcon.send_message(f"@{player}, you already voted...")
                else:
                    self.player_votes[player] = 1 if message.message == "!VoteYes" else 0
                    if message.message == "!VoteYes":
                        self.tribe_votes[self.__ue5_to_tribe(message.get_player_ue5_id())] = 1
    
    def __process(self, interval: int):
        response = self.rcon.get_new_entries(self.log_handle)

        if response and len(response):
            self._print("New log messages:")
            for entry in response:
                self._print(entry)
                self.__check_for_vote(entry)

                if entry.message == "!StartTestVote":
                    self.start_vote("Test", 60)

                elif entry.type == entry.EntryType.GAME and entry.message.startswith("[BOT] Is there an alpha "):
                    vote_t = entry.message.split("[BOT] Is there an alpha ")[1].split("?")[0]
                    self.start_vote(vote_t, 180)

                elif entry.type == entry.EntryType.GAME and entry.message.startswith("The highest ") and 'wild' in entry.message:
                    vote_t = "Dino hunt " + entry.message.split(" ")[2]
                    self.start_vote(vote_t, 180)

                elif entry.message.startswith("!AdminAlpha!"):
                    vote_t = entry.message.split("!")[-1]
                    self.start_vote(vote_t, 180)

            # self._print("\nFull log:")
            # for entry in self.rcon.game_log:
            #     self._print(entry)

    def __count_votes(self):
        yes_votes = 0
        no_votes = 0
        t_votes = 0

        for vote in self.player_votes.values():
            if vote:
                yes_votes += 1
            else:
                no_votes += 1

        for vote in self.tribe_votes.values():
            if vote:
                t_votes += 1
            else:
                t_votes += 1

        return yes_votes, no_votes, t_votes

    def __vote_count_down_thread(self):
        while not self.stop_vote_count.is_set():
            if self.vote_time_left > 0:
                self.vote_time_left -= 1
                if self.vote_time_left == 0:
                    self.handle_vote_result()
                    self.vote_type = None
                    self.player_votes = {}
                    self.tribe_votes = {}
                else:
                    if self.vote_time_left % 30 == 0 or (self.vote_time_left % 10 == 0 and self.vote_time_left <= 30):
                        self.rcon.send_message(f"Vote time left: {self.vote_time_left}s")
            time.sleep(1)

    def start_vote(self, vote_type: str, timeout: int, vote_message: str = None):
        self.vote_type = vote_type
        self.vote_time_left = timeout
        self.player_votes = {}
        self.tribe_votes = {}
        if vote_type == "reaper" or vote_type == "basilisk" or vote_type == "karkinos":
            self.rcon.send_message(f"Want to know its location? Vote to reveal it ;) ({timeout}s)")
            self.rcon.send_message("Vote passes if 1 person per tribe votes yes")
        elif vote_type.startswith("Dino hunt"):
            self.rcon.send_message(f"Want it's coordinates? Vote to reveal them ({timeout}s)")
            self.rcon.send_message("Vote passes if 2 tribes vote yes")
        elif vote_type in VOTE_MESSAGES:
            self.rcon.send_message(f"Vote started for {VOTE_MESSAGES[vote_type]} ({timeout}s)")
        else:
            self.rcon.send_message(f"Vote started for {vote_type} ({timeout}s)")
        self.rcon.send_message("Type !VoteYes or !VoteNo to vote")

    def __handle_alpha_vote_success(self):
        bp = None 
        if self.vote_type == "reaper":
            bp = Dinos.alpha_reaper_king
        elif self.vote_type == "basilisk":
            bp = Dinos.alpha_basilisk
        elif self.vote_type == "karkinos":
            bp = Dinos.alpha_karkinos

        self.ftp.connect()
        save_path = self.ftp.download_save_file(Path.cwd() / "artifacts" / "vote_mngr")
        self.ftp.close()
        save = AsaSave(save_path)
        dino_api = DinoApi(save)
        dinos: Dict[UUID, Dino] = dino_api.get_all_wild_by_class([bp])

        if len(dinos.keys()):
            dino = list(dinos.values())[0]
            self.rcon.send_message(f"Vote passed! Alpha {self.vote_type} found at {dino.location.as_map_coords(ArkMap.ABERRATION)}")

    def __handle_dino_hunt_vote_success(self):
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
            dino: Dino = DinoApi(AsaSave(contents=self.ftp.download_save_file())).get_best_dino_for_stat(stat=e_stat, only_untamed=True)[0]
            self.ftp.close()

            self.rcon.send_message(f"Vote passed! Go check {dino.location.as_map_coords(ArkMap.ABERRATION)}! Happy hunting!")
            

    def handle_vote_result(self):
        yes_votes, no_votes, tribes = self.__count_votes()
        
        if self.vote_type == "Test":
            self.rcon.send_message(f"Test vote ended. Yes: {yes_votes}, No: {no_votes}, {tribes} tribe{'s' if tribes != 1 else ''} voted yes")
        elif self.vote_type == "reaper" or self.vote_type == "basilisk" or self.vote_type == "karkinos":
            if tribes == 3: #self.__get_nr_of_tribes():
                self.__handle_alpha_vote_success()
            else:
                self.rcon.send_message("Vote failed! Not all tribes voted yes")
        elif self.vote_type.startswith("Dino hunt"):
            if tribes >= 2:
                self.__handle_dino_hunt_vote_success()
            else:
                self.rcon.send_message("Vote failed! Not enough tribes voted yes")

        else:
            self.rcon.send_message(f"Vote ended for type {self.vote_type}. Yes: {yes_votes}, No: {no_votes}, {tribes} tribe{'s' if tribes != 1 else ''} voted yes")
