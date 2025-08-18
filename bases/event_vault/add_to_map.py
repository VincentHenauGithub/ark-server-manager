from arkparse.parsing.struct.actor_transform import ActorTransform, MapCoords
from arkparse.parsing.struct import ArkVector
from pathlib import Path
from arkparse.enums import ArkMap
from arkparse import AsaSave
from arkparse.api.base_api import BaseApi, Base
from arkparse.api import EquipmentApi, PlayerApi
from arkparse.object_model.misc.object_owner import ObjectOwner
from arkparse.object_model.structures import StructureWithInventory, Structure
import random
from arkparse import Classes
from loot_configuration import add_loot
import json
from typing import Dict, Union
from uuid import UUID


class LoothouseState:
    __STATUS_PATH = Path.cwd() / "loothouse.json"
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

spawn = ActorTransform(vector=ArkVector(x=282151, y=97434, z=-7596))

LOOTHOUSE_TRIBE_ID = 77
LOOTHOUSE_PLAYER_ID = 77

MAP = ArkMap.RAGNAROK
store_path = Path("D:\\SteamLibrary\\steamapps\\common\\ARK Survival Ascended\\ShooterGame\\Saved\\SavedArksLocal\\Ragnarok_WP\\Ragnarok_WP.ark")
save_path = Path("D:\\SteamLibrary\\steamapps\\common\\ARK Survival Ascended\\ShooterGame\\Saved\\SavedArksLocal\\Ragnarok_WP\\_Ragnarok_WP.ark")
state = LoothouseState()
base_path = Path.cwd() / "loothouse" 
save = AsaSave(save_path)

b_api = BaseApi(save, MAP)
eq_api = EquipmentApi(save)
p_api = PlayerApi(save)

o: ObjectOwner = ObjectOwner()
o.set_tribe(p_api.generate_tribe_id(), "The administration")
o.set_player(p_api.generate_player_id())
print(f"Using tribe ID {o.tribe_id} and player ID {o.id_} for loothouse operations.")

def report(active_players: int):
    if active_players > 3:
        print(f"There is a suspicious hut at {state.coordinates}. Might wanna go check it out..")
    else:
        print(f"Not enough players online ({active_players}), no need to check the loothouse.")

if not state.is_active:
    print("Loothouse is not active, setting up...")
    base: Base = b_api.import_base(base_path, spawn)

    vault: StructureWithInventory = None
    for key, structure in base.structures.items():
        if structure.object.blueprint == Classes.structures.placed.utility.vault:
            vault = structure
            break
    initial_vault_items = vault.inventory.items.copy()

    amount = random.randint(0, 100)
    mixed = False
    if amount > 50:
        mixed = random.choice([True, False])

    for structure in base.structures.values():
        is_sign = structure.object.blueprint == Classes.structures.placed.metal.wall_sign
        structure.set_max_health(amount * (10000 if not is_sign else 500))
        structure.heal()

    # p_api = PlayerApi(save)
    # player = p_api.players[0]
    
    base.set_owner(o)

    add_loot(None, amount, save, vault, eq_api, mixed)

    for item in initial_vault_items:
        vault.remove_item(item)

    save.store_db(store_path)

    state.set_active(True)
    state.set_coordinates(spawn.as_map_coords(MAP))
else:
    print("Loothouse is already active, checking status...")
    structures: Dict[UUID, Union[Structure, StructureWithInventory]] = b_api.get_at_location(MAP, state.coordinates, radius=0.1)
    b_api.filter_by_owner(structures, o)

    vault = None
    for _, structure in structures.items():
        if structure.object.blueprint == Classes.structures.placed.utility.vault:
            vault = structure
            break
    if vault is None or vault.inventory is None or len(vault.inventory.items) == 0:
        print("Loothouse is gone or empty, cleaning up...")
        b_api.remove_at_location(MAP, state.coordinates, radius=0.1, owner_tribe_id=LOOTHOUSE_TRIBE_ID)
        state.set_active(False)
    else:
        print(f"Loothouse is still active at {state.coordinates}, checking player count...")
    
if state.is_active:
    report(77)