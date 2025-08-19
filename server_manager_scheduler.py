from pathlib import Path
import datetime
import time

from arkparse.enums import ArkMap
from arkparse import AsaSave
from arkparse.api.rcon_api import RconApi, PlayerDataFiles
from submanagers.player_activity_manager import PlayerActivityManager
from submanagers.save_tracker import SaveTracker
from submanagers.restart_manager import RestartManager
from submanagers.vote_manager import VoteManager
from submanagers.random_stat_manager import RandomStatManager
from submanagers.raid_base_manager import RaidBaseManager
from submanagers.dino_finder import DinoFinder
from submanagers.main_base_reporter import MainBaseReporter
from submanagers.chat_logger import ChatLogger
from submanagers.errorcatch import ErrorCatch
from submanagers.loot_house_manager import LootHouseManager
from submanagers.dino_boss_manager import DinoBossManager
from submanagers.command_manager import CommandManager

FTP_CONF = "ftp_config.json"
PlayerDataFiles.set_files(players_files_path=Path("players.json"))
MAP = ArkMap.RAGNAROK

class ServerManagerScheduler:
    """
    Server Manager Scheduler is responsible for managing the server's lifecycle,
    including player activity, save tracking, and various submanagers.
    """

    def __init__(self):
        self.start_time = datetime.datetime.now()
        self.rcon = RconApi.from_config("rcon_config.json")
        self.save_tracker = SaveTracker(ftp_config=FTP_CONF, map=MAP)
        self.activity_manager = PlayerActivityManager(self.rcon)
        self.dino_finder = DinoFinder(self.save_tracker, self.rcon, MAP)
        self.restart_manager = RestartManager(self.rcon, FTP_CONF)
        # self.vote_manager = VoteManager(SAVE_TRACKER, RCON)
        self.random_stat_manager = RandomStatManager(self.save_tracker, self.rcon)
        self.raid_base_manager = RaidBaseManager(self.rcon, self.save_tracker, Path.cwd() / "bases")
        self.main_base_reporter = MainBaseReporter(self.save_tracker, self.rcon)
        self.loot_house_manager = LootHouseManager(self.save_tracker, self.rcon)
        self.dino_boss_manager = DinoBossManager(self.rcon, self.save_tracker)
        self.chat_logger = ChatLogger(self.rcon)
        self.command_manager = CommandManager(self.rcon, self.save_tracker)

    def _print(self, message):
        current_time = time.strftime("%H:%M:%S", time.localtime())
        print(f"[{current_time}][scheduler] {message}")

    def is_10_minute_interval(self):
        cur_time = datetime.datetime.now()
        return (cur_time.minute % 10 == 0) and (cur_time.second == 0)

    def run(self):
        """
        Run the server manager scheduler.
        This function initializes and starts all submanagers.
        """
        while True:
            try:
                if self.is_10_minute_interval():
                    self._print("Schedule alive, running submanagers...")

                self.save_tracker.process()
                self.raid_base_manager.process()
                self.chat_logger.process()
                self.main_base_reporter.process()
                self.activity_manager.process()
                self.dino_finder.process()
                self.restart_manager.process()
                self.loot_house_manager.process()
                self.random_stat_manager.process()
                self.dino_boss_manager.process()
                self.command_manager.process()

            except Exception as e:
                self._print(f"Error in server manager scheduler: {e}")
                if not ErrorCatch.CATCH_ERRORS:
                    raise e

            time.sleep(1)  # Sleep to prevent busy waiting

if __name__ == "__main__":
    scheduler = ServerManagerScheduler()
    scheduler._print("Starting server manager scheduler...")
    ErrorCatch.set_catch_errors(True)

    # save_path = Path("D:\\SteamLibrary\\steamapps\\common\\ARK Survival Ascended\\ShooterGame\\Saved\\SavedArksLocal\\Ragnarok_WP\\_Ragnarok_WP.ark")
    # save = AsaSave(save_path)
    # scheduler.save_tracker.set_save(save)
    # scheduler.raid_base_manager.test_full()
    
    try:
        scheduler.run()
    # except KeyboardInterrupt:
    #     scheduler._print("Server manager scheduler stopped by user.")
    except Exception as e:
        scheduler._print(f"Unexpected error: {e}")
        if not ErrorCatch.CATCH_ERRORS:
            raise e

