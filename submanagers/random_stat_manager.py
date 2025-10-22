from arkparse.ftp.ark_ftp_client import ArkFtpClient, ArkFile, ArkMap
from pathlib import Path
from typing import Dict, List, Union
from uuid import UUID
from abc import ABC, abstractmethod

from arkparse.api.dino_api import DinoApi
from arkparse.api.player_api import PlayerApi
from arkparse.api.rcon_api import RconApi
from arkparse.api.stackable_api import StackableApi
from arkparse.api.structure_api import StructureApi
from arkparse.api.equipment_api import EquipmentApi

from arkparse.object_model.dinos.dino import Dino
from arkparse.object_model.dinos.tamed_dino import TamedDino
from arkparse.object_model.equipment.saddle import Saddle
from arkparse.object_model.equipment.weapon import Weapon
from arkparse.object_model.equipment.armor import Armor
from arkparse.ark_tribe import ArkTribe

from arkparse import AsaSave, Classes
from arkparse.enums import ArkMap, ArkStat, ArkItemQuality
from arkparse.classes.dinos import Dinos
from arkparse.classes.resources import Resources
from arkparse.classes.placed_structures import PlacedStructures
import random

from .__manager import Manager
from .save_tracker import SaveTracker



STATS = {}

class RandomStat(ABC):
    value: any
    save_tracker: SaveTracker
    
    def __init__(self, save_tracker: SaveTracker):
        self.value = None
        self.save_tracker = save_tracker

    @abstractmethod
    def _get_value(self) -> str:
        pass

    @abstractmethod
    def get_message(self) -> str:
        pass

class RandomResourceAmount(RandomStat):
    RESOURCES = {
        "wood": Resources.Basic.wood,
        "stone": Resources.Basic.stone,
        "obsidian": Resources.Basic.obsidian,
        "crystal": Resources.Basic.crystal,
        "oil": Resources.Basic.oil,
        "organic polymer": Resources.Basic.polymer_organic,
        "black_pearl": Resources.Basic.black_pearl,
        "cementing_paste": Resources.Crafted.chitin_paste,
        "hide": Resources.Basic.hide,
        "fiber": Resources.Basic.fiber,
        "keratin": Resources.Basic.keratin,
        "chitin": Resources.Basic.chitin,
        "charcoal": Resources.Crafted.charcoal,
        "flint": Resources.Basic.flint,
        "thatch": Resources.Basic.thatch,
        "metal ingot": Resources.Crafted.metal_ingot,
        "electronics": Resources.Crafted.electronics,
        "pelt": Resources.Basic.pelt,
    }

    resource_name: str

    def _get_value(self):
        self.resource_name = list(self.RESOURCES.keys())[random.randint(0, len(self.RESOURCES.keys()) - 1)]
        self.value = self.save_tracker.get_api(StackableApi).get_count(self.save_tracker.get_api(StackableApi).get_by_class(StackableApi.Classes.RESOURCE, [self.RESOURCES[self.resource_name]]))

    def get_message(self) -> str:
        self._get_value()
        return f"We gathered {self.value} units of {self.resource_name}"

class NumberOfDinos(RandomStat):
    def _get_value(self):
        self.value = len(self.save_tracker.get_api(DinoApi).get_all_wild())
    
    def get_message(self) -> str:
        self._get_value()
        return f"There are {self.value} dinos on the map, RIP server performance..."

class NumberOfAlphas(RandomStat):
    def _get_value(self):
        self.value = len(self.save_tracker.get_api(DinoApi).get_all_wild_by_class(Dinos.non_tameable.alpha.all_bps))
    
    def get_message(self) -> str:
        self._get_value()
        if self.value > 0:
            return f"There are {self.value} alphas, but which ones..."
        else:
            return "No alphas on the map :("

