from arkparse.api.rcon_api import RconApi, ActivePlayer
from .__manager import Manager

from .time_handler import TimeHandler, PreviousDate

class PlayerActivityManager(Manager):
    def __init__(self, rconapi: RconApi):
        super().__init__(self.__process, "player activity manager")
        self.rcon : RconApi = rconapi
        self.time_handler: TimeHandler = TimeHandler()
        self.last_active_ts: PreviousDate = None
        self.prev_players = self.rcon.get_active_players()
        self.last_print: PreviousDate = None

    def __process(self, interval: int):
        should_print = (self.last_print is None or self.last_print.is_new_minute()) and self.time_handler.is_quarter_hour()

        if should_print:
            self.last_print = PreviousDate()

        self.expose_players(should_print)
        current_players = self.rcon.get_active_players()
        self.notify_login_logout(current_players, self.prev_players)
        self.increase_playtimes(current_players, self.prev_players, interval)
        self.grind_notifier(current_players)
        self.prev_players = current_players

    def expose_players(self, p):
        players = self.rcon.get_active_players(p)
        last : PreviousDate = self.last_active_ts
        if players is None:
            return None
        
        if not self.time_handler.is_quarter_hour():
            return None

        if last is not None and not last.is_new_minute():
            return None
        
        message = f"Active players ({self.time_handler.get_hr_min_string()}): "

        for p in players:
            p : ActivePlayer = p
            message += p.get_name() + ", "

        self.rcon.send_message(message.strip(" ").strip(","))
        print(message)
        self.last_active_ts = PreviousDate()

        return players

    def notify_login_logout(self, curr_players, prev_players):
        if curr_players is None or prev_players is None:
            return
        
        for p in curr_players:
            p : ActivePlayer = p
            if p not in prev_players:
                self.rcon.send_message(f"({self.time_handler.get_hr_min_string()}) {p.get_name()} has logged in!")
        
        for p in prev_players:
            p : ActivePlayer = p
            if p not in curr_players:
                self.rcon.send_message(f"({self.time_handler.get_hr_min_string()}) {p.get_name()} has logged out!")

    def increase_playtimes(self, curr_players, prev_players, add: int):
        if curr_players is None or prev_players is None:
            return

        for p in curr_players:
            p : ActivePlayer = p
            if p in prev_players:
                p.update_playtime(add)

    def grind_notifier(self, players):
        if players is None:
            return
        
        for p in players:
            p : ActivePlayer = p            
            if p.playtime % (24*60*60) == 0 and p.playtime != 0:
                self.rcon.send_message(f"{p.get_name()} has grinded for {int(p.playtime / (24*60*60))} full days!")
