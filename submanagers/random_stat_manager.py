from arkparse.ftp.ark_ftp_client import ArkFtpClient, ArkFile, ArkMap
from pathlib import Path
from typing import Dict
from uuid import UUID

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

from arkparse import AsaSave
from arkparse.enums import ArkMap, ArkStat
from arkparse.classes.dinos import Dinos
from arkparse.classes.resources import Resources
from arkparse.classes.placed_structures import PlacedStructures
import random

from .__manager import Manager
from .save_tracker import SaveTracker

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

STATS = {}

class RandomStatManager(Manager):
    def __init__(self, save_tracker: SaveTracker, rconapi: RconApi):
        super().__init__(self.__process, "random stat manager", 1033)
        self.rcon: RconApi = rconapi
        self.save_tracker: SaveTracker = save_tracker

    def __process(self, _: int):
        
        STATS["randomResourceName"] = list(RESOURCES.keys())[random.randint(0, len(RESOURCES.keys()) - 1)]

        self.player_api: PlayerApi = self.save_tracker.get_api(PlayerApi)
        self.dino_api: DinoApi = self.save_tracker.get_api(DinoApi)
        self.structure_api: StructureApi = self.save_tracker.get_api(StructureApi)
        self.stackable_api: StackableApi = self.save_tracker.get_api(StackableApi)
        self.equipment_api: EquipmentApi = self.save_tracker.get_api(EquipmentApi)

        # TEST zone
        # tamed = self.dino_api.get_all_tamed(include_cryopodded=False)
        # for uuid in tamed:
        #     print(uuid)

        self._print("Parsing resources", False)
        
        STATS["randomResourceAmount"] = self.stackable_api.get_count(self.stackable_api.get_by_class(StackableApi.Classes.RESOURCE, [RESOURCES[STATS["randomResourceName"]]]))
        self._print("Parsing all dinos", False)
        STATS["nrOfDinosOnMap"] = len(self.dino_api.get_all_wild())
        STATS["nrOfLv150"] = len(self.dino_api.get_all_filtered(150, 150, None, tamed=False, include_cryopodded=False))

        self._print("Parsing alphas", False)
        STATS["nrOfAlphas"] = len(self.dino_api.get_all_wild_by_class(Dinos.non_tameable.alpha.all_bps))
        STATS["nrOfDodos"] = len(self.dino_api.get_all_wild_by_class([Dinos.abberant.dodo]))

        self._print("Parsing strong dinos", False)
        STATS["nr_of_gigas"] = len(self.dino_api.get_all_wild_by_class([Dinos.giganotosaurus]))
        STATS["nr_of_rhyniognatha"] = len(self.dino_api.get_all_wild_by_class([Dinos.flyers.rhyniognatha]))
        STATS["nr_of_carchas"] = len(self.dino_api.get_all_wild_by_class([Dinos.carcharadontosaurus]))
        STATS["nr_of_liopleurodon"] = len(self.dino_api.get_all_wild_by_class([Dinos.liopleurodon])) 
        STATS["nr_of_cats"] = len(self.dino_api.get_all_wild_by_class([Dinos.shoulder_pets.cat]))

        self._print("Parsing players", False)
        STATS["nrOfDeaths"] = self.player_api.get_deaths()
        STATS["combinedLevel"] = self.player_api.get_level()
        STATS["nrOfTamedDinos"] = len(self.dino_api.get_all_tamed(include_cryopodded=False))
        STATS["nrOfCryopoddedDinos"] = len(self.dino_api.get_all_in_cryopod())
        STATS["highestDeaths"] = self.player_api.get_player_with(PlayerApi.Stat.DEATHS, PlayerApi.StatType.HIGHEST)
        STATS["highestLevel"] = self.player_api.get_player_with(PlayerApi.Stat.LEVEL, PlayerApi.StatType.HIGHEST)

        self._print("Parsing structures", False)
        STATS["nrOfMetalStructures"] = len(self.structure_api.get_by_class(PlacedStructures.metal.all_bps))
        STATS["nrOfTekStructures"] = len(self.structure_api.get_by_class(PlacedStructures.tek.all_bps))
        STATS["nrOfStoneStructures"] = len(self.structure_api.get_by_class(PlacedStructures.stone.all_bps))
        STATS["nrOfTurrets"] = len(self.structure_api.get_by_class(PlacedStructures.turrets.all_bps))

        self._print("Parsing dino stats", False)
        STATS["nrOfWildDinosWithStatsOver30"] = len(self.dino_api.get_all_filtered(tamed=False, stat_minimum=30, level_upper_bound=150))
        STATS["nrOfWildDinosWithStatsOver35"] = len(self.dino_api.get_all_filtered(tamed=False, stat_minimum=35, level_upper_bound=150))
        STATS["nrOfWildDinosWithStatsOver40"] = len(self.dino_api.get_all_filtered(tamed=False, stat_minimum=40, level_upper_bound=150))
        STATS["nrOfTamedDinosWithBaseStatsOver50"] = len(self.dino_api.get_all_filtered(tamed=True, stat_minimum=50))
        STATS["nrOfTamedDinosWithBaseStatsOver60"] = len(self.dino_api.get_all_filtered(tamed=True, stat_minimum=60))
        STATS["highestWildDinoHealthStat"] = self.dino_api.get_best_dino_for_stat(stat=ArkStat.HEALTH, only_untamed=True)[1]
        STATS["highestWildDinoDamageStat"] = self.dino_api.get_best_dino_for_stat(stat=ArkStat.MELEE_DAMAGE, only_untamed=True)[1]
        STATS["highestWildDinoOxygenStat"] = self.dino_api.get_best_dino_for_stat(stat=ArkStat.OXYGEN, only_untamed=True)[1]
        STATS["highestWildDinoStat"] = self.dino_api.get_best_dino_for_stat(only_untamed=True)[1]
        STATS["highestTamedDinoHealthStat"] = self.dino_api.get_best_dino_for_stat(stat=ArkStat.HEALTH, only_tamed=True, mutated_stat=True)[1]
        STATS["highestTamedDinoDamageStat"] = self.dino_api.get_best_dino_for_stat(stat=ArkStat.MELEE_DAMAGE, only_tamed=True, mutated_stat=True)[1]
        STATS["highestTamedDinoOxygenStat"] = self.dino_api.get_best_dino_for_stat(stat=ArkStat.OXYGEN, only_tamed=True, mutated_stat=True)[1]
        STATS["highestTamedDinoStat"] = self.dino_api.get_best_dino_for_stat(only_tamed=True, mutated_stat=True)[1]
        STATS["mostMutations"] = self.get_most_mutations()
        STATS["nrOfSleepingBags"] = len(self.structure_api.get_by_class([PlacedStructures.utility.sleeping_bag]))

        # ideas: baby dinos, death worms, reasons of death, most pyromanes, most stegos, most rexes, most gigas, most alphas, most bps, nr of bps, nr of bps per type, 

        self._print("Parsing equipment", False)
        saddles: Dict[UUID, Saddle] = self.equipment_api.get_filtered(EquipmentApi.Classes.SADDLE)
        weapons: Dict[UUID, Weapon] = self.equipment_api.get_filtered(EquipmentApi.Classes.WEAPON)
        armor: Dict[UUID, Armor] = self.equipment_api.get_filtered(EquipmentApi.Classes.ARMOR)
        STATS["highestArmorSaddle"] = max(saddles.values(), key=lambda x: x.armor).armor if len(saddles) > 0 else "0"
        STATS["highestDamageWeapon"] = max(weapons.values(), key=lambda x: x.damage).damage if len(weapons) > 0 else "0"
        STATS["highestDuraArmor"] = max(armor.values(), key=lambda x: x.durability).durability if len(armor) > 0 else "0"

        message = self.get_random_stat()
        self._print(f"Sending message: {message}")
        self.rcon.send_message(message)

    def get_most_mutations(self):
        dinos = self.dino_api.get_all_tamed() 
        most_mutations: TamedDino = None
        for dino in dinos.values():
            dino: TamedDino = dino
            curr = 0 if most_mutations is None else most_mutations.stats.get_total_mutations()
            if most_mutations is None or (dino.stats.get_total_mutations() > curr):
                most_mutations = dino

        if most_mutations is None:
            return 0

        return int(most_mutations.stats.get_total_mutations())
    
    def get_random_structure_number_message(self):
        structures = {"nrOfMetalStructures": "metal", "nrOfTekStructures": "tek", "nrOfStoneStructures": "stone"}
        
        structure = random.choice(list(structures.keys()))

        message = f"We placed {STATS.get(structure, 0)} {structures[structure]} structures on the map"

        if STATS.get(structure, 0) < 1:
            message += ", time to get building!"
            return message

        if structure == "nrOfMetalStructures":
            message += ", time to upgrade to tek?"
        elif structure == "nrOfTekStructures":
            message += ", waste of resources, goddamn"
        elif structure == "nrOfStoneStructures":
            message += ", clean up your taming pens pls"

        return message
    
    def get_random_dino_stat_message(self):
        stats = {"nrOfWildDinosWithStatsOver30": ["wild", "30"], "nrOfWildDinosWithStatsOver35": ["wild", "35"], "nrOfWildDinosWithStatsOver40": ["wild", "40"], 
                 "nrOfTamedDinosWithBaseStatsOver50": ["tamed", "50"], "nrOfTamedDinosWithBaseStatsOver60": ["tamed", "60"]}
        
        stat = random.choice(list(stats.keys()))

        message = f"There are {STATS.get(stat, 0)} {stats[stat][0]} dinos with stats over {stats[stat][1]}"

        return message
    
    def get_random_highest_stat_message(self):
        stats = {"highestWildDinoHealthStat": ["wild", "health"], "highestWildDinoDamageStat": ["wild", "damage"], "highestWildDinoOxygenStat": ["wild", "oxygen"],
                    "highestWildDinoStat": ["wild", "stat"], "highestTamedDinoHealthStat": ["tamed", "health"], "highestTamedDinoDamageStat": ["tamed", "damage"],
                    "highestTamedDinoOxygenStat": ["tamed", "oxygen"], "highestTamedDinoStat": ["tamed", "stat"]}
        
        stat = random.choice(list(stats.keys()))

        message = f"The highest {stats[stat][1]} on a {stats[stat][0]} dino is {STATS.get(stat, 0)}"

        return message

    def get_random_stat(self):
        # Define a list of possible stat messages as lambda functions that return strings
        options = [
            lambda: f"There are {STATS.get('nrOfDinosOnMap', 0)} dinos on the map, RIP server performance...",
            
            lambda: f"There are {STATS.get('nrOfLv150', 0)} level 150 dinos on the map, go tame them!",
            
            lambda: (
                f"There are {STATS.get('nrOfAlphas', 0)} alphas, but which ones..."
                if STATS.get('nrOfAlphas', 0) > 0
                else "No alphas on the map :("
            ),
            
            # self.get_random_alpha_stat,
            lambda: ("Not a single reaper queens above 130 spotted, but i guess that makes sense on ragnarok"),

            lambda: f"There have been {STATS.get('nrOfDeaths', 0)} deaths, {'RIP!' if (STATS.get('nrOfDeaths', 0) > 0) else 'god damn, pro af!'}",
            lambda: f"Our combined level is {STATS.get('combinedLevel', 0)}, APES TOGETHER STRONG!",
            
            lambda: (f"There are {STATS.get('nrOfTamedDinos', 0)} tamed dinos walking around, make sure they are fed!" if (STATS.get('nrOfTamedDinos', 0) > 0) else ""),
            lambda: ( f"There are {STATS.get('nrOfCryopoddedDinos', 0)} dinos in cryopods, make sure the cryopods don't run out!" if (STATS.get('nrOfCryopoddedDinos', 0) > 0) else ""),
            lambda: ( f"{STATS['highestDeaths'][0].name} has the most deaths: {STATS['highestDeaths'][1]}.. Git gud, scrub!" if 'highestDeaths' in STATS and STATS['highestDeaths'] else ""),
            lambda: ( f"{STATS['highestLevel'][0].name} is the highest level player: {STATS['highestLevel'][1]}, take a break buddy!" if 'highestLevel' in STATS and STATS['highestLevel'] else ""),

            self.get_random_structure_number_message,
            lambda: f"We gathered {STATS.get('randomResourceAmount', 0)} units of {STATS.get('randomResourceName', 0)}",

            lambda: (
                "Not a single turret on the map, smoooooth sailing"
                if STATS.get('nrOfTurrets', 0) == 0
                else f"There are currently {STATS.get('nrOfTurrets', 0)} turrets placed on the map, careful ;)"
                if STATS.get('nrOfTurrets', 0) > 1
                else "There is a turret on the map, it's getting real!"
            ),

            self.get_random_dino_stat_message,
            self.get_random_highest_stat_message,

            lambda: f"Someone has a dino with {STATS.get('mostMutations', 0)} mutations, make those dinos have coitus!",
            lambda: f"There are {STATS.get('nrOfSleepingBags', 0)} sleeping bags on the map, check your base for random Barts ;)",

            lambda: (f"There are {STATS.get('nr_of_gigas', 0)} gigas on the map, don't get eaten!"
                if STATS.get('nr_of_gigas', 0) > 0
                else "No gigas on the map, Vincent probably tamed all of them!"
            ),

            lambda: (f"There are {STATS.get('nr_of_rhyniognatha', 0)} rhyniognathas on the map, let's get someone pregnant (not Sarah)!"
                if STATS.get('nr_of_rhyniognatha', 0) > 0
                else "No rhyniognathas on the map, another time!"),

            lambda: (f"There are {STATS.get('nr_of_carchas', 0)} carchas on the map, time for a hunt!"
                if STATS.get('nr_of_carchas', 0) > 0
                else "No carchas on the map, rather have gigas anyway!"),

            lambda: (f"There are {STATS.get('nr_of_liopleurodon', 0)} liopleurodons on the map, let's get some loot!"
                if STATS.get('nr_of_liopleurodon', 0) > 0
                else "No liopleurodons on the map, better luck next time!"),

            lambda: (f"There are {STATS.get('nr_of_cats', 0)} cats on the map, heeeere kitty kitty!"
                if STATS.get('nr_of_cats', 0) > 0
                else "No cats on the map, damn it..."),

            lambda: f"The highest armor saddle has {STATS.get('higestArmorSaddle', 0)} armor!",
            lambda: f"The highest damage weapon has {STATS.get('highestDamageWeapon', 0)} damage!",
            lambda: f"The highest durability armor has {STATS.get('highestDuraArmor', 0)} durability!"

        ]
        
        # Generate all possible messages
        all_messages = [option() for option in options]
        
        # Filter out any empty strings
        valid_messages = [msg for msg in all_messages if msg]
        
        if not valid_messages:
            return "No valid statistics available to display."
        
        # Randomly select and return one of the valid messages
        return random.choice(valid_messages)

