import threading
import time

from arkparse.api.rcon_api import RconApi, GameLogEntry
from .__manager import Manager

VOTE_MESSAGES = {
    "Test": "test of the voting system"
}

class VoteManager(Manager):

    def __init__(self, rconapi: RconApi):
        super().__init__(self.__process, "vote manager")
        self.rcon : RconApi = rconapi
        self.current_votes = {}
        self.vote_type = None
        self.vote_time_left = 0
        self.stop_vote_count = threading.Event()
        self.vote_count_down_thread = threading.Thread(target=self.__vote_count_down_thread)
        self.vote_count_down_thread.start()

    def stop(self):
        super().stop()
        self.stop_vote_count.set()
        self.vote_count_down_thread.join()

    def is_alive(self):
        return super().is_alive() and self.vote_count_down_thread.is_alive()

    def __check_for_vote(self, message: GameLogEntry):
        if message.type == message.EntryType.PLAYER:
            player = message.get_player_chat_name()

            if message.message == "!VoteYes" or message.message == "!VoteNo":
                if self.vote_type is None:
                    self.rcon.send_message(f"@{player}, what are you trying to vote for?")
                elif player in self.current_votes:
                    self.rcon.send_message(f"@{player}, you already voted...")
                else:
                    self.current_votes[player] = 1 if message.message == "!VoteYes" else 0
    
    def __process(self, interval: int):
        response = self.rcon.update_game_log()

        if response and len(response):
            print("\nNew log messages:")
            for entry in response:
                print(entry)
                self.__check_for_vote(entry)

                if entry.message == "!StartTestVote":
                    self.start_vote("Test", 30)

            # print("\nFull log:")
            # for entry in self.rcon.game_log:
            #     print(entry)

    def __count_votes(self):
        yes_votes = 0
        no_votes = 0

        for vote in self.current_votes.values():
            if vote:
                yes_votes += 1
            else:
                no_votes += 1

        return yes_votes, no_votes

    def __vote_count_down_thread(self):
        while not self.stop_vote_count.is_set():
            if self.vote_time_left > 0:
                self.vote_time_left -= 1
                if self.vote_time_left == 0:
                    yes_votes, no_votes = self.__count_votes()
                    self.rcon.send_message(f"Vote ended. Results: Yes: {yes_votes}, No: {no_votes}")
                    self.vote_type = None
                    self.current_votes = {}
                else:
                    if self.vote_time_left % 10 == 0:
                        self.rcon.send_message(f"Vote time left: {self.vote_time_left}")
            time.sleep(1)

    def start_vote(self, vote_type: str, timeout: int):
        self.vote_type = vote_type
        self.vote_time_left = timeout
        self.current_votes = {}
        self.rcon.send_message(f"Vote started ({timeout}s): \"{vote_type}\"")
        self.rcon.send_message(f"Type !VoteYes or !VoteNo to vote")