class NumberOfDinosOfType(RandomStat):
    DINO_BPS = {
        "giganotosaurus": [Dinos.giganotosaurus, Dinos.paleo.giga],
        "rhyniognatha": [Dinos.flyers.rhyniognatha],
        "carcharadontosaurus": [Dinos.carcharadontosaurus],
        "liopleurodon": [Dinos.liopleurodon],
        "cat": [Dinos.shoulder_pets.cat],
        "dodo": [Dinos.abberant.dodo, Dinos.dodo],
        "reaper queen": [Dinos.reaper_queen],
        "death worms": [Dinos.non_tameable.death_worm],
        "titanoboa": [Dinos.titanoboa],
    }

    dino_type: str

    def _get_value(self, forced_type: str = None):
        if forced_type:
            self.dino_type = forced_type
        else:
            self.dino_type = list(self.DINO_BPS.keys())[random.randint(0, len(self.DINO_BPS.keys()) - 1)]
        self.value = len(self.save_tracker.get_api(DinoApi).get_all_wild_by_class(self.DINO_BPS[self.dino_type]))

    def get_message(self, forced_type: str = None) -> str:
        self._get_value(forced_type)
        if self.dino_type == "giganotosaurus":
            if self.value > 0:
                return f"There are {self.value} gigas on the map, don't get eaten!"
            else:
                return "No gigas on the map, Vincent probably tamed all of them!"
        elif self.dino_type == "rhyniognatha":
            if self.value > 0:
                return f"There are {self.value} rhyniognathas on the map, let's get someone pregnant (not Sarah)!"
            else:
                return "No rhyniognathas on the map, another time!"
        elif self.dino_type == "carcharadontosaurus":
            if self.value > 0:
                return f"There are {self.value} carchas on the map, time for a hunt!"
            else:
                return "No carchas on the map, rather have gigas anyway!"
        elif self.dino_type == "liopleurodon":
            if self.value > 0:
                return f"There are {self.value} liopleurodons on the map, let's get some loot!"
            else:
                return "No liopleurodons on the map, better luck next time!"
        elif self.dino_type == "cat":
            if self.value > 0:
                return f"There are {self.value} cats on the map, heeeere kitty kitty!"
            else:
                return "No cats on the map, damn it..."
        elif self.dino_type == "dodo":
            return f"There are {self.value} dodos on the map"
        elif self.dino_type == "reaper queen":
            if self.value > 0:
                return f"There are {self.value} reaper queens on the map, wait a minute... what?"
            else:
                return "No reaper queens on the map, but I guess that makes sense on Ragnarok!"
        elif self.dino_type == "death worms":
            if self.value > 0:
                return f"There are {self.value} death worms on the map, stay away from the desert!"
            else:
                return "No death worms on the map"
        elif self.dino_type == "titanoboa":
            if self.value > 0:
                return f"Better get back on your boat Davy Jones! There are {self.value} titanoboa ready to knock you out!"
            else:
                return "No titanoboa on the map, lucky Davy!"

class NumberOfLv150WildDinos(RandomStat):
    def _get_value(self):
        self.value = len(self.save_tracker.get_api(DinoApi).get_all_filtered(150, 150, None, tamed=False, include_cryopodded=False))
    
    def get_message(self) -> str:
        self._get_value()
        return f"There are {self.value} level 150 dinos on the map, go tame them!"

class NumberOfDeaths(RandomStat):
    def _get_value(self):
        self.value = self.save_tracker.get_api(PlayerApi).get_deaths()
    
    def get_message(self) -> str:
        self._get_value()
        return f"There have been {int(self.value)} deaths, {'RIP!' if self.value > 0 else 'god damn, pro af!'}"
    
class CombinedLevel(RandomStat):
    def _get_value(self):
        self.value = self.save_tracker.get_api(PlayerApi).get_level()
    
    def get_message(self) -> str:
        self._get_value()
        return f"Our combined level is {self.value}, APES TOGETHER STRONG!"

class NumberOfTamedDinos(RandomStat):
    def _get_value(self):
        self.value = len(self.save_tracker.get_api(DinoApi).get_all_tamed(include_cryopodded=False))
    
    def get_message(self) -> str:
        self._get_value()
        return f"There are {self.value} tamed dinos walking around, make sure they are fed!"
    
class NumberOfCryopoddedDinos(RandomStat):
    def _get_value(self):
        self.value = len(self.save_tracker.get_api(DinoApi).get_all_in_cryopod())
    
    def get_message(self) -> str:
        self._get_value()
        return f"There are {self.value} dinos in cryopods, make sure the cryopods don't run out!"
    
