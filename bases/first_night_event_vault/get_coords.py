import json
from pathlib import Path
from uuid import UUID
from arkparse.parsing.struct.actor_transform import ActorTransform, MapCoords
from arkparse.parsing.struct import ArkVector
from arkparse.ftp.ark_ftp_client import ArkFtpClient, ArkMap
from arkparse.api.player_api import PlayerApi
from arkparse import MapCoords
from arkparse.api.base_api import BaseApi, StructureApi
from arkparse.enums import ArkMap
from arkparse.api import BaseApi
from arkparse.saves.asa_save import AsaSave
from arkparse.classes import *

spawn = ActorTransform(vector=ArkVector(x=331203, y=112653, z=-10265))

MAP = ArkMap.RAGNAROK
save_path = Path("D:\\SteamLibrary\\steamapps\\common\\ARK Survival Ascended\\ShooterGame\\Saved\\SavedArksLocal\\Ragnarok_WP\\Ragnarok_WP.ark") 
save = AsaSave(save_path)

locations = []

id = 1

s_api = StructureApi(save)
stage_1 = s_api.get_by_class([Classes.structures.placed.adobe.quarter_foundation])
print(f"Found {len(stage_1)} adobe quarter foundations in stage 1.")
for key, structure in stage_1.items():
    print(structure.location)
    state = {
        "stage": 1,
        "id": id,
        "revealed": False,
        "pincode": "1234",
        "location": structure.location.as_json(),
    }
    locations.append(state)
    id += 1

stage_2 = s_api.get_by_class([Classes.structures.placed.adobe.tri_floor])
print(f"Found {len(stage_2)} adobe tri floors in stage 2.")
for key, structure in stage_2.items():
    print(structure.location)
    state = {
        "stage": 2,
        "id": id,
        "revealed": False,
        "pincode": "1234",
        "location": structure.location.as_json(),
    }
    locations.append(state)
    id += 1

with open("intro_loot.json", 'w') as file:
    json.dump(locations, file, indent=4)    
