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

from arkparse import AsaSave
from arkparse.enums import ArkMap, ArkStat
from arkparse.classes.dinos import Dinos
from arkparse.classes.resources import Resources
from arkparse.classes.placed_structures import PlacedStructures
import random

from .__manager import Manager

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

STATS = {
    "nrOfDinosOnMap" : None,
    "nrOfLv150" : None,
    "nrOfAlphas" : None,
    "isThereAlphaReaper" : None,
    "isThereAlphaBasilisk" : None,
    "isThereAlphaKark" : None,
    "nrOfReapersAbove130" : None,
    "nrOfDodos" : None,
    "nrOfDeaths" : None,
    "combinedLevel" : None,
    "nrOfTamedDinos" : None,
    "nrOfCryopoddedDinos" : None,
    "highestDeaths" : None,
    "highestLevel" : None,
    "nrOfMetalStructures" : None,
    "nrOfTekStructures" : None,
    "nrOfStoneStructures" : None,
    "nrOfTurrets" : None,
    "randomResourceName" : None,
    "randomResourceAmount" : None,
    "nrOfWildDinosWithStatsOver30": None,
    "nrOfWildDinosWithStatsOver35": None,
    "nrOfWildDinosWithStatsOver40": None,
    "nrOfTamedDinosWithBaseStatsOver50": None,
    "nrOfTamedDinosWithBaseStatsOver60": None,
    "highestWildDinoHealthStat": None,
    "highestWildDinoDamageStat": None,
    "highestWildDinoOxygenStat": None,
    "highestWildDinoStat": None,
    "highestTamedDinoHealthStat": None,
    "highestTamedDinoDamageStat": None,
    "highestTamedDinoOxygenStat": None,
    "highestTamedDinoStat": None,
    "mostMutations": None,
    "nrOfSleepingBags": None,
    "higestArmorSaddle": None,
    "highestDamageWeapon": None,
}

