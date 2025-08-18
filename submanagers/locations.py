from pathlib import Path
import json
import random
from typing import List

from arkparse.api import BaseApi
from arkparse.enums import ArkMap
from arkparse.parsing.struct import ArkVector
from arkparse.parsing.struct.actor_transform import MapCoords, ActorTransform

class LocationController:
    _active_location_path: str = Path("D:\\ARK servers\\Ascended\\scripts\\bases\\active_locations.json")
    _locations_folder: str = Path("D:\\ARK servers\\Ascended\\scripts\\bases\\locations\\ragnarok")

    @staticmethod
    def get_active_locations() -> list:
        """
        Returns a list of active locations from the JSON file.
        """
        try:
            with open(LocationController._active_location_path, 'r') as file:
                locations = json.load(file)
            return locations
        except FileNotFoundError:
            print(f"File not found: {LocationController._active_location_path}")
            return []
        except json.JSONDecodeError:
            print("Error decoding JSON from the file.")
            return []
        
    @staticmethod
    def get_available_locations(exclude: List[str]) -> list:
        all = LocationController.get_all_locations()
        active = LocationController.get_active_locations()
        return [loc for loc in all if loc not in active and loc not in exclude]

    @staticmethod
    def get_random_available_location(exclude: List[str]) -> str:
        """
        Returns a random location from the available locations.
        """
        available_locations = LocationController.get_available_locations(exclude)
        if len(available_locations) == 0:
            print("No available locations.")
            return None
        return random.choice(available_locations)

    @staticmethod
    def get_loc_coordinates(location: str, map: ArkMap) -> MapCoords:
        """
        Returns the coordinates of a given location from the JSON file.
        """
        at = LocationController.get_loc_actor_transform(location)
        if at is None:
            return None
        return at.as_map_coords(map)
        
    @staticmethod
    def get_loc_actor_transform(location: str) -> ActorTransform:
        """
        Returns the ActorTransform of a given location from the JSON file.
        """
        try:
            with open(Path(LocationController._locations_folder) / f"{location}", 'r') as file:
                data: dict = json.load(file)
                uuid = list(data.keys())[0]
                at = ActorTransform.from_json(data[uuid]['location'])
                return at
        except FileNotFoundError:
            print(f"Location file not found: {location}")
            return None
        except json.JSONDecodeError:
            print(f"Error decoding JSON for location: {location}")
            return None

        
    @staticmethod
    def get_all_locations() -> list:
        """
        Returns a list of all locations from the JSON file.
        """
        locations = []
        try:
            for loc_file in Path(LocationController._locations_folder).iterdir():
                if loc_file.is_file() and loc_file.suffix == '.json':
                    locations.append(loc_file.name)
        except FileNotFoundError:
            print(f"File not found in directory: {LocationController._locations_folder}")
        except json.JSONDecodeError:
            print("Error decoding JSON from one of the files.")
        except Exception as e:
            print(f"Unexpected error: {e}")
        return locations
    
    @staticmethod
    def get_random_unblocked_location(base_api: BaseApi, radius: float = 1, owner_tribe_id: int = None, map: ArkMap = ArkMap.RAGNAROK, limit: int = 5):
        tried = []

        while True:
            random_loc = LocationController.get_random_available_location(tried)
            if random_loc is None:
                raise ValueError("No available locations found.")
            tried.append(random_loc)
            coords = LocationController.get_loc_coordinates(random_loc, map)
            structures = base_api.get_at_location(map, coords, radius)

            if owner_tribe_id is not None:
                filtered = base_api.filter_by_owner(structures, owner_tribe_id=owner_tribe_id, invert=True)
            else:
                filtered = structures
            
            if len(filtered) < limit:
                with open(LocationController._locations_folder / f"{random_loc}", 'r') as file:
                    data = json.load(file)
                    return data, random_loc, coords
            else:
                print(f"There are {len(filtered)} other structures around {coords}, cannot spawn here")

    @staticmethod
    def add_active_location(location: str):
        """
        Adds a new active location to the JSON file.
        """
        locations = LocationController.get_active_locations()
        if location not in locations:
            locations.append(location)
            with open(LocationController._active_location_path, 'w') as file:
                json.dump(locations, file, indent=4)
            print(f"Location {location} added successfully.")
        else:
            print(f"Location {location} already exists.")

    @staticmethod
    def remove_active_location(location: str):
        """
        Removes an active location from the JSON file.
        """
        locations = LocationController.get_active_locations()
        if location in locations:
            locations.remove(location)
            with open(LocationController._active_location_path, 'w') as file:
                json.dump(locations, file, indent=4)
            print(f"Location {location} removed successfully.")
        else:
            print(f"Location {location} not found.")
