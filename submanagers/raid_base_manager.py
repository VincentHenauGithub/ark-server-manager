from pathlib import Path
import json
import random
import time

from arkparse import MapCoords, Classes, AsaSave
from arkparse.ftp import ArkFtpClient
from arkparse.enums import ArkMap, ArkEquipmentStat
from arkparse.api import StructureApi, BaseApi, EquipmentApi
from arkparse.api.rcon_api import RconApi, ActivePlayer
from arkparse.parsing.struct import ActorTransform
from arkparse.object_model.bases.base import Base
from arkparse.object_model.misc.object_owner import ObjectOwner
from arkparse.object_model.structures.structure_with_inventory import StructureWithInventory
from arkparse.object_model.stackables.resource import Resource
from .__manager import Manager
from .time_handler import TimeHandler, PreviousDate

class RaidBaseManager(Manager):
    def __init__(self, rconapi: RconApi, ftp_config: str, base_path: Path):
        super().__init__(self.__process, "raid base manager")
        self.rcon : RconApi = rconapi
        self.ftp: ArkFtpClient = ArkFtpClient.from_config(ftp_config, ArkMap.ABERRATION)
        self.ftp.close()

        self.save: AsaSave = None
        self.s_api: StructureApi = None,
        self.b_api: BaseApi = None
        self.e_api: EquipmentApi = None

        self.time_handler: TimeHandler = TimeHandler()

        self.data_path = base_path / "data.json"
        self.owner_path = base_path / "owners.json"
        self.data_ = self.__init_data(self.data_path)
        self.base_path = base_path
        self.config: dict = json.load(open(base_path / "config.json", 'r'))
        
        self.__save_data(self.data_path)

    def __init_data(self, path: Path):
        if not path.exists():
            return {
                "active_bases": [],
            }
        else:
            with open(path, 'r') as f:
                return json.load(f)

    def set_save(self, save: AsaSave, map: ArkMap = ArkMap.ABERRATION):
        self.save = save
        self.s_api = StructureApi(save)
        self.b_api = BaseApi(save, map)
        self.e_api = EquipmentApi(save)

    def __save_data(self, path: Path):
        with open(path, 'w') as f:
            json.dump(self.data_, f, indent=4)

    def __are_structures_present(self, coords: MapCoords, radius: float = 2, owner_tribe_id: int = 1, map: ArkMap = ArkMap.ABERRATION, limit : int = 5) -> bool:
        structures = self.s_api.get_at_location(map, coords, radius)
        filtered = self.s_api.filter_by_owner(structures, owner_tribe_id=owner_tribe_id, invert=True)

        result = False
        if len(filtered) > limit:
            result = True
            self._print(f"There are {len(filtered)} other structures around {coords}, cannot spawn here")

        return result

    def __is_base_raided(self, coords: MapCoords, radius: float = 1, owner_tribe_id: int = 1, map: ArkMap = ArkMap.ABERRATION) -> bool:
        structures = self.s_api.get_at_location(map, coords, radius)

        vault = None
        for _, structure in structures.items():
            if structure.object.blueprint == Classes.structures.placed.utility.vault and structure.owner.tribe_id == owner_tribe_id:
                vault = structure
                break

        if vault is None:
            return True
        
        if vault.inventory is None:
            return True
        
        if len(vault.inventory.items) == 0:
            return True
        
        return False
    
    def __is_base_spawned_at(self, loc_file: Path) -> bool:
        for base in self.data_["active_bases"]:
            if base["config"]["location"] == loc_file.name:
                return True
        return False
    
    def __get_main_location(self, loc_file: Path) -> MapCoords:
        jsn = json.load(loc_file.open())
        for loc in jsn.keys():
            if jsn[loc]["type"] == "main":
                return ActorTransform.from_json(jsn[loc]["location"]).as_map_coords(ArkMap.ABERRATION)
    
    def __get_blocked_locations(self, map: ArkMap = ArkMap.ABERRATION) -> list:
        blocked = []
        possible_locations = self.base_path / "locations" / "randomised" 
        for loc_file in possible_locations.iterdir():
            if self.__is_base_spawned_at(loc_file):
                blocked.append(loc_file.name)
            elif self.__are_structures_present(self.__get_main_location(loc_file), map=map):
                blocked.append(loc_file.name)

        return blocked
    
    def __get_random_location(self, map: ArkMap = ArkMap.ABERRATION) -> MapCoords:
        possible_locations = self.base_path / "locations" / "randomised" 
        loc_file =  random.choice(list(possible_locations.iterdir()))
        blocked = self.__get_blocked_locations(map)

        if len(blocked) == len(list(possible_locations.iterdir())):
            raise Exception("All locations have been used")
        
        if loc_file.name in blocked:
            return self.__get_random_location(map)
            
        return json.load(loc_file.open()), loc_file.name
    
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
    
    def compose_base(self):
        size = random.choice(list(self.config.keys()))
        cfg = self.config[size]
        loc_config, file = self.__get_random_location()
        config: dict = {
            "locations": loc_config,
            "size": size,
            "location": file,
            "total_turrets": 0,
        }
        turret_total = 0
        curr_tries = 0

        while cfg["min_turrets"] >= turret_total or cfg["max_turrets"] <= turret_total:
            size = random.choice(list(self.config.keys()))
            cfg = self.config[size]
            if curr_tries > 50:
                loc_config, file = self.__get_random_location()
                curr_tries = 0
            config = {
                "locations": loc_config,
                "size": size,
                "location": file,
                "total_turrets": 0,
            }
            curr_tries += 1
            turret_total = 0
            for loc in loc_config.keys():
                if config["locations"][loc]["type"] == "main":
                    selected_base = random.choice(cfg["main"])
                    config["locations"][loc]["selected_path"] = str(self.base_path / "base" / selected_base)
                elif config["locations"][loc]["type"] == "tower":
                    selected_base = random.choice(cfg["tower"])
                    config["locations"][loc]["selected_path"] = str(self.base_path / "turret_tower" / selected_base)
                config["locations"][loc]["selection"] = json.load(open(Path(config["locations"][loc]["selected_path"]) / "base.json", 'r'))
                turret_total += config["locations"][loc]["selection"]["nr_of_turrets"]

        config["total_turrets"] = turret_total

        return config
    
    def __add_loot(self, base: Base, loot_path: Path):
        def get_equipment_class(type: str):
            if type == "armor":
                return EquipmentApi.Classes.ARMOR, ArkEquipmentStat.ARMOR
            elif type == "weapon":
                return EquipmentApi.Classes.WEAPON, ArkEquipmentStat.DAMAGE
            elif type == "saddle":
                return EquipmentApi.Classes.SADDLE, ArkEquipmentStat.ARMOR
            else:
                raise ValueError(f"Invalid type: {type}")

        def get_vault(base: Base) -> StructureWithInventory:
            for _, structure in base.structures.items():
                if structure.object.blueprint == Classes.structures.placed.utility.vault:
                    return structure

        def add_random_gear_pieces(base: Base, loot: dict):
            nr_of_entries = len(loot)
            vault = get_vault(base)
            is_bp = True
            for _ in range(3):
                entry = loot[random.randint(0, nr_of_entries - 1)]
                cls, stat = get_equipment_class(entry["type"])
                item = self.e_api.generate_equipment(cls, entry["blueprint"], stat, entry["min_value"], entry["max_value"], force_bp=is_bp)
                self.save.add_to_db(item)
                vault.add_item(item.object.uuid, self.save)
                is_bp = random.choices([True, False], weights=[20, 80], k=1)[0]

        def add_resources(base: Base, loot: dict):
            vault = get_vault(base)
            for entry in loot:
                total = random.randint(entry["min_value"], entry["max_value"])
                while total > 0:
                    local = min(total, get_stack_size(entry["blueprint"]))
                    total -= local
                    item = Resource.generate_from_template(entry["blueprint"], self.save, vault.object.uuid)
                    item.set_quantity(local)
                    self.save.add_to_db(item)
                    vault.add_item(item.object.uuid, self.save)

        def get_stack_size(blueprint: str):
            with open(self.base_path / "loot" / "stack_sizes.json") as f:
                stack_sizes = json.load(f)
                return stack_sizes["sizes"][blueprint] * stack_sizes["multiplier"]
            
        loot = json.load(loot_path.open())
        initial_vault_items = get_vault(base).inventory.items.copy()
        add_random_gear_pieces(base, loot["gear"])
        add_resources(base, loot["resources"])
        for item in initial_vault_items:
            get_vault(base).remove_item(item)
    
    def __spawn_section(self, path: Path, loc: ActorTransform, owner: dict):
        self._print(f"[Spawn]Importing section from {path}")
        base: Base = self.b_api.import_base(path, location=loc)
        self._print(f"[Spawn]Section imported at {loc.as_map_coords(ArkMap.ABERRATION)}")
        base.pad_turret_ammo(25, self.save)
        self._print(f"[Spawn]Turret ammo padded")
        base.set_nr_of_element_in_generators(3, self.save)
        self._print(f"[Spawn]Element added to generators")
        o: ObjectOwner = ObjectOwner()
        o.set_tribe(1, owner["name"])
        o.set_player(1)
        base.set_owner(o, self.save)
        self._print(f"[Spawn]Owner set to {owner['name']}")
        return base
    
    def spawn_base(self, base_config: dict, map: ArkMap = ArkMap.ABERRATION):
        base_status = {
            "type": base_config["size"],
            "is_raided": False,
            "raid_broadcasted": False,
            "config": base_config,
            "owner": self.__get_random_owner()
        }
        base_config = base_config["locations"]
        for loc in base_config.keys():
            path = base_config[loc]["selected_path"]
            actor_transform = ActorTransform.from_json(base_config[loc]["location"])
            base: Base = self.__spawn_section(path, actor_transform, base_status["owner"])
            self._print(f"[Spawn]Spawned base section")

            if base_config[loc]["type"] == "main":
                base_status["location"] = str(actor_transform.as_map_coords(map))
                self._print(f"[Spawn]Adding loot to the base")
                self.__add_loot(base, self.base_path / "loot" / (base_status["type"] + ".json"))
        self._print(f"[Spawn]Base inserted, saving...")

        self.data_["active_bases"].append(base_status)
        self.__save_data(self.data_path)
        self._print(f"[Spawn]Import complete")

    def __pad_active_base_generators(self):
        for base in self.data_["active_bases"]:
            loc: str = base["location"]
            x, y = map(float, loc.strip("()").split(", "))
            coords = MapCoords(x, y)
            base: Base = self.b_api.get_base_at(coords, 2, owner_tribe_id=1)
            nr = base.set_nr_of_element_in_generators(3, self.save)
            self._print(f"[Spawn]Element added to {nr} generators at {coords}")


    def __check_raided(self):
        for base in self.data_["active_bases"]:
            file_path = self.base_path / "locations" / "randomised" / base["config"]["location"]
            if self.__is_base_raided(self.__get_main_location(file_path)) and not base["is_raided"]:
                base["is_raided"] = True
                self._print(f"[Raided]Base at {base['location']} is raided")
                self._print(f"[Raided]{base['owner']['raided']}")
                self.rcon.send_message(f"{base['owner']['raided']}")
        self.__save_data(self.data_path)

    def __remove_raided(self):
        data_copy = self.data_["active_bases"].copy()
        for base in self.data_["active_bases"]:
            if base["is_raided"]:
                loc: str = base["location"]
                x, y = map(float, loc.strip("()").split(", "))
                coords = MapCoords(x, y)
                self._print(f"[Raided]Removing base at {coords}")
                self.s_api.remove_at_location(ArkMap.ABERRATION, coords, 2, owner_tribe_id=1)
                data_copy.remove(base)
        self.data_["active_bases"] = data_copy
        self.__save_data(self.data_path)

    def __process(self, interval: int):
        self.main()

    def __get_save(self):
        self.ftp.connect()
        self.set_save(AsaSave(contents=self.ftp.download_save_file()))
        self.ftp.close()

    def __put_save(self):
        self.ftp.connect()
        self.save.store_db(self.base_path / "Aberration_WP.ark")
        self.ftp.upload_save_file(path=self.base_path / "Aberration_WP.ark")
        self.ftp.close()

    def main(self):

        if self.time_handler.is_half_hour():
            self._print(f"[Main]Checking for bases (hour={time.localtime().tm_hour})")
            self.__get_save()
            # check if any bases have been raided
            self.__check_raided()

            if time.localtime().tm_hour == 5:
                self._print(f"[Main]Spawning and updating bases")
                # remove raided bases
                self.__remove_raided()
                # spawn up to three bases
                for _ in range(3):
                    if len(self.data_["active_bases"]) >= 3:
                        break
                    cfg = self.compose_base()
                    self.spawn_base(cfg)
                # Pad generators
                self.__pad_active_base_generators()
                self.__put_save()
            # Report active bases
            for base in self.data_["active_bases"]:
                if not base["is_raided"]:
                    self._print(f"[Active]Base at {base['location']} is active")
                    self._print(f"[Active]{base['owner']['message']}{base['location']}")
                    self.rcon.send_message(f"{base['owner']['message']}{base['location']}")

    def test_full(self):
        self._print(f"[Main]Checking for bases")
        self.__get_save()

        # self.set_save(AsaSave(self.base_path / "Aberration_WP_pre.ark"))

        # check if any bases have been raided
        self.__check_raided()

        self._print(f"[Main]Spawning and updating bases")
        # remove raided bases
        self.__remove_raided()
        # spawn up to three bases
        for _ in range(3):
            if len(self.data_["active_bases"]) >= 3:
                break
            cfg = self.compose_base()
            self.spawn_base(cfg)
        # Pad generators
        self.__pad_active_base_generators()
        # self.save.store_db(Path.cwd() / "Aberration_WP.ark")
        self.__put_save()
        # Report active bases
        for base in self.data_["active_bases"]:
            if not base["is_raided"]:
                self._print(f"[Active]Base at {base['location']} is active")
                self._print(f"[Active]{base['owner']['message']}{base['location']}")
                self.rcon.send_message(f"{base['owner']['message']}{base['location']}")

    def test_hour(self):
        self._print(f"[Main]Checking for bases")
        self.__get_save()
        # check if any bases have been raided
        self.__check_raided()
        
        for base in self.data_["active_bases"]:
            if not base["is_raided"]:
                self._print(f"[Active]Base at {base['location']} is active")
                self._print(f"[Active]{base['owner']['message']}{base['location']}")
                self.rcon.send_message(f"{base['owner']['message']}{base['location']}")
    

    
# base = Path.cwd().parent / "bases"
# rcon = RconApi.from_config(Path.cwd().parent / "rcon_config.json")
# mngr = RaidBaseManager(rcon, "../ftp_config.json", base)

# mngr.test_hour()