from pathlib import Path
from typing import Dict, List
from arkparse import AsaSave
from arkparse.enums import ArkMap
from arkparse.api.player_api import PlayerApi
from arkparse.api.base_api import BaseApi, Base
from arkparse.object_model.misc.object_owner import ObjectOwner
from arkparse.parsing.struct.actor_transform import MapCoords, ActorTransform, MapCoordinateParameters

store_path = Path("D:\\SteamLibrary\\steamapps\\common\\ARK Survival Ascended\\ShooterGame\\Saved\\SavedArksLocal\\Ragnarok_WP\\Ragnarok_WP.ark")
save_path = Path("D:\\SteamLibrary\\steamapps\\common\\ARK Survival Ascended\\ShooterGame\\Saved\\SavedArksLocal\\Ragnarok_WP\\_Ragnarok_WP.ark")
save = AsaSave(save_path)

def __get_available() -> list:
        base_folder_path = Path.cwd()
        available_bases = []
        for base_file in base_folder_path.iterdir():
            prefix = base_file.name.split("_")[0]
            if prefix in ["mixed", "large", "medium"]:
                available_bases.append(base_file)
        return available_bases

starting_coords = MapCoords(55.3, 78.0)
available = __get_available()
api = BaseApi(save, ArkMap.RAGNAROK)
bases = [
    # {
    #     "x": 50.4, 
    #     "y": 33.9,
    #     "name": ["base", "small"],
    #     "radius": 0.2
    # }
]
z=-11000

x = [99433, 263943, 137942.5]
y= [373505, 334913, -91229]
lat =[78.51, 75.57, 43.04]
long = [57.59, 70.15, 60.53]

print(MapCoordinateParameters.fit_transform_params(x, y, lat, long))

me = PlayerApi(save).players[0]

current_location = starting_coords
for base in available:
    print(f"Importing base {base.name} at {current_location}")
    at = current_location.as_actor_transform(ArkMap.RAGNAROK)
    print(at)
    b: Base = api.import_base(base, at)
    b.set_fuel_in_generators(api.save, 50, 50)
    b.set_turret_ammo(api.save, 100, 100, 100)
    b.set_owner(ObjectOwner.from_profile(me, PlayerApi(save).get_tribe_of(me)))
    bases.append(
        {
            "x": current_location.lat,
            "y": current_location.long,
            "name": base.name,
            "radius": 0.2
        }
    )
    current_location.long += 0.5

print(bases)
save.store_db(store_path)
print(f"Stored bases in {store_path}")