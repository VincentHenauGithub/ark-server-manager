from pathlib import Path
import json
import random
import time
from typing import List

from arkparse import MapCoords, Classes
from arkparse.enums import ArkMap
from arkparse.api import BaseApi, EquipmentApi, PlayerApi
from arkparse.api.rcon_api import RconApi
from arkparse.parsing.struct import ActorTransform
from arkparse.object_model.bases.base import Base
from arkparse.object_model.misc.object_owner import ObjectOwner
from arkparse.object_model.structures.structure_with_inventory import StructureWithInventory
from .__manager import Manager
from .time_handler import TimeHandler, PreviousDate
from .loot_configuration import add_loot
from .save_tracker import SaveTracker
from .locations import LocationController
from .nitrado_api import NitradoClient
from arkparse.object_model.ark_game_object import ArkGameObject
from arkparse.logging import ArkSaveLogger

BASE_SIZES = [
    {
        "min_turrets": 0,
        "max_turrets": 15,
        "active": True,
        "types": [
            "starter"
        ]
    },
    {
        "min_turrets": 15,
        "max_turrets": 30,
        "active": True, 
        "types": [
            "starter",
            "medium"
        ]
    },
    {
        "min_turrets": 30,
        "max_turrets": 40,
        "active": True, 
        "types": [
            "starter",
            "medium"
        ]
    },
    {
        "min_turrets": 40,
        "max_turrets": 50,
        "active": False, 
        "types": [
            "medium",
            "large"
        ]
    },
    {
        "min_turrets": 50,
        "max_turrets": 75,
        "active": False, 
        "types": [
            "medium",
            "large"
        ]
    },
    {
        "min_turrets": 50,
        "max_turrets": 75,
        "active": False, 
        "types": [
            "mixed"
        ]
    },
    {
        "min_turrets": 75,
        "max_turrets": 100,
        "active": False, 
        "types": [
            "medium",
            "large"
        ]
    },
    {
        "min_turrets": 75,
        "max_turrets": 100,
        "active": False, 
        "types": [
            "mixed"
        ]
    }
]

