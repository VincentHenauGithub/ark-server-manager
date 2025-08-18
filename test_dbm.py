from pathlib import Path

from arkparse.enums import ArkMap
from arkparse import AsaSave
from arkparse.api.rcon_api import RconApi, PlayerDataFiles
from submanagers.save_tracker import SaveTracker
from submanagers.dino_boss_manager import DinoBossManager
from arkparse.logging import ArkSaveLogger

FTP_CONF = "ftp_config.json"
PlayerDataFiles.set_files(players_files_path=Path("players.json"))
MAP = ArkMap.RAGNAROK
save_path = Path("D:\\SteamLibrary\\steamapps\\common\\ARK Survival Ascended\\ShooterGame\\Saved\\SavedArksLocal\\Ragnarok_WP\\Ragnarok_WP.ark")


if __name__ == "__main__":
    ArkSaveLogger.set_log_level(ArkSaveLogger.LogTypes.OBJECTS, False)
    ArkSaveLogger.set_log_level(ArkSaveLogger.LogTypes.API, False)
    rcon = RconApi.from_config("rcon_config.json")
    save_tracker = SaveTracker(ftp_config=FTP_CONF, map=MAP)
    dino_boss_manager = DinoBossManager(rcon, save_tracker)
    save = AsaSave(save_path)
    save_tracker.set_save(save)
    dino_boss_manager.main()

