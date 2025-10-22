import json
import time

from arkparse.api.rcon_api import RconApi
from arkparse.ftp.ark_ftp_client import ArkFtpClient, INI, ArkMap

from .time_handler import TimeHandler, PreviousDate
from .__manager import Manager
from .nitrado_api import NitradoClient

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
        super().__init__(self.__process, "restart manager", 10)
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
        self.next_password = None
        self.last_wipe_day = None

    def __process(self, interval: int):
        last_print: PreviousDate = LAST_TIMESTAMPS["print"]
        if last_print is None or last_print.has_been_quarter_hour():
            self._print(f"Next restart in: {self.time_handler.time_until_next_restart()} minutes ({self.time_handler.time_until_next_restart() / 60:.2f} hours); next restart is playable: {'Yes' if self.time_handler.is_next_restart_playable() else 'No'}")
            LAST_TIMESTAMPS["print"] = PreviousDate()    
        self.restart_warning()

    def restart_warning(self):
        time_to = self.time_handler.time_until_next_restart()

        if time_to < 60 and not self.in_countdown:
            self._print("entering countdown mode")
            self.in_countdown = True
            self.rcon.send_message(f"Server will shut down in {time_to} minutes!")
            self.last_timestamps["restart_ping"] = PreviousDate()

        next_playable = self.time_handler.is_next_restart_playable()
        # self._print("next password is " + self.next_password)
        # self._print(f"Next restart playable: {'Yes' if next_playable else 'No'}; current password is {'open' if self.password_changed else 'secret'}")
        if next_playable != self.next_restart_playable:
            self._print(f"Next restart playable changed: {self.next_restart_playable} -> {next_playable}")

            self._print("Stopping server")
            NitradoClient().stop_server()
            self._print(f"Server status: {NitradoClient().get_status()}")

            time.sleep(60 * 10) # wait 10 minutes to ensure the server has fully stopped and released the file lock

            self._print("Changing server password")
            new_pass = self.open_password if time.localtime().tm_hour >= 4 and time.localtime().tm_hour < 10 else self.secret_password
            self.ftp.connect()
            self.ftp.change_ini_setting("ServerPassword", new_pass, INI.GAME_USER_SETTINGS)
            self.ftp.close()
            self._print(f"Server password changed to {new_pass}")
            self.password_changed = True
            self.in_countdown = False
            self.next_password = self.open_password if self.next_restart_playable else self.secret_password
            self._print("Starting server")
            NitradoClient().start_server()
            self._print(f"Server status: {NitradoClient().get_status()}")

           
            
            if self.next_restart_playable:
                self.last_timestamps["open"] = PreviousDate()
            else:
                self.last_timestamps["close"] = PreviousDate()

            self.next_restart_playable = next_playable

        self.wipe_dinos()


        if (self.in_countdown and
            ((self.last_timestamps["restart_ping"] is None) or
            (self.last_timestamps["restart_ping"].more_than_ago(minutes=10)) or
            (time_to < 10 and self.last_timestamps["restart_ping"].is_new_minute()))):
            self._print("Sending restart warning")
            self.rcon.send_message(f"Server will shut down in {time_to} minutes!")
            self.last_timestamps["restart_ping"] = PreviousDate()

    def wipe_dinos(self):
        self._print(f"Day of list: {self.time_handler.is_day_of_list(self.wipe_on)}; hour={time.localtime().tm_hour}; last wipe day={self.last_wipe_day}; current day={self.time_handler._get_current_day()}", False)
        if self.time_handler.is_day_of_list(self.wipe_on) and (time.localtime().tm_hour == 1) and (self.last_wipe_day != self.time_handler._get_current_day()):
            self._print(f"Day of list: {self.time_handler.is_day_of_list(self.wipe_on)}; hour={time.localtime().tm_hour}; last wipe day={self.last_wipe_day}; current day={self.time_handler._get_current_day()}")
            
            response = None
            for _ in range(10):
                response = self.rcon.send_cmd("DestroyWildDinos")
                if response is not None:
                    break

            if response is not None:
                self.last_wipe_day = self.time_handler._get_current_day()
                self._print("Performing Dino Wipe, response: " + response)
                message = f"Wiping dinos ({self.time_handler.get_hr_min_string()}): "
                self.rcon.send_message(message)
                self.last_timestamps["dinowipe"] = PreviousDate()
            else:
                self._print("Dino wipe command failed")
            
         