import random
from arkparse.parsing.struct.actor_transform import ActorTransform, MapCoords
from arkparse.enums import ArkMap
from arkparse.api import StructureApi
from pathlib import Path

import json
from typing import List
from uuid import UUID, uuid4

class MenagerieMemberState:
    _MENAGERIE_MEMBER_STATE = {
        "location": None,
        "difficulty": 0,
        "mixed": False,
        "mapcoords": None,
        "tribe_id": None,
        "blueprint": None,
        "line": None
    }

    _PATH = Path(__file__).parent / "menagerie_state.json"
    
    def __init__(self, uuid: UUID):
        self.uuid = uuid
        self.state = None
        self._load_state()

    def remove(self):
        with open(self._PATH, 'r') as file:
            data = json.load(file)

        if str(self.uuid) in data:
            del data[str(self.uuid)]
            with open(self._PATH, 'w') as file:
                json.dump(data, file, indent=4)

    def _load_state(self) -> dict:
        if self._PATH.exists():
            with open(self._PATH, 'r') as file:
                data = json.load(file)
        
        if str(self.uuid) in data:
            self.state =  data[str(self.uuid)]
        else:
            self.state = self._MENAGERIE_MEMBER_STATE.copy()
            self._update()

        print(f"Loaded state for {self.uuid}: {self.state}")
            
    def _update(self):
        data = None
        with open(self._PATH, 'r') as file:
            data = json.load(file)

        with open(self._PATH, 'w') as file:
            data[str(self.uuid)] = self.state
            json.dump(data, file, indent=4)

    @property
    def mapcoords(self) -> MapCoords:
        return MapCoords(self.state["mapcoords"]["lat"],
                         self.state["mapcoords"]["lon"])

    @mapcoords.setter
    def mapcoords(self, value: MapCoords):
        self.state["mapcoords"] = {"lat": value.lat, "lon": value.long}
        self._update()

    @property
    def difficulty(self) -> int:
        return self.state["difficulty"]
    
    @difficulty.setter
    def difficulty(self, value: int):
        self.state["difficulty"] = value
        self._update()

    @property
    def mixed(self) -> bool:
        return self.state["mixed"]
    
    @mixed.setter
    def mixed(self, value: bool):
        self.state["mixed"] = value
        self._update()

    @property
    def tribe_id(self) -> int:
        return self.state["tribe_id"]
    
    @tribe_id.setter
    def tribe_id(self, value: int):
        self.state["tribe_id"] = value
        self._update()

    @property
    def blueprint(self) -> str:
        return self.state["blueprint"]
    
    @blueprint.setter
    def blueprint(self, value: str):
        self.state["blueprint"] = value
        self._update()

    @property
    def location(self) -> ActorTransform:
        return ActorTransform.from_json(self.state["location"])
    
    @location.setter
    def location(self, value: ActorTransform):
        self.state["location"] = value.as_json()
        self._update()

    @property
    def line(self) -> str:
        return self.state["line"]
    
    @line.setter
    def line(self, value: str):
        self.state["line"] = value
        self._update()

class MenagerieState:
    _PATH = Path(__file__).parent / "menagerie_state.json"
    def __init__(self):
        self.members: List[MenagerieMemberState] = []
        self._load_state()

    def _load_state(self):
        if not self._PATH.exists():
            with open(self._PATH, 'w') as file:
                json.dump({}, file, indent=4)

        with open(self._PATH, 'r') as file:
            data: dict = json.load(file)
            for uuid_str in data.keys():
                uuid = UUID(uuid_str)
                self.members.append(MenagerieMemberState(uuid))

    def add_member(self) -> MenagerieMemberState:
        member = MenagerieMemberState(uuid4())
        self.members.append(member)
        return member
    
    def remove_member(self, member: MenagerieMemberState):
        member.remove()
        self.members.remove(member)
    
    @property
    def used_locations(self) -> List[ActorTransform]:
        return [member.location for member in self.members if member.location is not None]
    
    @property
    def number_active(self) -> int:
        return len(self.members)
    
    def get_unused_name(self) -> str:
        names = [
            "Ixlix, the All-Devouring",
            "Morgrath, the Bone-Breaker",
            "Velthar, the Soul-Scourge",
            "Chyrix, the Hollow Maw",
            "Drosvek, the Blood-Drowned",
            "Thalyth, the Whispering Hunger",
            "Korvash, the World-Withered",
            "Uthrix, the Shadow Unending",
            "Zerakor, the Flesh-Unmaker",
            "Nyrrith, the Endless Woe",
            "Skorval, the Death-Tide",
            "Veylith, the Skin-Thief",
            "Krathok, the Night-Harvester",
            "Phorxis, the Carrion Crown",
            "Ulmorr, the Womb of Rot",
            "Ixthar, the Ashen Maw",
            "Ghorrith, the Grief-Eater",
            "Wyrloch, the Pale Calamity",
            "Orravex, the Thousand Eyes",
            "Charnyx, the Grave-Singer"
        ]
        used = [member.line for member in self.members if member.line is not None]
        names = [name for name in names if name not in used]

        if not names:
            raise ValueError("No unused names available")

        return random.choice(names)

    def get_unused_line(self) -> str:
        lines = [
            "Whispers of cursed shapes drift from",
            "Rumours of blood-chilling screams spread from",
            "They say the shadows move on their own near",
            "Old wives speak of an unquiet stirring at",
            "Hushed tales of vanishing travellers come from",
            "The survivors dare not tread close to",
            "Legends claim a foul hunger awakens at",
            "Rumours of claw marks and broken ground swirl around",
            "The brave speak of dreadful chanting from",
            "It is said the night itself recoils at",
            "They whisper of bones unearthed at",
            "It is said that no torches burn long at",
            "Travellers speak of dreadful shapes lurking at",
            "The air is thick with fearful talk of",
            "Shuddered warnings drift from those who passed by",
            "The survivors speak only in hushed tones of",
            "All who return bring tales of horror from"
        ]

        used = [member.line for member in self.members if member.line is not None]
        lines = [line for line in lines if line not in used]

        if not lines:
            raise ValueError("No unused lines available")

        return random.choice(lines)
    
class LocationController:
    _LAND_PATH = Path(__file__).parent / "land_dino_spawns.json"
    _WATER_PATH = Path(__file__).parent / "water_dino_spawns.json"

    @staticmethod
    def get_random_free_location(loc_type: str, structure_api: StructureApi, dont_use: List[ActorTransform] = [], map: ArkMap = ArkMap.RAGNAROK) -> ActorTransform:
        if loc_type == "both":
            loc_type = random.choice(["land", "water"])
        
        if loc_type == "land":
            with open(LocationController._LAND_PATH, 'r') as file:
                locations = json.load(file)
        elif loc_type == "water":
            with open(LocationController._WATER_PATH, 'r') as file:
                locations = json.load(file)
        else:
            raise ValueError(f"Unknown location type: {loc_type}")

        actor_transforms = [ActorTransform.from_json(loc) for loc in locations]

        filtered = []
        for loc in actor_transforms:
            no_use = False
            too_many_structures = False
            for dont in dont_use:
                if loc.get_distance_to(dont) < 100:
                    no_use = True

            structures_at_loc = structure_api.get_at_location(map, loc.as_map_coords(map), radius=2)

            if len(structures_at_loc) > 15:
                too_many_structures = True

            if not no_use and not too_many_structures:
                filtered.append(loc)

        if len(filtered) == 0:
            raise ValueError("No valid locations found")
        
        return random.choice(filtered)
