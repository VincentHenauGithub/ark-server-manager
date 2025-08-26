from arkparse.api.rcon_api import RconApi
from arkparse.object_model.dinos import TamedDino
from .__manager import Manager
from .time_handler import TimeHandler
from .save_tracker import SaveTracker

class PlatformDinoExposer(Manager):
    ALLOWED_UUIDS = [
        "98b65ea0-4b7f-7249-8b76-082277b260c1"
    ]
    def __init__(self, rconapi: RconApi, save_tracker: SaveTracker):
        super().__init__(self._process, "platform dino exposer", 900)
        self.rcon: RconApi = rconapi

        self.save_tracker: SaveTracker = save_tracker
        self.time_handler: TimeHandler = TimeHandler()

    def _process(self, _):
        tamed = self.save_tracker.dino_api.get_all_tamed()

        for dino in tamed.values():
            dino: TamedDino
            if len(dino.object.get_property_value("SaddleStructures", [])) > 10:
                if str(dino.uuid) not in self.ALLOWED_UUIDS:
                    self._print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    self._print(f"Found platform dino with more than 10 saddle structures, found {len(dino.object.get_property_value("SaddleStructures", []))} saddle structures")
                    self._print(f"Dino: {dino.get_short_name()}")
                    self._print(f"Owner: {dino.owner}")
                    self._print(f"UUID: {dino.uuid}")
                    self._print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                else:
                    self._print("Allowed platform dino found:")
                    self._print(f"Dino: {dino.get_short_name()} with {len(dino.object.get_property_value('SaddleStructures', []))} saddle structures")
                    self._print(f"Owner: {dino.owner}")
                    self._print(f"UUID: {dino.uuid}")
            elif len(dino.object.get_property_value("SaddleStructures", [])) > 0:
                self._print(f"Dino: {dino.get_short_name()} with {len(dino.object.get_property_value('SaddleStructures', []))} saddle structures")
                self._print(f"Owner: {dino.owner}")
                self._print(f"UUID: {dino.uuid}")
                
