from pathlib import Path
import datetime
import time

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
vote_manager = VoteManager(RCON)
rs_manager = RandomStatManager(FTP_CONF, RCON)

activity_manager.start(INTERVAL)
restart_manager.start(INTERVAL)
vote_manager.start(INTERVAL)
rs_manager.start(1020)

while True:
    print(f"\n{datetime.datetime.now()}: Main thread running")
    print(f"Activity Manager Thread Alive: {activity_manager.is_alive()}")
    print(f"Restart Manager Thread Alive: {restart_manager.is_alive()}")
    print(f"Vote Manager Thread Alive: {vote_manager.is_alive()}")
    print(f"Random Stat Manager Thread Alive: {rs_manager.is_alive()}")
    time.sleep(300)
