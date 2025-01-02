from pathlib import Path
import datetime
import time
import keyboard

from arkparse.api.rcon_api import RconApi, PlayerDataFiles
from submanagers.player_activity_manager import PlayerActivityManager
from submanagers.restart_manager import RestartManager
from submanagers.vote_manager import VoteManager
from submanagers.random_stat_manager import RandomStatManager

INTERVAL = 1
RCON : RconApi = RconApi.from_config("rcon_config.json")
FTP_CONF = "ftp_config.json"

PlayerDataFiles.set_files(players_files_path=Path("players.json"))

activity_manager = PlayerActivityManager(RCON)
restart_manager = RestartManager(RCON, FTP_CONF)
vote_manager = VoteManager(RCON, FTP_CONF)
rs_manager = RandomStatManager(FTP_CONF, RCON)

activity_manager.start(INTERVAL)
restart_manager.start(INTERVAL)
vote_manager.start(INTERVAL)
rs_manager.start(1020)

t = 0

try:
    while True:
        if keyboard.is_pressed('ctrl+q'):
            print("Quitting...")
            activity_manager.stop()
            restart_manager.stop()
            vote_manager.stop()
            rs_manager.stop()
            break
        if t % 300 == 0:
            print(f"{datetime.datetime.now()}: Main thread running")
        time.sleep(1)
        t += 1
except KeyboardInterrupt:
    print("Interrupted by user")
    activity_manager.stop()
    restart_manager.stop()
    vote_manager.stop()
    rs_manager.stop()
