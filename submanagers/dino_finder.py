from typing import List, Dict
from uuid import UUID

from arkparse.enums import ArkStat
from .__manager import Manager
from .save_tracker import SaveTracker
from arkparse.api import RconApi, DinoApi
from arkparse.object_model.dinos.dino import Dino
from arkparse.enums import ArkMap
from arkparse import Classes
import random

class DinoFinder(Manager):
    def __init__(self, save_tracker: SaveTracker, rconapi: RconApi, map: ArkMap):
        super().__init__(self.__process, "Dino finder", 1654)
        self.rcon_api: RconApi = rconapi
        self.map: ArkMap = map
        self.save_tracker: SaveTracker = save_tracker
        self.level_limits: List[int] = [0, 150]
        self.wanted_stats: List[ArkStat] = [
            ArkStat.HEALTH,
            ArkStat.STAMINA,
            ArkStat.WEIGHT,
            ArkStat.MELEE_DAMAGE
        ]
        self.wanted = list(set(Classes.dinos.all_bps) - set(Classes.dinos.non_tameable.all_bps))

    def __process(self, _: int = 0):        
        # self._print("Starting dino finder process")
        dino_api: DinoApi = self.save_tracker.get_api(DinoApi)
        dino_api.get_all()
        # self._print("Retrieved dinos...")        

        online_players = len(self.rcon_api.get_active_players())
        stat_search = 20 + online_players * 5

        candidates = {}
        while len(candidates) == 0:
            candidates: Dict[UUID: Dino] = dino_api.get_all_filtered(
                level_lower_bound= self.level_limits[0],
                level_upper_bound= self.level_limits[1],
                tamed=False,
                stats=self.wanted_stats,
                stat_minimum=stat_search,
                class_names=self.wanted
            )

            if len(candidates) == 0:
                stat_search -= 1

        self._print(f"Found {len(candidates)} candidates with stats >= {stat_search}")

        random_choice: Dino = random.choice(list(candidates.values()))

        self._print(f"Randomly selected dino: {random_choice.get_short_name()} (lvl {random_choice.stats.current_level})")
        self._print(f"Stats: {random_choice.stats.base_stat_points}")

        self.rcon_api.send_message(f"There is a creature with a core stat of {stat_search}+ running around at {random_choice.location.as_map_coords(self.map)}! Go get it!")