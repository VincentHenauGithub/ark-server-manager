from arkparse.ftp.ark_ftp_client import ArkFile, ArkMap
from pathlib import Path
from typing import Dict
import json
from uuid import UUID
import os

from arkparse.api.rcon_api import RconApi
from arkparse.api.structure_api import StructureApi
from arkparse.api import PlayerApi
from arkparse.object_model.structures import Structure
from arkparse.classes.placed_structures import PlacedStructures

from .__manager import Manager
from .save_tracker import SaveTracker

class MainBaseReporter(Manager):
    def __init__(self, save_tracker: SaveTracker, rconapi: RconApi):
        super().__init__(self.__process, "main base reporter", 3521)
        self.rcon: RconApi = rconapi
        self.save_tracker: SaveTracker = save_tracker

    def __process(self, interval: int):
        signs, water_signs = self.__get_all_signs()
        tribe_map = self.__player_to_tribe_map()
        bases = ""
        water_pens = ""
        for player in tribe_map:
            tribe_id = tribe_map[player]
            if tribe_id in signs:
                sign_text, coords = signs[tribe_id]
                if sign_text == "DIRTY":
                    self.rcon.send_message(f"{player} seems to have multiple main bases, which means you can go blow them up :)")
                else:
                    bases += f"{player}{coords.str_short()}; "
            else:
                bases +=  f"{player}(no base); "
            
            if tribe_id in water_signs:
                sign_text, coords = water_signs[tribe_id]
                if sign_text == "DIRTY":
                    self.rcon.send_message(f"{player} seems to have multiple water breeding pens, which means you can go blow them up :)")
                else:
                    water_pens += f"{player}{coords.str_short()}; "

        if bases:
            self.rcon.send_message(f"======= Main Bases =======")
            self.rcon.send_message(bases)

        if water_pens:
            self.rcon.send_message(f"======= Water Pens =======")
            self.rcon.send_message(water_pens)

    def __player_to_tribe_map(self):
        player_to_tribe: Dict[str, int] = {}
        players: Dict[str, dict] = {}
        cur_file_dir = os.path.dirname(__file__)
        with open(Path(cur_file_dir).parent / "players.json", "r") as f:
            players = json.load(f)

        for player in players.values():
            tribe_id = player.get("tribe")
            player_name = player.get("real_name")
            platform_name = player.get("steam_name")
            p_api: PlayerApi = self.save_tracker.get_api(PlayerApi)
            player = p_api.get_player_by_platform_name(platform_name)
            if player is None:
                self._print(f"Player {player_name} not found, skipping")
                continue
            player_to_tribe[player_name] = player.tribe if player.tribe else player.id_

        return player_to_tribe

    def __get_all_signs(self):
        # ArkSaveLogger.enable_debug = True
        signs = {}
        water_signs = {}
        api: StructureApi = self.save_tracker.get_api(StructureApi)
        sign_objects: Dict[UUID, Structure] = api.get_by_class([PlacedStructures.wood.sign, PlacedStructures.metal.sign, PlacedStructures.metal.wall_sign, PlacedStructures.wood.wall_sign])

        for sign in sign_objects.values():
            text: str = sign.object.get_property_value('SignText', 'NO_TEXT')
            if text.lower() == "main base" or text.lower() == "mainbase":
                if sign.owner.tribe_id in signs:
                    signs[sign.owner.tribe_id] = "DIRTY", None
                    self._print(f"Multiple main bases for tribe {sign.owner.tribe_id}, removing from report")
                else:
                    signs[sign.owner.tribe_id] = text, sign.location.as_map_coords(self.save_tracker.map)
                    self._print(f"Found main base sign for tribe {sign.owner.tribe_id} at {sign.location.as_map_coords(self.save_tracker.map)} with text: {text}")

            if text.lower() == "water pen" or text.lower() == "waterpen":
                if sign.owner.tribe_id in water_signs:
                    water_signs[sign.owner.tribe_id] = "DIRTY", None
                    self._print(f"Multiple water pens for tribe {sign.owner.tribe_id}, removing from report")
                else:
                    water_signs[sign.owner.tribe_id] = text, sign.location.as_map_coords(self.save_tracker.map)
                    self._print(f"Found water pen for tribe {sign.owner.tribe_id} at {sign.location.as_map_coords(self.save_tracker.map)} with text: {text}")

        return signs, water_signs


