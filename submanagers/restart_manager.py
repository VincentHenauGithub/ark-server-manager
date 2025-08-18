import json

from arkparse.api.rcon_api import RconApi
from arkparse.ftp.ark_ftp_client import ArkFtpClient, INI, ArkMap

from .time_handler import TimeHandler, PreviousDate
from .__manager import Manager

passwords = None
with open("passwords.json", 'r') as pass_file:
    passwords = json.load(pass_file)
    
OPEN_PASSWORD=passwords["known"]
SECRET_PASSWORD=passwords["secret"]

LAST_TIMESTAMPS = {
    "print": None,
    "open": None,
    "close": None,
    "restart_ping": None,
    "password_change": None,
    "dinowipe": None,
}

RESTARTS = {
    "weekStartup": 8,
    "weekShutdown": 0,
    "weekendStartup": 8,
    "weekendShutdown": 0,
}

class RestartManager(Manager):
    def __init__(self, rconapi: RconApi, ftp_config: dict):
        super().__init__(self.__process, "restart manager", 30)
        self.time_handler: TimeHandler = TimeHandler(RESTARTS["weekStartup"], RESTARTS["weekShutdown"], RESTARTS["weekendStartup"], RESTARTS["weekendShutdown"])
        self.rcon : RconApi = rconapi
        self.ftp : ArkFtpClient = ArkFtpClient.from_config(ftp_config, ArkMap.RAGNAROK)
        self.ftp.close()
        self.wipe_on = ["Monday", "Wednesday", "Friday"]  # Days to wipe dinos
        self.restarts = RESTARTS.copy()
        self.last_timestamps = LAST_TIMESTAMPS.copy()
        self.secret_password = SECRET_PASSWORD
        self.open_password = OPEN_PASSWORD
        self.warning_times = [60, 45, 30, 25, 20, 15, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]  
        self.next_restart_playable = self.time_handler.is_next_restart_playable()
        self.password_changed = False
        self.in_countdown = False

    def __process(self, interval: int):
        last_print: PreviousDate = LAST_TIMESTAMPS["print"]
        if last_print is None or last_print.has_been_quarter_hour():
            self._print(f"Next restart in: {self.time_handler.time_until_next_restart()} minutes ({self.time_handler.time_until_next_restart() / 60:.2f} hours); next restart is playable: {'Yes' if self.time_handler.is_next_restart_playable() else 'No'}")
            LAST_TIMESTAMPS["print"] = PreviousDate()    
        self.restart_warning()
        self.wipe_dinos()

    def restart_warning(self):
        time_to = self.time_handler.time_until_next_restart()

        if time_to > 60:
            self.in_countdown = False
            self.password_changed = False
            return

        if time_to < 60 and not self.in_countdown:
            self._print("entering countdown mode")
            self.in_countdown = True
            self.rcon.send_message(f"Server will shut down in {time_to} minutes!")
            self.last_timestamps["restart_ping"] = PreviousDate()

        next_playable = self.time_handler.is_next_restart_playable()
        if next_playable != self.next_restart_playable:
            self._print(f"Next restart playable changed: {self.next_restart_playable} -> {next_playable}")
            if self.next_restart_playable:
                self.last_timestamps["open"] = PreviousDate()
            else:
                self.last_timestamps["close"] = PreviousDate()
            self.next_restart_playable = next_playable


        if (self.in_countdown and
            ((self.last_timestamps["restart_ping"] is None) or
            (self.last_timestamps["restart_ping"].more_than_ago(minutes=10)) or
            (time_to < 10 and self.last_timestamps["restart_ping"].is_new_minute()))):
            self._print("Sending restart warning")
            self.rcon.send_message(f"Server will shut down in {time_to} minutes!")
            self.last_timestamps["restart_ping"] = PreviousDate()

            if not self.password_changed:
                self._print("Changing server password")
                new_pass = self.open_password if self.time_handler.is_next_restart_playable() else self.secret_password
                self.ftp.connect()
                self.ftp.change_ini_setting("ServerPassword", new_pass, INI.GAME_USER_SETTINGS)
                self.ftp.close()
                self._print(f"Server password changed to {new_pass}")
                self.password_changed = True

    def wipe_dinos(self):
        last_close : PreviousDate = self.last_timestamps["close"]
        last_wipe : PreviousDate = self.last_timestamps["dinowipe"]

        if last_close is None:
            return
        
        if last_wipe is not None and not(last_wipe.is_new_day() or last_wipe.is_new_minute()):
            return

        if self.time_handler.is_next_restart_playable() and self.time_handler.is_day_of_list(self.wipe_on) and last_close.minutes_since() == 15:
            self.rcon.send_cmd("DestroyWildDinos")
            message = f"Wiping dinos ({self.time_handler.get_hr_min_string()}): "
            self.rcon.send_message(message)
            self.last_timestamps["dinowipe"] = PreviousDate()
