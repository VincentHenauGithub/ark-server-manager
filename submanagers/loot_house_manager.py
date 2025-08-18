import json
import random
from pathlib import Path
import time

from arkparse import Classes
from arkparse.api.base_api import Base
from arkparse.api.rcon_api import RconApi
from arkparse.object_model.misc.object_owner import ObjectOwner
from arkparse.object_model.structures import StructureWithInventory
from arkparse.parsing.struct import MapCoords
from arkparse.parsing.struct.actor_transform import MapCoords

from submanagers.save_tracker import SaveTracker
from .__manager import Manager
from .locations import LocationController
from .time_handler import PreviousDate, TimeHandler
from .loot_configuration import add_loot

class LoothouseState:
    __STATUS_PATH = Path(__file__).parent.parent / "loothouse" / "loothouse.json"
    def __init__(self):
        with open(self.__STATUS_PATH, 'r') as file:
            self.state = json.load(file)

    @property
    def is_active(self) -> bool:
        return self.state.get("active", False)
    
    @property
    def coordinates(self) -> MapCoords:
        coords = self.state.get("coordinates", {"latitude": 0, "longitude": 0})
        return MapCoords(coords["latitude"], coords["longitude"])
    
    @property
    def is_removed(self) -> bool:
        return self.state.get("removed", False)
    
    def set_removed(self, removed: bool):
        self.state["removed"] = removed
        with open(self.__STATUS_PATH, 'w') as file:
            json.dump(self.state, file, indent=4)
    
    def set_active(self, active: bool):
        self.state["active"] = active
        with open(self.__STATUS_PATH, 'w') as file:
            json.dump(self.state, file, indent=4)

    def set_coordinates(self, coords: MapCoords):
        self.state["coordinates"] = {
            "latitude": coords.lat,
            "longitude": coords.long
        }
        with open(self.__STATUS_PATH, 'w') as file:
            json.dump(self.state, file, indent=4)

class LootHouseManager(Manager):
    __LOOTHOUSE_TRIBE_ID = 77
    __LOOTHOUSE_PLAYER_ID = 77
    __MIN_TURRETS = 0
    __MAX_TURRETS = 40
    __LOOTHOUSE_PATH = Path(__file__).parent.parent / "loothouse" / "loothouse"

    def __init__(self, save_tracker: SaveTracker, rconapi: RconApi):
        super().__init__(self.__process, "loot house manager", 2345)
        self.rcon : RconApi = rconapi
        self.save_tracker: SaveTracker = save_tracker
        self.time_handler: TimeHandler = TimeHandler()
        self.state = LoothouseState()
        self.last_timestamp: PreviousDate = None

        self.owner: ObjectOwner = ObjectOwner()
        self.owner.set_tribe(self.__LOOTHOUSE_TRIBE_ID, "The administration")
        self.owner.set_player(self.__LOOTHOUSE_PLAYER_ID)

    def _spawn(self):
        self._print("Loothouse is not active, setting up...")
        _, location, coords = LocationController.get_random_unblocked_location(self.save_tracker.base_api, radius=1, map=self.save_tracker.map)
        base: Base = self.save_tracker.base_api.import_base(self.__LOOTHOUSE_PATH, LocationController.get_loc_actor_transform(location))

        vault: StructureWithInventory = None
        for _, structure in base.structures.items():
            if structure.object.blueprint == Classes.structures.placed.utility.vault:
                vault = structure
                break
        initial_vault_items = vault.inventory.items.copy()

        amount = random.randint(self.__MIN_TURRETS, self.__MAX_TURRETS)
        mixed = False
        if amount > 50:
            mixed = random.choice([True, False])

        for structure in base.structures.values():
            is_sign = structure.object.blueprint == Classes.structures.placed.metal.wall_sign
            structure.set_max_health(amount * (10000 if not is_sign else 500))
            structure.heal()
        
        base.set_owner(self.owner)

        add_loot(None, amount, self.save_tracker.save, vault, self.save_tracker.equipment_api, mixed)

        for item in initial_vault_items:
            vault.remove_item(item)

        self.state.set_active(True)
        self.state.set_coordinates(coords)
        LocationController.add_active_location(location)
        self._print(f"Loothouse is set up at {coords}")

        self.save_tracker.put_save()

    def _refresh_active(self) -> bool:
        if self.state.is_active:
            b_api = self.save_tracker.base_api
            base: Base = b_api.get_base_at(self.state.coordinates, radius=0.1, owner_tribe_id=self.__LOOTHOUSE_TRIBE_ID)
            
            vault: StructureWithInventory = None
            if base is not None:
                for _, structure in base.structures.items():
                    if structure.object.blueprint == Classes.structures.placed.utility.vault:
                        vault = structure
                        break
            if vault is None or vault.inventory is None or len(vault.inventory.items) == 0:
                self._print("Loothouse is gone or empty, refreshing state...")
                self.state.set_active(False)
            else:
                self._print(f"Loothouse is still active at {self.state.coordinates}")
        else:
            self._print("Loothouse is not active... No refresh needed.")

    def _update_insertion(self):
        if not self.state.is_active and not self.state.is_removed:
            self._print("Removing remains of raided loothouse...")
            self.save_tracker.base_api.remove_at_location(self.save_tracker.map, self.state.coordinates, radius=0.1, owner_tribe_id=self.__LOOTHOUSE_TRIBE_ID)
            self.state.set_removed(True)
        
        if not self.state.is_active:
            self._spawn()

    def _report_status(self):
        active_players = len(self.rcon.get_active_players())
        if active_players > 3:
            message = f"There are {active_players} players online. Checking loothouse at {self.state.coordinates}..."
            self._print(message)
            self.rcon.send_message(message)
        else:
            self._print(f"Not enough players online ({active_players}), no need to check the loothouse.")

    def __process(self, interval: int):
        self._refresh_active()

        if time.localtime().tm_hour == 5 and (self.last_timestamp is None or self.last_timestamp.has_been_hour()):
            self.last_timestamp = PreviousDate()
            self._print("It's 5 AM, updating loothouse in save...")
            self._update_insertion()

        self._report_status()


