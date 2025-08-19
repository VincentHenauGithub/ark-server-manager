from enum import member
from .dino_spawns.state_controllers import LocationController, MenagerieMemberState, MenagerieState
from pathlib import Path
import json
import random
import time
from typing import List, Dict, Union

from arkparse import MapCoords, Classes
from arkparse.enums import ArkMap, ArkStat
from arkparse.api import BaseApi, EquipmentApi, PlayerApi
from arkparse.api.rcon_api import RconApi
from arkparse.parsing.struct import ActorTransform
from arkparse.object_model.bases.base import Base
from arkparse.object_model.misc.dino_owner import DinoOwner
from arkparse.object_model.dinos.tamed_dino import TamedDino
from arkparse.object_model.structures.structure_with_inventory import StructureWithInventory
from .__manager import Manager
from .time_handler import TimeHandler, PreviousDate
from .loot_configuration import add_loot
from .save_tracker import SaveTracker

CONFIG = [
    { "enabled": True,  "type": "land",  "path": "skippy",   "added_levels": 90,  "base_levels": 255, "difficulty_level": 7,  "mixed": False , "blueprint": Classes.dinos.non_tameable.alpha.alpha_raptor       },
    { "enabled": True,  "type": "land",  "path": "skippy",   "added_levels": 170,  "base_levels": 255, "difficulty_level": 20, "mixed": False , "blueprint": Classes.dinos.non_tameable.alpha.alpha_raptor       },
    { "enabled": True,  "type": "water", "path": "sicko",    "added_levels": 255, "base_levels": 255, "difficulty_level": 20, "mixed": False , "blueprint": Classes.dinos.non_tameable.alpha.alpha_leedsichthys },
    { "enabled": False,  "type": "land",  "path": "barny",    "added_levels": 115,  "base_levels": 255, "difficulty_level": 35, "mixed": False , "blueprint": Classes.dinos.non_tameable.alpha.alpha_carnotaurus  },  
    { "enabled": False,  "type": "land",  "path": "candle",   "added_levels": 255, "base_levels": 255, "difficulty_level": 45, "mixed": False , "blueprint": Classes.dinos.non_tameable.alpha.alpha_fire_wyvern  },
    { "enabled": False,  "type": "land",  "path": "slithers", "added_levels": 255, "base_levels": 255, "difficulty_level": 60, "mixed": False , "blueprint": Classes.dinos.non_tameable.alpha.alpha_basilisk     },
    { "enabled": False,  "type": "water", "path": "jaws",     "added_levels": 255, "base_levels": 255, "difficulty_level": 60, "mixed": False , "blueprint": Classes.dinos.non_tameable.alpha.alpha_megalodon    },
    { "enabled": False,  "type": "land",  "path": "roger",    "added_levels": 255, "base_levels": 255, "difficulty_level": 60, "mixed": True  , "blueprint": Classes.dinos.non_tameable.alpha.alpha_rex          },
    { "enabled": False,  "type": "water", "path": "moose",    "added_levels": 255, "base_levels": 255, "difficulty_level": 60, "mixed": True  , "blueprint": Classes.dinos.non_tameable.alpha.alpha_mosasaurus   },
    { "enabled": False,  "type": "both",  "path": "pincers",  "added_levels": 255, "base_levels": 255, "difficulty_level": 99, "mixed": False , "blueprint": Classes.dinos.non_tameable.alpha.alpha_karkinos     },
    { "enabled": False,  "type": "water", "path": "toetsie",  "added_levels": 255, "base_levels": 255, "difficulty_level": 99, "mixed": False , "blueprint": Classes.dinos.non_tameable.alpha.alpha_tuso         },
    { "enabled": False, "type": "land",  "path": "dodow",    "added_levels": 255, "base_levels": 43,  "difficulty_level": 99, "mixed": True  , "blueprint": Classes.dinos.non_tameable.event.dodo_wyvern        }
]