class MostDeaths(RandomStat):
    def _get_value(self):
        self.value = self.save_tracker.get_api(PlayerApi).get_player_with(PlayerApi.Stat.DEATHS, PlayerApi.StatType.HIGHEST)
    
    def get_message(self) -> str:
        self._get_value()
        if self.value:
            return f"{self.value[0].name} has the most deaths: {int(self.value[1])}.. Git gud, scrub!"
        else:
            return ""
        
class HighestLevel(RandomStat):
    def _get_value(self):
        self.value = self.save_tracker.get_api(PlayerApi).get_player_with(PlayerApi.Stat.LEVEL, PlayerApi.StatType.HIGHEST)
    
    def get_message(self) -> str:
        self._get_value()
        if self.value:
            return f"{self.value[0].name} is the highest level player: {self.value[1]}, take a break buddy!"
        else:
            return ""
        
class TotalNumberOfStructures(RandomStat):
    def _get_value(self):
        self.value = len(self.save_tracker.get_api(StructureApi).get_all())
    
    def get_message(self) -> str:
        self._get_value()
        return f"There are {self.value} structures placed on the map."

class NumberOfStructuresOfType(RandomStat):
    STRUCTURE_BPS = {
        "metal": PlacedStructures.metal.all_bps,
        "tek": PlacedStructures.tek.all_bps,
        "stone": PlacedStructures.stone.all_bps
    }

    structure_type: str

    def _get_value(self):
        self.structure_type = list(self.STRUCTURE_BPS.keys())[random.randint(0, len(self.STRUCTURE_BPS.keys()) - 1)]
        self.value = len(self.save_tracker.get_api(StructureApi).get_by_class(self.STRUCTURE_BPS[self.structure_type]))

    def get_message(self) -> str:
        self._get_value()
        if self.structure_type == "metal":
            if self.value > 0:
                return f"There are {self.value} metal structures on the map, time to upgrade to tek?"
            else:
                return "No metal structures on the map, time to get some cementing paste!"
        elif self.structure_type == "tek":
            if self.value > 0:
                return f"There are {self.value} tek structures on the map, waste of resources!"
            else:
                return "No tek structures on the map, ugabuga mode engaged!"
        elif self.structure_type == "stone":
            if self.value > 0:
                return f"There are {self.value} stone structures on the map, clean up your taming pens pls"
            else:
                return "No stone structures on the map, still on thatch i see!"

class NumberOfTurrets(RandomStat):
    def _get_value(self):
        self.value = len(self.save_tracker.structure_api.get_by_class(Classes.structures.placed.turrets.all_bps))
    
    def get_message(self) -> str:
        self._get_value()
        if self.value == 0:
            return "Not a single turret on the map, smoooooth sailing"
        elif self.value > 0:
            return f"There are currently {self.value} turrets placed on the map, careful ;)"

class DinoWithStatOver(RandomStat):
    LEVELS = [
        30, 35, 40, 50, 60
    ]
    selected_level: int

    def _get_value(self):
        self.selected_level = self.LEVELS[random.randint(0, len(self.LEVELS) - 1)]
        self.value = len(self.save_tracker.dino_api.get_all_filtered(tamed=False, stat_minimum=self.selected_level, level_upper_bound=150))

    def get_message(self) -> str:
        self._get_value()
        return f"There are {self.value} wild dinos with a stat over {self.selected_level}"
    
class TamedDinoWithStatOver(RandomStat):
    LEVELS = [
        50, 60, 70, 80, 90
    ]
    selected_level: int

    def _get_value(self):
        self.selected_level = self.LEVELS[random.randint(0, len(self.LEVELS) - 1)]
        self.value = len(self.save_tracker.dino_api.get_all_filtered(tamed=True, stat_minimum=self.selected_level, level_upper_bound=1000))
    
    def get_message(self) -> str:
        self._get_value()
        return f"There are {self.value} tamed dinos with a base stat over {self.selected_level}"
    
class WildDinoWithHighestStat(RandomStat):
    STATS = [ArkStat.HEALTH, ArkStat.OXYGEN, ArkStat.MELEE_DAMAGE, ArkStat.STAMINA, ArkStat.WEIGHT, ArkStat.FOOD]
    selected_stat: ArkStat

    def _get_value(self):
        self.selected_stat = self.STATS[random.randint(0, len(self.STATS) - 1)]
        best_dino, best_value, _ = self.save_tracker.dino_api.get_best_dino_for_stat(stat=self.selected_stat, only_untamed=True, level_upper_bound=150)
        self.value = best_value if best_dino else 0

    def get_message(self) -> str:
        self._get_value()
        stat_name = self.selected_stat.name.replace("_", " ").lower()
        return f"The highest {stat_name} on a wild dino is {self.value}"
    
