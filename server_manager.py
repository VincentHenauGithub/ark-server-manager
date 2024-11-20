from arkparse.api.rcon_api import RconApi, PlayerDataFiles
from arkparse.ftp.ark_ftp_client import ArkFtpClient

from submanagers.player_activity_manager import PlayerActivityManager
from submanagers.restart_manager import RestartManager
from submanagers.vote_manager import VoteManager

INTERVAL = 1
RCON : RconApi = RconApi.from_config("rcon_config.json")
FTP: ArkFtpClient = ArkFtpClient.from_config("ftp_config.json")
PlayerDataFiles.set_files(playtime_file_path="playtime.json", player_id_to_name_path="player_id_to_name.json")

activity_manager = PlayerActivityManager(RCON)
restart_manager = RestartManager(RCON, FTP)
vote_manager = VoteManager(RCON)

activity_manager.start(INTERVAL)
restart_manager.start(INTERVAL)
vote_manager.start(INTERVAL)

if input("Press 'q' to quit\n").strip().lower() == 'q':
    print("Quitting...")
    FTP.close()
    activity_manager.stop()
    restart_manager.stop()
    vote_manager.stop()