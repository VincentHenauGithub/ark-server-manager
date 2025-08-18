from arkparse.parsing.struct.actor_transform import ActorTransform
from pathlib import Path
from arkparse.enums import ArkMap
from arkparse import AsaSave
from arkparse.api.base_api import BaseApi, Base
from arkparse.api import EquipmentApi, PlayerApi
from arkparse.object_model.misc.object_owner import ObjectOwner
from arkparse.object_model.structures import StructureWithInventory
from arkparse.ftp.ark_ftp_client import ArkFtpClient
import random
from arkparse import Classes
from loot_configuration import add_loot
import json
from typing import Dict, Union
from uuid import UUID


class IntroLootState:
    __STATUS_PATH = Path.cwd() / "intro_loot.json"
    def __init__(self):
        with open(self.__STATUS_PATH, 'r') as file:
            self.state = json.load(file)

    def set_pincode(self, id: int, pincode: int):
        for loc in self.state:
            if loc["id"] == id:
                loc["pincode"] = pincode
                break
        with open(self.__STATUS_PATH, 'w') as file:
            json.dump(self.state, file, indent=4)

    def get_random_unrevealed(self, stage: int = None) -> Union[Dict, None]:
        unrevealed = [loc for loc in self.state if not loc["revealed"]]
        if stage is not None:
            unrevealed = [loc for loc in unrevealed if loc["stage"] == stage]
        if unrevealed:
            return random.choice(unrevealed)
        return None
    
    def set_revealed(self, id: int, state: bool = True):
        for loc in self.state:
            if loc["id"] == id:
                loc["revealed"] = state
                break
        with open(self.__STATUS_PATH, 'w') as file:
            json.dump(self.state, file, indent=4)

    
MAP = ArkMap.RAGNAROK
FTP_CLIENT = ArkFtpClient.from_config("../../ftp_config.json", MAP)
save_content = FTP_CLIENT.download_save_file(map=MAP)  # download the save file
# save_path  = Path.cwd() / "Ragnarok_WP.ark"
save = AsaSave(contents=save_content)   # load the save file
state = IntroLootState()
base_path = Path.cwd() / "fn_loothouse"

b_api = BaseApi(save, MAP)
eq_api = EquipmentApi(save)
p_api = PlayerApi(save)

o: ObjectOwner = ObjectOwner()
o.set_tribe(p_api.generate_tribe_id(), "The administration")
o.set_player(p_api.generate_player_id())

print("Loothouse is not active, setting up...")
for loc in state.state:
    spawn = ActorTransform.from_json(loc["location"])
    pincode = random.randint(1000, 9999)
    state.set_pincode(loc["id"], pincode)
    state.set_revealed(loc["id"], False)

    base: Base = b_api.import_base(base_path, spawn)

    vault: StructureWithInventory = None
    for key, structure in base.structures.items():
        if structure.object.blueprint == Classes.structures.placed.utility.small_storage_box:
            vault = structure
            break
    initial_vault_items = vault.inventory.items.copy()

    for structure in base.structures.values():
        structure.set_max_health(999999999)
        structure.heal()

    for structure in base.structures.values():
        if structure.object.blueprint == Classes.structures.placed.stone.door:
            structure.set_pincode(pincode)

    # p_api = PlayerApi(save)
    # player = p_api.players[0]

    base.set_owner(o)

    add_loot(None, 1, save, vault, eq_api, False)

    for item in initial_vault_items:
        vault.remove_item(item)

save.store_db(Path.cwd() / "_Ragnarok_WP.ark")
FTP_CLIENT.remove_save_file(MAP)
FTP_CLIENT.upload_save_file(Path.cwd() / "_Ragnarok_WP.ark", map=MAP)