class TamedDinoWithHighestStat(RandomStat):
    STATS = [ArkStat.HEALTH, ArkStat.OXYGEN, ArkStat.MELEE_DAMAGE, ArkStat.STAMINA, ArkStat.WEIGHT, ArkStat.FOOD]
    selected_stat: ArkStat

    def _get_value(self):
        self.selected_stat = self.STATS[random.randint(0, len(self.STATS) - 1)]
        best_dino, best_value, _ = self.save_tracker.dino_api.get_best_dino_for_stat(stat=self.selected_stat, only_tamed=True, mutated_stat=True, level_upper_bound=1000)
        self.value = best_value if best_dino else 0

    def get_message(self) -> str:
        self._get_value()
        stat_name = self.selected_stat.name.replace("_", " ").lower()
        return f"The highest {stat_name} on a tamed dino is {self.value}"

class HighestStatOnWildDino(RandomStat):
    def _get_value(self):
        best_dino, best_value, best_stat = self.save_tracker.dino_api.get_best_dino_for_stat(only_untamed=True, level_upper_bound=150)
        self.value = (best_dino, best_value, best_stat) if best_dino else (None, 0, None)

    def get_message(self) -> str:
        self._get_value()
        if self.value[0] is None:
            return "No wild dinos found"
        stat_name = self.value[2].name.replace("_", " ").lower() if self.value[2] else "unknown stat"
        return f"The highest {stat_name} on a wild dino is {self.value[1]} on a {self.value[0].get_short_name()}"
    
class HighestStatOnTamedDino(RandomStat):
    def _get_value(self):
        best_dino, best_value, best_stat = self.save_tracker.dino_api.get_best_dino_for_stat(only_tamed=True, mutated_stat=True, level_upper_bound=1000)
        self.value = (best_dino, best_value, best_stat) if best_dino else (None, 0, None)

    def get_message(self) -> str:
        self._get_value()
        if self.value[0] is None:
            return "No tamed dinos found"
        stat_name = self.value[2].name.replace("_", " ").lower() if self.value[2] else "unknown stat"
        return f"The highest {stat_name} on a tamed dino is {self.value[1]}"

class MostMutations(RandomStat):
    def _get_value(self):
        dinos = self.save_tracker.dino_api.get_all_tamed() 
        most_mutations: TamedDino = None
        for dino in dinos.values():
            dino: TamedDino = dino
            curr = 0 if most_mutations is None else most_mutations.stats.get_total_mutations()
            if most_mutations is None or (dino.stats.get_total_mutations() > curr):
                most_mutations = dino

        if most_mutations is None:
            self.value = (None, 0)
        else:
            self.value = (most_mutations, most_mutations.stats.get_total_mutations())

    def get_message(self) -> str:
        self._get_value()
        if self.value[0] is None:
            return "No tamed dinos found"
        if self.value[1] == 0:
            return f"No mutations found on any tamed dino, get breeding!"
        return f"Someone has a dino with {int(self.value[1])} mutations, make those dinos have coitus!"

class HighestStatEquipment(RandomStat):
    def _get_value(self):
        p_api = self.save_tracker.get_api(PlayerApi)
        e_api = self.save_tracker.get_api(EquipmentApi)

        saddles: Dict[UUID, Saddle] = e_api.get_filtered(EquipmentApi.Classes.SADDLE)
        weapons: Dict[UUID, Weapon] = e_api.get_filtered(EquipmentApi.Classes.WEAPON)
        armor: Dict[UUID, Armor] = e_api.get_filtered(EquipmentApi.Classes.ARMOR)
        highest_armor = max(saddles.values(), key=lambda x: x.armor).armor if len(saddles) > 0 else 0
        highest_damage = max(weapons.values(), key=lambda x: x.damage).damage if len(weapons) > 0 else 0
        highest_durability = max(armor.values(), key=lambda x: x.durability).durability if len(armor) > 0 else 0

        self.value = (highest_armor, highest_damage, highest_durability)

    def get_message(self) -> str:
        selection = random.randint(0, 2)
        if selection == 0:
            return f"The highest armor on a saddle is {self.value[0]}"
        elif selection == 1:
            return f"The highest damage on a weapon is {self.value[1]}"
        else:
            return f"The highest durability on armor is {self.value[2]}"