class RandomStatManager(Manager):
    
    def __init__(self, ftp_config: ArkFtpClient, rconapi: RconApi):
        super().__init__(self.__process, "random stat manager")
        self.ftp_config = ftp_config
        self.previous_save: ArkFile = None
        self.ftp_client: ArkFtpClient = ArkFtpClient.from_config(ftp_config, ArkMap.ABERRATION)
        self.player_api: PlayerApi = PlayerApi(ftp_config, ArkMap.ABERRATION)
        self.rcon: RconApi = rconapi
        self.dino_api = None

    def stop(self):
        super().stop()
        self.player_api.dispose()
        self.ftp_client.close()
        self.ftp_client = None

    def testprocess(self):
        self.__process(1)
        
    def __process(self, interval: int):
        if self.ftp_client is None:
            self.ftp_client: ArkFtpClient = ArkFtpClient.from_config(self.ftp_config, ArkMap.ABERRATION)

        self.ftp_client.connect()
        
        save_file_info : ArkFile = self.ftp_client.check_save_file()[0]
        STATS["randomResourceName"] = list(RESOURCES.keys())[random.randint(0, len(RESOURCES.keys()) - 1)]

        if self.previous_save is None or save_file_info.is_newer_than(self.previous_save):
            self._print("New save file detected, downloading...")
            self.previous_save = save_file_info
            save_path = self.ftp_client.download_save_file(Path.cwd())

            self._print("Parsing files...")
            save = AsaSave(save_path)
            self.dino_api = DinoApi(save)
            self._print("Parsing dinos")
            self.dino_api.get_all()
            structure_api = StructureApi(save)
            stackable_api = StackableApi(save)
            equipment_api = EquipmentApi(save)
            
            self._print("Parsing resources")
            
            STATS["randomResourceAmount"] = stackable_api.get_count(stackable_api.get_by_class(StackableApi.Classes.RESOURCE, [RESOURCES[STATS["randomResourceName"]]]))
            self._print("Parsing all dinos")
            STATS["nrOfDinosOnMap"] = len(self.dino_api.get_all_wild())
            STATS["nrOfLv150"] = len(self.dino_api.get_all_filtered(150, 150, None, tamed=False, include_cryopodded=False))
            self._print("Parsing alphas")
            STATS["nrOfAlphas"] = len(self.dino_api.get_all_wild_by_class([Dinos.alpha_karkinos, Dinos.alpha_reaper_king, Dinos.alpha_basilisk]))
            STATS["isThereAlphaReaper"] = len(self.dino_api.get_all_wild_by_class([Dinos.alpha_reaper_king])) > 0
            STATS["isThereAlphaBasilisk"] = len(self.dino_api.get_all_wild_by_class([Dinos.alpha_basilisk])) > 0
            STATS["isThereAlphaKark"] = len(self.dino_api.get_all_wild_by_class([Dinos.alpha_karkinos])) > 0
            STATS["nrOfReapersAbove130"] = len(self.dino_api.get_all_filtered(130, None, Dinos.reaper_queen, False, include_cryopodded=False))
            STATS["nrOfDodos"] = len(self.dino_api.get_all_wild_by_class([Dinos.abberant.dodo]))
            self._print("Parsing players")
            STATS["nrOfDeaths"] = self.player_api.get_deaths()
            STATS["combinedLevel"] = self.player_api.get_level()
            STATS["nrOfTamedDinos"] = len(self.dino_api.get_all_tamed(include_cryopodded=False))
            STATS["nrOfCryopoddedDinos"] = len(self.dino_api.get_all_in_cryopod())
            STATS["highestDeaths"] = self.player_api.get_player_with(PlayerApi.Stat.DEATHS, PlayerApi.StatType.HIGHEST)
            STATS["highestLevel"] = self.player_api.get_player_with(PlayerApi.Stat.LEVEL, PlayerApi.StatType.HIGHEST)
            self._print("Parsing structures")
            STATS["nrOfMetalStructures"] = len(structure_api.get_by_class(PlacedStructures.metal.all_bps))
            STATS["nrOfTekStructures"] = len(structure_api.get_by_class(PlacedStructures.tek.all_bps))
            STATS["nrOfStoneStructures"] = len(structure_api.get_by_class(PlacedStructures.stone.all_bps))
            STATS["nrOfTurrets"] = len(structure_api.get_by_class(PlacedStructures.turrets.all_bps))
            self._print("Parsing dino stats")
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
            STATS["nrOfSleepingBags"] = len(structure_api.get_by_class([PlacedStructures.utility.sleeping_bag]))
            self._print("Parsing equipment")
            saddles: Dict[UUID, Saddle] = equipment_api.get_filtered(EquipmentApi.Classes.SADDLE)
            weapons: Dict[UUID, Weapon] = equipment_api.get_filtered(EquipmentApi.Classes.WEAPON)
            STATS["higestArmorSaddle"] = max(saddles.values(), key=lambda x: x.armor)
            STATS["highestDamageWeapon"] = max(weapons.values(), key=lambda x: x.damage)

        message = self.get_random_stat()
        self._print(f"Sending message: {message}")
        self.rcon.send_message(message)
        self.ftp_client.close()

    def get_most_mutations(self):
        dinos = self.dino_api.get_all_tamed() 
        most_mutations: TamedDino = None
        for dino in dinos.values():
            dino: TamedDino = dino
            curr = 0 if most_mutations is None else most_mutations.stats.get_total_mutations()
            if most_mutations is None or (dino.stats.get_total_mutations() > curr):
                most_mutations = dino

        return int(most_mutations.stats.get_total_mutations())

    def get_random_dino_with_stat_over_30(self):
        dinos: Dict[UUID, Dino] = self.dino_api.get_all_filtered(tamed=False, stat_minimum=30, level_upper_bound=150)

        random_dino: Dino = random.choice(list(dinos.values()))

        return f"{random_dino.location.as_map_coords(ArkMap.ABERRATION)}, might be a dodo though ;)"

    def get_random_alpha_stat(self):
        def craft_string(name, stat):
            return f"Is there an alpha {name}? Survey says... {'Yes!!' if {stat} else 'Nope! (at least not yet)'}"

        options = [
            lambda: (craft_string("reaper", STATS.get('isThereAlphaReaper', False))),
            lambda: (craft_string("basilisk", STATS.get('isThereAlphaBasilisk', False))),
            lambda: (craft_string("karkinos", STATS.get('isThereAlphaKark', False))),
        ]
        
        # Generate all possible messages
        all_messages = [option() for option in options]
        
        # Filter out any empty strings
        valid_messages = [msg for msg in all_messages if msg]
        
        if not valid_messages:
            return "No valid alpha statistics available to display."
        
        # Randomly select and return one of the valid messages
        return random.choice(valid_messages)
    
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

        if stat == "nrOfWildDinosWithStatsOver30":
            message += f", one is at {self.get_random_dino_with_stat_over_30()}"

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
            
            self.get_random_alpha_stat,
            lambda: (
                f"There are {STATS.get('nrOfReapersAbove130', 0)} reapers above level 130, might be a good idea to track one down!"
                if STATS.get('nrOfReapersAbove130', 0) > 0
                else "Not a single reaper queens above 130 spotted, wtffffff"
            ),
            lambda: f"There have been {STATS.get('nrOfDeaths', 0)} deaths, RIP!",
            
            lambda: f"Our combined level is {STATS.get('combinedLevel', 0)}, APES TOGETHER STRONG!",
            
            lambda: (
                f"There are {STATS.get('nrOfTamedDinos', 0)} tamed dinos walking around, make sure they are fed!"
                if STATS.get('nrOfTamedDinos', 0) > 0
                else ""
            ),
            lambda: (
                f"There are {STATS.get('nrOfCryopoddedDinos', 0)} dinos in cryopods, make sure the cryopods don't run out!"
                if STATS.get('nrOfCryopoddedDinos', 0) > 0
                else ""
            ),
            lambda: (
                f"{STATS['highestDeaths'][0].name} has the most deaths: {STATS['highestDeaths'][1]}.. Git gud, scrub!"
                if 'highestDeaths' in STATS and STATS['highestDeaths']
                else ""
            ),
            lambda: (
                f"{STATS['highestLevel'][0].name} is the highest level player: {STATS['highestLevel'][1]}, take a break buddy!"
                if 'highestLevel' in STATS and STATS['highestLevel']
                else ""
            ),
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
            lambda: f"There are {STATS.get('nrOfSleepingBags', 0)} sleeping bags on the map, check your base for random Barts ;)"
        ]
        
        # Generate all possible messages
        all_messages = [option() for option in options]
        
        # Filter out any empty strings
        valid_messages = [msg for msg in all_messages if msg]
        
        if not valid_messages:
            return "No valid statistics available to display."
        
        # Randomly select and return one of the valid messages
        return random.choice(valid_messages)

