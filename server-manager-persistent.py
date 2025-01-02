from pathlib import Path
import datetime
import time

from arkparse.api.rcon_api import RconApi, PlayerDataFiles
from submanagers.player_activity_manager import PlayerActivityManager
from submanagers.restart_manager import RestartManager
from submanagers.vote_manager import VoteManager
from submanagers.random_stat_manager import RandomStatManager
from submanagers.raid_base_manager import RaidBaseManager
from arkparse.logging import ArkSaveLogger

INTERVAL = 1
RCON : RconApi = RconApi.from_config("rcon_config.json")
FTP_CONF = "ftp_config.json"

PlayerDataFiles.set_files(players_files_path=Path("players.json"))

activity_manager = PlayerActivityManager(RCON)
restart_manager = RestartManager(RCON, FTP_CONF)
vote_manager = VoteManager(RCON, FTP_CONF)
# ArkSaveLogger.enable_debug = True
rs_manager = RandomStatManager(FTP_CONF, RCON)
rb_manager = RaidBaseManager(RCON, FTP_CONF, Path.cwd() / "bases")

# while True:
#     rs_manager.testprocess()
#     time.sleep(1)

activity_manager.start(INTERVAL)
restart_manager.start(INTERVAL)
vote_manager.start(INTERVAL)
rs_manager.start(600)
rb_manager.start(60)

def _print(message):
        current_time = time.strftime("%H:%M:%S", time.localtime())
        print(f"[{current_time}][main thread] {message}")

while True:
    print("")
    _print(f"{datetime.datetime.now()}: Main thread running")
    _print(f"Activity Manager Thread Alive: {activity_manager.is_alive()}")
    _print(f"Restart Manager Thread Alive: {restart_manager.is_alive()}")
    _print(f"Vote Manager Thread Alive: {vote_manager.is_alive()}")
    _print(f"Random Stat Manager Thread Alive: {rs_manager.is_alive()}")
    _print(f"Raid Base Manager Thread Alive: {rb_manager.is_alive()}\n")

    if activity_manager.is_alive() == False:
        _print("Restarting Activity Manager")
        activity_manager.start(INTERVAL)

    if restart_manager.is_alive() == False:
        _print("Restarting Restart Manager")
        restart_manager.start(INTERVAL)

    if vote_manager.is_alive() == False:
        _print("Restarting Vote Manager")
        vote_manager.start(INTERVAL)
    
    if rs_manager.is_alive() == False:
        _print("Restarting Random Stat Manager")
        rs_manager.start(600)

    if rb_manager.is_alive() == False:
        _print("Restarting Raid Base Manager")
        rb_manager.start(60)

    print("")
    time.sleep(300)
