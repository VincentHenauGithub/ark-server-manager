import json
import random
from pathlib import Path
import time

from arkparse import Classes
from arkparse.api.base_api import Base
from arkparse.api import PlayerApi
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

    def tribe_id(self, player_api: PlayerApi) -> int:
        id_ = self.state.get("tribe_id", None)
        if id_ is None:
            id_ = player_api.generate_tribe_id()
            self.state["tribe_id"] = id_
            with open(self.__STATUS_PATH, 'w') as file:
                json.dump(self.state, file, indent=4)
        return id_

    def player_id(self, player_api: PlayerApi) -> int:
        id_ = self.state.get("player_id", None)
        if id_ is None:
            id_ = player_api.generate_player_id()
            self.state["player_id"] = id_
            with open(self.__STATUS_PATH, 'w') as file:
                json.dump(self.state, file, indent=4)
        return id_

class LootHouseManager(Manager):
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

        p_api = self.save_tracker.player_api
        self.tribe_id = self.state.tribe_id(p_api)
        self.player_id = self.state.player_id(p_api)
        self.owner.set_tribe(self.tribe_id, "The administration")
        self.owner.set_player(self.player_id)

    def _spawn(self):
        self._print("Loothouse is not active, setting up...")
        self.save_tracker.stop_and_update()
        
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

        self.state.set_active(True)
        self.state.set_coordinates(coords)
        self.state.set_removed(False)
        LocationController.add_active_location(location)
        self._print(f"Loothouse is set up at {coords}")

    def _refresh_active(self) -> bool:
        if self.state.is_active:
            b_api = self.save_tracker.base_api
            base: Base = b_api.get_base_at(self.state.coordinates, radius=0.1, owner_tribe_name="The administration")

            vault: StructureWithInventory = None
            if base is not None and base.structures is not None and len(base.structures) > 0:
                for _, structure in base.structures.items():
                    if structure.object.blueprint == Classes.structures.placed.utility.vault:
                        vault = structure
                        break
            if vault is None or vault.inventory is None or len(vault.inventory.items) == 0:
                self._print("Loothouse is gone or empty, refreshing state...")
                self.state.set_active(False)
            else:
                self._print(f"Loothouse is still active at {self.state.coordinates}")
                self._report_status()
        else:
            self._print("Loothouse is not active... No refresh needed.")

    def _update_insertion(self):
        update = False
        if not self.state.is_active and not self.state.is_removed:
            self._print("Removing remains of raided loothouse...")
            self.save_tracker.base_api.remove_at_location(self.save_tracker.map, self.state.coordinates, radius=0.1, owner_tribe_name="The administration")
            self.state.set_removed(True)
            update = True

        if not self.time_handler._get_current_day() == "Saturday":
            self._print("It's not Saturday, no update needed.")
        elif not self.state.is_active:
            self._spawn()
            update = True

        if update:
            self.save_tracker.put_save()

    def _report_status(self):
        active_players = len(self.rcon.get_active_players())
        if active_players >= 3:
            message = f"There is definitely not a vault full of loot at {self.state.coordinates}, no need to go there"
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

        if not time.localtime().tm_hour == 5:
            self._print("It's not 5 AM, no update needed.")