class DinoBossManager(Manager):
    def __init__(self, rconapi: RconApi, save_tracker: SaveTracker):
        super().__init__(self.__process, "dino boss manager", 3456)
        self.rcon: RconApi = rconapi

        self.save_tracker: SaveTracker = save_tracker
        self.time_handler: TimeHandler = TimeHandler()
        self.last_timestamp: PreviousDate = None

        self.menagerie_state = MenagerieState()

    def __get_dino(self, menagerie_state: MenagerieMemberState) -> Union[TamedDino, ]:
        """
        Returns the dino associated with the given menagerie state.
        """
        tribe_id = menagerie_state.tribe_id
        blueprint = menagerie_state.blueprint
        
        d_api = self.save_tracker.dino_api
        entities = d_api.get_all_by_class([blueprint])

        for entity in entities.values():
            if isinstance(entity, TamedDino):
                if entity.owner.target_team == tribe_id:
                    return entity

        return None

    def __is_dino_killed(self, menagerie_state: MenagerieMemberState) -> bool:
        dino = self.__get_dino(menagerie_state)
        if dino is None:
            return True
        
        if dino.is_dead:
            return True
    
        return False

    def __get_random_enabled_config(self) -> Dict[str, Union[str, int, bool]]:
        """
        Returns a random enabled configuration from the CONFIG list.
        """
        enabled_configs = [config for config in CONFIG if config["enabled"]]
        return random.choice(enabled_configs) if enabled_configs else None
    
    def spawn_new(self):
        cfg = self.__get_random_enabled_config()
        line = self.menagerie_state.get_unused_line()
        dino_path = Path(__file__).parent / "dino_spawns" / cfg["path"]

        p_api = self.save_tracker.player_api
        d_api = self.save_tracker.dino_api
        save = self.save_tracker.save
        e_api = self.save_tracker.equipment_api

        owner = DinoOwner()
        owner.set_tribe(p_api.generate_tribe_id(), "The dread menagerie")
        owner.set_player(p_api.generate_player_id(), "The Admin")

        spawn = LocationController.get_random_free_location(cfg["type"], self.save_tracker.structure_api, dont_use=self.menagerie_state.used_locations)
        spawn.z += 1000

        dino: TamedDino = d_api.import_dino(dino_path, spawn)

        if not isinstance(dino, TamedDino):
            raise ValueError("Imported dino is not a TamedDino")
        
        dino.heal()
        dino.set_name(self.menagerie_state.get_unused_name())
        dino.stats.set_tamed_levels(cfg["added_levels"], ArkStat.HEALTH)
        dino.stats.set_tamed_levels(255, ArkStat.WEIGHT)
        dino.stats.set_tamed_levels(50, ArkStat.MELEE_DAMAGE)
        dino.stats.set_levels(cfg["base_levels"], ArkStat.HEALTH)
        dino.set_owner(owner)

        member_state: MenagerieMemberState = self.menagerie_state.add_member()

        member_state.mapcoords = spawn.as_map_coords(ArkMap.RAGNAROK)
        member_state.difficulty = cfg["difficulty_level"]
        member_state.mixed = cfg["mixed"]
        member_state.tribe_id = owner.target_team
        member_state.blueprint = cfg["blueprint"]
        member_state.location = spawn
        member_state.line = line

        add_loot(self, member_state.difficulty, save, dino, e_api, mixed=member_state.mixed)

        self._print(f"Spawning dino {dino.get_short_name()} ({dino.tamed_name}) at {member_state.mapcoords} with difficulty {member_state.difficulty} and line: {member_state.line}")

        return member_state

    def __process(self, interval: int):
        self.main()

    def main(self):
        self._print(f"Evaluating the dread menagerie, there are {self.menagerie_state.number_active} active members")

        to_remove = []
        for member in self.menagerie_state.members:
            if self.__is_dino_killed(member):
                self._print(f"Marking monster from menagerie state for removal, it was killed")
                self.rcon.send_message(f"A dread monster has been slain at {member.mapcoords}")
                to_remove.append(member)
            else:
                active_players = len(self.rcon.get_active_players())
                message = ""
                if active_players > 3:
                    dino: TamedDino = self.__get_dino(member)
                    member.mapcoords = dino.location.as_map_coords(ArkMap.RAGNAROK)
                    message = f"{member.line} {member.mapcoords}"
                else:
                    message = f"{member.line} an undisclosed location"

                self._print(message)
                self.rcon.send_message(message)
                self._print_tp_command(member)
        
        for member in to_remove:
            self.menagerie_state.remove_member(member)
            self._print(f"Removed member {member} from menagerie state")

        self._print(f"After evaluation, there are {self.menagerie_state.number_active} active members")

        if self.menagerie_state.number_active == 0 and time.localtime().tm_hour == 5:
            self._print("All dread monsters have been slain, spawning new ones...")
            while self.menagerie_state.number_active < 2:
                mem = self.spawn_new()
                self._print_tp_command(mem)

            self._print(f"Resetting location of all members in the menagerie")
            for member in self.menagerie_state.members:
                dino: TamedDino = self.__get_dino(member)
                if dino is None:
                    raise ValueError(f"Could not find dino for member {member}")
                dino.set_location(member.location)
                member.mapcoords = member.location.as_map_coords(ArkMap.RAGNAROK)

            self.__put_save()

    def __put_save(self):
        self.save_tracker.put_save()
        # store_path = Path("D:\\SteamLibrary\\steamapps\\common\\ARK Survival Ascended\\ShooterGame\\Saved\\SavedArksLocal\\Ragnarok_WP\\Ragnarok_WP.ark")
        # self.save_tracker.save.store_db(store_path)

    def _print_tp_command(self, member: MenagerieMemberState):
        loc = member.location
        map_loc = member.mapcoords
        self._print(f"TP COMMAND: cheat TPCoords {map_loc.lat} {map_loc.long} {int(loc.z + 3000)}")