class NumberOfSleepingBags(RandomStat):
    def _get_value(self):
        self.value = len(self.save_tracker.get_api(StructureApi).get_by_class([PlacedStructures.utility.sleeping_bag]))
    
    def get_message(self) -> str:
        self._get_value()
        return f"There are {self.value} sleeping bags on the map, check your base for random Barts ;)"

class NrOfBabiesWildDinos(RandomStat):
    def _get_value(self):
        self.value = len(self.save_tracker.dino_api.get_all_babies(include_tamed=False, include_wild=True))
    
    def get_message(self) -> str:
        self._get_value()
        return f"There are {self.value} wild baby dinos on the map, awwww! GO KILL MOMMY AND DADDY!"

class NrOfBabiesTamedDinos(RandomStat):
    def _get_value(self):
        self.value = len(self.save_tracker.dino_api.get_all_babies(include_tamed=True, include_wild=False, include_cryopodded=False))

    def get_message(self) -> str:
        self._get_value()
        return f"There are {self.value} tamed baby dinos on the map, keep them fed!"

class GetTamedMostByType(RandomStat):
    DINOS = {
        "pyromanes": [Dinos.dlc_dinos.firemane],
        "stegos": [Dinos.stegosaurus, Dinos.abberant.stegosaurus, Dinos.paleo.stego],
        "rexes": [Dinos.rex, Dinos.paleo.rex, Dinos.paleo.legacy_rex],
        "gigas": [Dinos.giganotosaurus, Dinos.paleo.giga],
    }
    selected_dino: str

    def sort_by_owner_tribe(self, dinos: List[TamedDino]) -> tuple:
        tribes: Dict[int, List[TamedDino]] = {}
        for dino in dinos:
            if dino.owner and dino.owner.target_team is not None:
                if dino.owner.target_team not in tribes:
                    tribes[dino.owner.target_team] = []
                tribes[dino.owner.target_team].append(dino)

        most_dinos = 0
        tribe_id = None
        for tribe, dino_list in tribes.items():
            if len(dino_list) > most_dinos:
                most_dinos = len(dino_list)
                tribe_id = tribe
        
        tribe: ArkTribe = self.save_tracker.get_api(PlayerApi).get_tribe(tribe_id)

        return (tribe, most_dinos)
        

    def _get_value(self):
        self.selected_dino = list(self.DINOS.keys())[random.randint(0, len(self.DINOS.keys()) - 1)]
        dinos = self.save_tracker.dino_api.get_all_tamed_by_class(self.DINOS[self.selected_dino])
        tribe, count = self.sort_by_owner_tribe(list(dinos.values()))
        self.value = (tribe, count)
    
    def get_message(self) -> str:
        self._get_value()
        if self.value[0] is None:
            return f"No tribe has tamed any {self.selected_dino}"
        tribe: ArkTribe = self.value[0]
        if self.selected_dino == "pyromanes":
            return f"Pay to win huh, {tribe.name} has the most pyromanes: {self.value[1]}"
        elif self.selected_dino == "stegos":
            return f"Gearing up for a raid? {tribe.name} has the most stegos: {self.value[1]}"
        elif self.selected_dino == "rexes":
            return f"Boss fight inc! {tribe.name} has the most rexes: {self.value[1]}"
        elif self.selected_dino == "gigas":
            return f"Bart better watch out, {tribe.name} has the most gigas: {self.value[1]}"

class NumberOfBpsPerType(RandomStat):
    TYPES = [
        EquipmentApi.Classes.SADDLE,
        EquipmentApi.Classes.WEAPON,
        EquipmentApi.Classes.ARMOR,
        EquipmentApi.Classes.SHIELD
    ]
    TYPE_TO_NAME = {
        EquipmentApi.Classes.SADDLE: "saddles",
        EquipmentApi.Classes.WEAPON: "weapons",
        EquipmentApi.Classes.ARMOR: "armors",
        EquipmentApi.Classes.SHIELD: "shields"
    }
    selected_type = None

    def _get_value(self):
        self.selected_type = self.TYPES[random.randint(0, len(self.TYPES) - 1)]
        self.value = len(self.save_tracker.equipment_api.get_filtered(cls=self.selected_type, only_blueprints=True, minimum_quality=ArkItemQuality.ASCENDANT))

    def get_message(self) -> str:
        self._get_value()
        return f"There are {self.value} ascendant {self.TYPE_TO_NAME[self.selected_type]} blueprints going around"

