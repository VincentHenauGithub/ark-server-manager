import json
import random
from pathlib import Path
import time

from typing import Dict, Union

from arkparse.api import RconApi
from arkparse.enums import ArkMap
from arkparse.parsing.struct.actor_transform import ActorTransform, MapCoords

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
    
    def set_revealed(self, id: int):
        for loc in self.state:
            if loc["id"] == id:
                loc["revealed"] = True
                break
        with open(self.__STATUS_PATH, 'w') as file:
            json.dump(self.state, file, indent=4)
    
state = IntroLootState()
MAP = ArkMap.RAGNAROK

time.sleep(60*30)
while True:
    rcon: RconApi = RconApi.from_config("../../rcon_config.json")

    s1 = state.get_random_unrevealed(stage=1)
    if s1:
        print(f"Revealing stage 1 location")
        pincode = s1["pincode"]
        mapcoords = ActorTransform.from_json(s1["location"]).as_map_coords(MAP)
        print(f"THE ADMINISTRATION PROVIDES! The hut at {mapcoords} will be revealed in 5 minutes")
        rcon.send_message(f"THE ADMINISTRATION PROVIDES! The pincode of the hut at {mapcoords} will be revealed in 5 minutes")
        time.sleep(5*60)
        print(f"Revealing pincode: {pincode}")
        rcon.send_message(f"Pincode is: {pincode}")
        state.set_revealed(s1["id"])
    else:
        print("No unrevealed stage 1 locations found, revealing stage 2 instead.")
        s2 = state.get_random_unrevealed(stage=2)
        if s2: 
            pincode = s2["pincode"]
            mapcoords = ActorTransform.from_json(s2["location"]).as_map_coords(MAP)
            print(f"sending leading message for stage 2")
            rcon.send_message(f"THE ADMINISTRATION PROVIDES! The pincode of the hut at {mapcoords} will be revealed in 5 minutes")
            time.sleep(5*60)
            print(f"Revealing stage 2 location")
            rcon.send_message(f"Pincode is: {pincode}")

            state.set_revealed(s2["id"])
        else:
            print("No unrevealed locations found, stopping the script.")
            break
    time.sleep(60*15)