class RaidBaseManager(Manager):
    def __init__(self, rconapi: RconApi, save_tracker: SaveTracker, base_path: Path):
        super().__init__(self.__process, "raid base manager", 450)
        self.rcon: RconApi = rconapi

        self.save_tracker: SaveTracker = save_tracker
        self.time_handler: TimeHandler = TimeHandler()

        self.data_path = base_path / "data.json"
        self.owner_path = base_path / "owners.json"
        self.data_ = self.__init_data(self.data_path)
        self.base_path = base_path
        self.config: dict = json.load(open(base_path / "config.json", 'r'))
        self.last_timestamp: PreviousDate = None
        self.last_message: PreviousDate = None

        self.__save_data(self.data_path)

    def get_nr_of_bases(self) -> int:
        return len(self.data_["active_bases"])

    def __init_data(self, path: Path):
        if not path.exists():
            return {
                "active_bases": [],
            }
        else:
            with open(path, 'r') as f:
                return json.load(f)
    def __save_data(self, path: Path):
        with open(path, 'w') as f:
            json.dump(self.data_, f, indent=4)

    def __is_base_raided(self, coords: MapCoords, owner_tribe_name: str, radius: float = 1, map: ArkMap = ArkMap.RAGNAROK) -> bool:
        structures = self.save_tracker.get_api(BaseApi).get_at_location(map, coords, radius)

        all_vaults = [structure for _, structure in structures.items() if structure.object.blueprint == Classes.structures.placed.utility.vault]
        self._print(f"Nr of vaults found: {len(all_vaults)}")
        for vault in all_vaults:
            self._print(f"Vault owner tribe name: {vault.owner.tribe_name}, checking against {owner_tribe_name}")
            if vault.owner.tribe_name == owner_tribe_name:
                if vault.inventory is not None and len(vault.inventory.items) > 0:
                    return False
                
        return True

    def __get_main_location(self, loc_file: Path) -> MapCoords:
        jsn = json.load(loc_file.open())
        for loc in jsn.keys():
            if jsn[loc]["type"] == "main":
                return ActorTransform.from_json(jsn[loc]["location"]).as_map_coords(ArkMap.RAGNAROK)

    def __get_random_owner(self) -> int:
        owners = json.load(open(self.owner_path, 'r'))
        unused_owners = []

        # Filter used
        for owner in owners:
            used = False
            for base in self.data_["active_bases"]:
                if base["owner"]["name"] == owner["name"]:
                    used = True
                    break
            if not used:
                unused_owners.append(owner)

        return random.choice(unused_owners)
    
    def __get_enabled_config(self) -> list:
        enabled_configs = []
        for config in BASE_SIZES:
            if config["active"]:
                enabled_configs.append(config)
        return enabled_configs
    
    def __get_available_main_bases(self, types: List[str]) -> list:
        base_folder_path = self.base_path / "base"
        available_bases = []
        for base_file in base_folder_path.iterdir():
            prefix = base_file.name.split("_")[0]
            if prefix in types:
                available_bases.append(base_file)
        return available_bases
    
    def __get_available_towers(self, types: List[str]) -> list:
        base_folder_path = self.base_path / "tower"
        available_bases = []
        for base_file in base_folder_path.iterdir():
            prefix = base_file.name.split("_")[0]
            if prefix in types:
                available_bases.append(base_file)
        return available_bases

    def compose_base(self):
        cfg = random.choice(self.__get_enabled_config())
        loc_config, file, _ = LocationController.get_random_unblocked_location(self.save_tracker.get_api(BaseApi), radius=1, map=ArkMap.RAGNAROK, limit=5)
        turret_total = 0
        curr_tries = 0

        bases = self.__get_available_main_bases(cfg["types"])
        towers = self.__get_available_towers(cfg["types"])

        self._print(f"[Base]Selected {len(bases)} bases and {len(towers)} towers for configuration {cfg['types']}")

        while cfg["min_turrets"] >= turret_total or cfg["max_turrets"] <= turret_total:
            if curr_tries > 50:
                loc_config, file, _ = LocationController.get_random_unblocked_location(self.save_tracker.get_api(BaseApi), radius=1, map=ArkMap.RAGNAROK, limit=5)
                curr_tries = 0

            config = {
                "locations": loc_config,
                "location": file,
                "total_turrets": 0,
                "mixed": True if "mixed" in cfg["types"] else False,
            }

            curr_tries += 1
            turret_total = 0
            for loc in loc_config.keys():
                if config["locations"][loc]["type"] == "main":
                    selected_base = random.choice(bases)
                    config["locations"][loc]["selected_path"] = str(selected_base)
                elif config["locations"][loc]["type"] == "tower":
                    selected_tower = random.choice(towers)
                    config["locations"][loc]["selected_path"] = str(selected_tower)

                config["locations"][loc]["selection"] = json.load(open(Path(config["locations"][loc]["selected_path"]) / "base.json", 'r'))

                turret_total += config["locations"][loc]["selection"]["nr_of_turrets"]

        LocationController.add_active_location(file)
        config["total_turrets"] = turret_total

        return config
    
    def __clean_other_vaults(self, base: Base, loot_vault: StructureWithInventory):
        all_vaults = [structure for _, structure in base.structures.items() if structure.object.blueprint == Classes.structures.placed.utility.vault]
        for vault in all_vaults:
            vault: StructureWithInventory
            if vault.uuid != loot_vault.uuid:
                vault.inventory.clear_items()
        self._print(f"[Loot]Cleared other vaults in base")

    def __add_loot(self, base: Base, nr_of_turrets: int, mixed: bool):
        def get_vault(base: Base) -> StructureWithInventory:
            all_vaults = [structure for _, structure in base.structures.items() if structure.object.blueprint == Classes.structures.placed.utility.vault]
            random_vault = random.choice(all_vaults)
            return random_vault

        selected_vault: StructureWithInventory = get_vault(base)
        initial_vault_items = selected_vault.inventory.items.copy()

        add_loot(self, nr_of_turrets, self.save_tracker.get_save(), selected_vault, self.save_tracker.get_api(EquipmentApi), mixed=mixed)

        self._print(f"[Loot]Added loot to vault {selected_vault.uuid} in base")
        self.__clean_other_vaults(base, selected_vault)

    def __spawn_section(self, path: Path, loc: ActorTransform, owner: ObjectOwner):
        self._print("[Spawn]Importing section from {path}")
        base: Base =  self.save_tracker.get_api(BaseApi).import_base(path, location=loc)
        self._print(f"[Spawn]Section imported at {loc.as_map_coords(ArkMap.RAGNAROK)}")

        for _, structure in base.structures.items():
            if structure.object.blueprint == Classes.structures.placed.metal.generator:
                structure.object.change_class(Classes.structures.placed.tek.generator, structure.binary)
                structure.update_binary()
                structure.object = ArkGameObject(uuid=structure.uuid, blueprint=Classes.structures.placed.tek.generator, binary_reader=structure.binary)
                structure.owner.properties = structure.object
                self._print("[Spawn]Generator converted to TEK")

        base.set_turret_ammo(self.save_tracker.get_save(), bullets_in_auto=1400, bullets_in_heavy=2500, shards_in_tek=1500)
        self._print("[Spawn]Turret ammo padded")
        base.set_fuel_in_generators(self.save_tracker.get_save(), nr_of_element=3, nr_of_gasoline=30)
        self._print("[Spawn]Element added to generators")
        
        base.set_owner(owner)
        self._print(f"[Spawn]Owner set to {owner.tribe_name} ({owner.tribe_id})")
        return base

    def spawn_base(self, base_config: dict, map: ArkMap = ArkMap.RAGNAROK):
        base_status = {
            "is_raided": False,
            "raid_broadcasted": False,
            "config": base_config,
            "tribe_id": None,
            "player_id": None,
            "owner": self.__get_random_owner()
        }
        turrets = base_config["total_turrets"]
        loc_config: dict = base_config["locations"]
        o: ObjectOwner = ObjectOwner()
        tribe_id = self.save_tracker.get_api(PlayerApi).generate_tribe_id()
        player_id = self.save_tracker.get_api(PlayerApi).generate_player_id()
        o.set_tribe(tribe_id, base_status["owner"]["name"])
        o.set_player(player_id)
        for loc in loc_config.keys():
            path = loc_config[loc]["selected_path"]
            actor_transform = ActorTransform.from_json(
                loc_config[loc]["location"])
            base = self.__spawn_section(
                path, actor_transform, o)
            self._print("[Spawn]Spawned base section")
            base_status["tribe_id"] = tribe_id
            base_status["player_id"] = player_id
            if loc_config[loc]["type"] == "main":
                base_status["location"] = str(
                    actor_transform.as_map_coords(map))
                self._print("[Spawn]Adding loot to the base")
                self.__add_loot(base, turrets, mixed=base_config["mixed"])
        self._print("[Spawn]Base inserted, saving...")

        self.data_["active_bases"].append(base_status)
        self.__save_data(self.data_path)
        self._print("[Spawn]Import complete")

    def __pad_active_base_generators(self):
        for base in self.data_["active_bases"]:
            loc: str = base["location"]
            x, y = map(float, loc.strip("()").split(", "))
            coords = MapCoords(x, y)
            base: Base =  self.save_tracker.get_api(BaseApi).get_base_at(coords, 2, owner_tribe_name=base["owner"]["name"])
            print(f"Nr of items in base: {len(base.structures)}")
            nr = base.set_fuel_in_generators(self.save_tracker.get_save(), nr_of_element=3, nr_of_gasoline=277)
            self._print(f"[Spawn]Fuel added to {nr} generators at {coords}")

    def __check_raided(self):
        for base in self.data_["active_bases"]:
            file_path = self.base_path / "locations" / \
                "ragnarok" / base["config"]["location"]
            if self.__is_base_raided(self.__get_main_location(file_path), owner_tribe_name=base["owner"]["name"]) and not base["is_raided"]:
                base["is_raided"] = True
                self._print(f"[Raided]Base at {base['location']} is raided")
                self._print(f"[Raided]{base['owner']['raided']}")
                self.rcon.send_message(f"{base['owner']['raided']}")
            elif not base["is_raided"]:
                self._print(f"[Active]Base at {base['location']} is active")
            else:
                self._print(f"[Raided]Base at {base['location']} is still raided")
        self.__save_data(self.data_path)

    def __remove_raided(self):
        data_copy = self.data_["active_bases"].copy()
        for base in self.data_["active_bases"]:
            if base["is_raided"]:
                loc: str = base["location"]
                x, y = map(float, loc.strip("()").split(", "))
                coords = MapCoords(x, y)
                self._print(f"[Raided]Removing base at {coords}")
                self.save_tracker.get_api(BaseApi).remove_at_location(
                    ArkMap.RAGNAROK, coords, 2, owner_tribe_name=base["owner"]["name"])
                data_copy.remove(base)
                LocationController.remove_active_location(base["config"]["location"])
        self.data_["active_bases"] = data_copy
        self.__save_data(self.data_path)

    def __process(self, interval: int):
        self.main()

    def __put_save(self):
        self.save_tracker.put_save()

    def _print_tp_command(self, config: dict):
        locations = config["locations"]
        for loc in locations.keys():
            if locations[loc]["type"] == "main":
                coords = ActorTransform.from_json(locations[loc]["location"])
                map_loc = coords.as_map_coords(ArkMap.RAGNAROK)
                self._print(f"TP COMMAND: cheat TPCoords {map_loc.lat} {map_loc.long} {int(coords.z + 3000)}")

    def main(self):
        self._print(f"[Main]Checking for bases (hour={time.localtime().tm_hour})")
        # check if any bases have been raided
        self.__check_raided()

        if True and (time.localtime().tm_hour == 5 and (self.last_timestamp is None or self.last_timestamp.has_been_hour())):
            self.save_tracker.stop_and_update()

            self.last_timestamp = PreviousDate()
            self._print("[Main]Spawning and updating bases")
            
            # remove raided bases
            self.__remove_raided()

            # spawn up to 5 bases
            if len(self.data_["active_bases"]) <= 1:
                for _ in range(5):
                    cfg = self.compose_base()
                    self.spawn_base(cfg)

            # Pad generators
            self.__pad_active_base_generators()

            self.__put_save()

        nr_online = len(self.rcon.get_active_players())

        # Report active bases
        minutes_since = 150 if self.last_message is None else self.last_message.minutes_since()
        prnt = False
        self._print(f"[Active]Minutes since last message: {minutes_since}; {'printing' if minutes_since > 127 else 'not printing'}")
        if minutes_since > 127:
            self.last_message = PreviousDate()
            prnt = True

        for base in self.data_["active_bases"]:
            if not base["is_raided"]:
                self._print(f"[Active]{base['owner']['message']}{base['location']}")
                message = f"{base['owner']['message']}{base['location']}"
                self._print_tp_command(base["config"])
                if prnt:
                    if nr_online < 3:
                        self._print(f"[Active]Not enough players online ({nr_online}), not sending coords")
                        message = message.split(' at ')[0] + " at an undisclosed location"
                    self.rcon.send_message(message)

    def test_full(self):
        self._print("[Main]Checking for bases")
        # self.__get_save()

        self.data_["active_bases"] = []
        self._print("[Main]Spawning and updating bases")

        for _ in range(3):
            if len(self.data_["active_bases"]) >= 3:
                break
            cfg = self.compose_base()
            self.spawn_base(cfg)

        # Pad generators
        self.__pad_active_base_generators()
        store_path = Path("D:\\SteamLibrary\\steamapps\\common\\ARK Survival Ascended\\ShooterGame\\Saved\\SavedArksLocal\\Ragnarok_WP\\Ragnarok_WP.ark")
        self.save_tracker.get_save().store_db(store_path)

        for base in self.data_["active_bases"]:
            if not base["is_raided"]:
                self._print(f"[Active]Base at {base['location']} is active")
                self._print(f"[Active]{base['owner']['message']}{base['location']}")
                self.rcon.send_message(
                    f"{base['owner']['message']}{base['location']}")

    def test_hour(self):
        self._print("[Main]Checking for bases")
        self.save_tracker.get_save()
        # check if any bases have been raided
        self.__check_raided()

        for base in self.data_["active_bases"]:
            if not base["is_raided"]:
                self._print(f"[Active]Base at {base['location']} is active")
                self._print(f"[Active]{base['owner']['message']}{base['location']}")
                self.rcon.send_message(
                    f"{base['owner']['message']}{base['location']}")


# base = Path.cwd().parent / "bases"
# rcon = RconApi.from_config(Path.cwd().parent / "rcon_config.json")
# mngr = RaidBaseManager(rcon, "../ftp_config.json", base)

# mngr.test_hour()
