from arkparse.ftp.ark_ftp_client import ArkFtpClient, ArkFile, FtpArkMap
from pathlib import Path
from arkparse.api.dino_api import DinoApi
from arkparse.api.player_api import PlayerApi
from arkparse.api.rcon_api import RconApi
from arkparse.api.stackable_api import StackableApi
from arkparse.api.structure_api import StructureApi
from arkparse.objects.saves.asa_save import AsaSave
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
    "highestDeaths" : None,
    "highestLevel" : None,
    "nrOfMetalStructures" : None,
    "nrOfTekStructures" : None,
    "nrOfStoneStructures" : None,
    "nrOfTurrets" : None,
    "randomResourceName" : None,
    "randomResourceAmount" : None,
    # "nrOfWildDinosWithStatsOver35": None,
    # "nrOfWildDinosWithStatsOver40": None,
    # "nrOfTamedDinosWithBaseStatsOver45": None,
    # "nrOfTamedDinosWithBaseStatsOver50": None,
    # "highestWildDinoHealthStat": None,
    # "highestWildDinoDamageStat": None,
    # "highestWildDinoOxygenStat": None,
    # "highestTamedDinoHealthStat": None,
    # "highestTamedDinoDamageStat": None,
    # "highestTamedDinoOxygenStat": None,
    # "higestArmorSaddle": None,
    # "nrOfMaxArmorSaddles": None,
    # "highestDamageWeapon": None,
}

