from pathlib import Path
from uuid import UUID
from arkparse.parsing.struct.actor_transform import ActorTransform, MapCoords
from arkparse.parsing.struct import ArkVector
from arkparse.ftp.ark_ftp_client import ArkFtpClient, ArkMap
from arkparse.api.player_api import PlayerApi
from arkparse import MapCoords
from arkparse.api.base_api import BaseApi
from arkparse.enums import ArkMap
from arkparse.api import BaseApi
from arkparse.saves.asa_save import AsaSave
from arkparse.classes import *

spawn = ActorTransform(vector=ArkVector(x=282151, y=97434, z=-7596))

MAP = ArkMap.RAGNAROK
save_path = Path("D:\\SteamLibrary\\steamapps\\common\\ARK Survival Ascended\\ShooterGame\\Saved\\SavedArksLocal\\Ragnarok_WP\\Ragnarok_WP.ark")
base_path = Path.cwd() / "loothouse" 
save = AsaSave(save_path)

bApi = BaseApi(save, MAP)
location = spawn.as_map_coords(MAP)

base_path = Path.cwd() / "loothouse"
base = bApi.get_base_at(location, radius=0.1)

tek_floor = None
for key, structure in base.structures.items():
    if structure.object.blueprint == Classes.structures.placed.tek.floor:
        tek_floor = structure
        break
base.set_keystone(tek_floor.object.uuid)
base.store_binary(base_path)