class NumberOfSpecificBpsPerType(RandomStat):
    TPYES = {
        "compound bow": [
            EquipmentApi.Classes.WEAPON,
            [Classes.equipment.weapons.advanced.compound_bow]
        ],
        "flak": [
            EquipmentApi.Classes.ARMOR,
            [Classes.equipment.armor.flak.boots, Classes.equipment.armor.flak.shirt, Classes.equipment.armor.flak.gloves, Classes.equipment.armor.flak.helmet, Classes.equipment.armor.flak.pants]
        ],
        "fabby sniper": [
            EquipmentApi.Classes.WEAPON,
            [Classes.equipment.weapons.advanced.fabricated_sniper]
        ],
        "shotty": [
            EquipmentApi.Classes.WEAPON,
            [Classes.equipment.weapons.advanced.fabricated_shotgun]
        ]
    }
    selected_type: str = None

    def _get_value(self):
        self.selected_type = list(self.TPYES.keys())[random.randint(0, len(self.TPYES) - 1)]
        cls, bps = self.TPYES[self.selected_type]
        self.value = len(self.save_tracker.equipment_api.get_filtered(cls=cls, only_blueprints=True, minimum_quality=ArkItemQuality.ASCENDANT, classes=bps))

    def get_message(self) -> str:
        self._get_value()
        return f"There are {self.value} ascendant {self.selected_type} blueprints on the map"

class RandomStatManager(Manager):
    def __init__(self, save_tracker: SaveTracker, rconapi: RconApi):
        super().__init__(self.__process, "random stat manager", 1033)
        self.stats: List[RandomStat] = []
        self.rcon: RconApi = rconapi
        self.save_tracker: SaveTracker = save_tracker

        self.stats.append(RandomResourceAmount(save_tracker))
        self.stats.append(NumberOfDinos(save_tracker))
        self.stats.append(NumberOfAlphas(save_tracker))
        self.stats.append(NumberOfDinosOfType(save_tracker))
        self.stats.append(NumberOfLv150WildDinos(save_tracker))
        self.stats.append(NumberOfDeaths(save_tracker))
        self.stats.append(CombinedLevel(save_tracker))
        self.stats.append(NumberOfTamedDinos(save_tracker))
        self.stats.append(NumberOfCryopoddedDinos(save_tracker))
        self.stats.append(MostDeaths(save_tracker))
        self.stats.append(HighestLevel(save_tracker))
        self.stats.append(TotalNumberOfStructures(save_tracker))
        self.stats.append(NumberOfStructuresOfType(save_tracker))
        self.stats.append(NumberOfTurrets(save_tracker))
        self.stats.append(DinoWithStatOver(save_tracker))
        self.stats.append(TamedDinoWithStatOver(save_tracker))
        self.stats.append(WildDinoWithHighestStat(save_tracker))
        self.stats.append(TamedDinoWithHighestStat(save_tracker))
        self.stats.append(HighestStatOnWildDino(save_tracker))
        self.stats.append(HighestStatOnTamedDino(save_tracker))
        self.stats.append(MostMutations(save_tracker))
        self.stats.append(HighestStatEquipment(save_tracker))
        self.stats.append(NumberOfSleepingBags(save_tracker))
        self.stats.append(NrOfBabiesWildDinos(save_tracker))
        self.stats.append(NrOfBabiesTamedDinos(save_tracker))
        self.stats.append(GetTamedMostByType(save_tracker))
        self.stats.append(NumberOfBpsPerType(save_tracker))
        self.stats.append(NumberOfSpecificBpsPerType(save_tracker))
        
    def __process(self, _: int):
        
        # ideaself.: reasons of death, most bps

        # Test
        for stat in self.stats:
            stat._get_value()
            self._print(stat.get_message())


        stat = self.stats[random.randint(0, len(self.stats) - 1)]
        message = stat.get_message()
        if message != "":
            self._print(message)
            self.rcon.send_message(message)