class RandomStatManager(Manager):
    
    def __init__(self, ftp_config: ArkFtpClient, rconapi: RconApi):
        super().__init__(self.__process, "random stat manager")
        self.previous_save: ArkFile = None
        self.ftp_client: ArkFtpClient = ArkFtpClient.from_config(ftp_config, FtpArkMap.ABERRATION)
        self.player_api: PlayerApi = PlayerApi(ftp_config, FtpArkMap.ABERRATION)
        self.rcon: RconApi = rconapi

    def stop(self):
        super().stop()
        self.player_api.dispose()
        self.ftp_client.close()

    def testprocess(self):
        self.__process(1)
        
    def __process(self, interval: int):
        self.ftp_client.connect()
        
        save_file_info : ArkFile = self.ftp_client.check_save_file()[0]

        if self.previous_save is None or save_file_info.is_newer_than(self.previous_save):
            print("New save file detected, downloading...")
            self.previous_save = save_file_info
            save_path = self.ftp_client.download_save_file(Path.cwd())

            print("Parsing files...")
            save = AsaSave(save_path)
            dino_api = DinoApi(save)
            structure_api = StructureApi(save)
            stackable_api = StackableApi(save)
            STATS["randomResourceName"] = list(RESOURCES.keys())[random.randint(0, len(RESOURCES.keys()) - 1)]
            STATS["randomResourceAmount"] = stackable_api.get_count(stackable_api.get_by_class(StackableApi.Classes.RESOURCE, [RESOURCES[STATS["randomResourceName"]]]))
            STATS["nrOfDinosOnMap"] = len(dino_api.get_all_wild())
            STATS["nrOfLv150"] = len(dino_api.get_all_filtered(150, 150, None, tamed=False, include_cryopodded=False))
            STATS["nrOfAlphas"] = len(dino_api.get_all_wild_by_class([Dinos.alpha_karkinos, Dinos.alpha_reaper_king, Dinos.alpha_basilisk]))
            STATS["isThereAlphaReaper"] = len(dino_api.get_all_wild_by_class([Dinos.alpha_reaper_king])) > 0
            STATS["isThereAlphaBasilisk"] = len(dino_api.get_all_wild_by_class([Dinos.alpha_basilisk])) > 0
            STATS["isThereAlphaKark"] = len(dino_api.get_all_wild_by_class([Dinos.alpha_karkinos])) > 0
            STATS["nrOfReapersAbove130"] = len(dino_api.get_all_filtered(130, None, Dinos.reaper_queen, False, include_cryopodded=False))
            STATS["nrOfDodos"] = len(dino_api.get_all_wild_by_class([Dinos.abberant.dodo]))
            STATS["nrOfDeaths"] = self.player_api.get_deaths()
            STATS["combinedLevel"] = self.player_api.get_level()
            STATS["nrOfTamedDinos"] = len(dino_api.get_all_tamed())
            STATS["highestDeaths"] = self.player_api.get_player_with(PlayerApi.Stat.DEATHS, PlayerApi.StatType.HIGHEST)
            STATS["highestLevel"] = self.player_api.get_player_with(PlayerApi.Stat.LEVEL, PlayerApi.StatType.HIGHEST)
            STATS["nrOfMetalStructures"] = len(structure_api.get_by_class(PlacedStructures.metal.all_bps))
            STATS["nrOfTekStructures"] = len(structure_api.get_by_class(PlacedStructures.tek.all_bps))
            STATS["nrOfStoneStructures"] = len(structure_api.get_by_class(PlacedStructures.stone.all_bps))
            STATS["nrOfTurrets"] = len(structure_api.get_by_class(PlacedStructures.turrets.all_bps))

        self.rcon.send_message(self.get_random_stat())
        self.ftp_client.close()

    def get_random_alpha_stat(self):
        def craft_string(name, stat):
            return f"Is there an alpha {name}? Survey says... {'YESS!!' if {stat} else 'Nope! (at least not yet)'}"

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

    def get_random_stat(self):
        """
        Randomly selects and returns one of the statistics from the STATS dictionary as a string.
        
        Parameters:
            STATS (dict): A dictionary containing various game statistics.
            
        Returns:
            str: A randomly selected statistic message.
        """
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
            
            lambda: f"There are {STATS.get('nrOfDodos', 0)} dodos, c4 dodo raid?",
            
            lambda: f"There have been {STATS.get('nrOfDeaths', 0)} deaths, RIP!",
            
            lambda: f"Our combined level is {STATS.get('combinedLevel', 0)}, APES TOGETHER STRONG!",
            
            lambda: (
                f"There are {STATS.get('nrOfTamedDinos', 0)} tamed dinos walking around, make sure they are fed!"
                if STATS.get('nrOfTamedDinos', 0) > 0
                else ""
            ),
            
            lambda: (
                f"{STATS['highestDeaths'][0].player_data.name} has the most deaths: {STATS['highestDeaths'][1]}.. Git gud, scrub!"
                if 'highestDeaths' in STATS and STATS['highestDeaths']
                else ""
            ),
            
            lambda: (
                f"{STATS['highestLevel'][0].player_data.name} has the highest level: {STATS['highestLevel'][1]}.. Take a break man!"
                if 'highestLevel' in STATS and STATS['highestLevel']
                else ""
            ),
            
            lambda: (
                f"We placed {STATS.get('nrOfMetalStructures', 0)} metal structures, time to upgrade to tek?"
                if STATS.get('nrOfMetalStructures', 0) > 0
                else ""
            ),
            
            lambda: (
                f"We placed {STATS.get('nrOfTekStructures', 0)} tek structures, waste of resources, goddamn"
                if STATS.get('nrOfTekStructures', 0) > 0
                else ""
            ),
            
            lambda: (
                f"We placed {STATS.get('nrOfStoneStructures', 0)} stone structures, clean up your taming pens pls"
                if STATS.get('nrOfStoneStructures', 0) > 0
                else ""
            ),
            lambda: f"We gathered {STATS.get('randomResourceAmount', 0)} units of {STATS.get('randomResourceName', 0)}",
            lambda: (
                "Not a single turret on the map, smoooooth sailing"
                if STATS.get('nrOfTurrets', 0) == 0
                else f"There are currently {STATS.get('nrOfTurrets', 0)} turrets placed on the map, careful ;)"
                if STATS.get('nrOfTurrets', 0) > 1
                else "There is a turret on the map, it's getting real!"
            )
        ]
        
        # Generate all possible messages
        all_messages = [option() for option in options]
        
        # Filter out any empty strings
        valid_messages = [msg for msg in all_messages if msg]
        
        if not valid_messages:
            return "No valid statistics available to display."
        
        # Randomly select and return one of the valid messages
        return random.choice(valid_messages)

