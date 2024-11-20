from arkparse.ftp.ark_ftp_client import ArkFtpClient, ArkFile, ArkMaps
from pathlib import Path
from arkparse.api.dino_api import DinoApi
from arkparse.api.player_api import PlayerApi
from arkparse.api.rcon_api import RconApi
from arkparse.api.structure_api import StructureApi
from arkparse.objects.saves.asa_save import AsaSave
from arkparse.classes.dinos import Dinos
from arkparse.classes.placed_structures import PlacedStructures
import random

from .__manager import Manager


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
    # "amountOfResource" : None,
    "nrOfTamedDinos" : None,
    "highestDeaths" : None,
    "highestLevel" : None,
    "nrOfMetalStructures" : None,
    "nrOfTekStructures" : None,
    "nrOfStoneStructures" : None,
    "nrOfTurrets" : None,
}

class RandomStatManager(Manager):
    
    def __init__(self, ftp_config: ArkFtpClient, rconapi: RconApi):
        super().__init__(self.__process, "random stat manager")
        self.previous_save: ArkFile = None
        self.ftp_client: ArkFtpClient = ArkFtpClient.from_config(ftp_config, ArkMaps.ABERRATION)
        self.player_api: PlayerApi = PlayerApi(self.ftp_client)
        self.rcon: RconApi = rconapi

    def stop(self):
        super().stop()
        self.ftp_client.close()

    def __process(self, interval: int):
        save_file_info : ArkFile = self.ftp_client.check_save_file()[0]

        if self.previous_save is None or save_file_info.is_newer_than(self.previous_save):
            print("New save file detected, downloading...")
            self.previous_save = save_file_info
            save_path = self.ftp_client.download_save_file("Aberration_WP.ark", Path.cwd())

            print("Parsing files...")
            save = AsaSave(save_path)
            dino_api = DinoApi(save)
            structure_api = StructureApi(save)

            STATS["nrOfDinosOnMap"] = len(dino_api.get_all_wild())
            STATS["nrOfLv150"] = len(dino_api.get_all_filtered(150, 150, None, False))
            STATS["nrOfAlphas"] = len(dino_api.get_all_wild_by_class([Dinos.alpha_karkinos, Dinos.alpha_reaper_king, Dinos.alpha_basilisk]))
            STATS["isThereAlphaReaper"] = len(dino_api.get_all_wild_by_class([Dinos.alpha_reaper_king])) > 0
            STATS["isThereAlphaBasilisk"] = len(dino_api.get_all_wild_by_class([Dinos.alpha_basilisk])) > 0
            STATS["isThereAlphaKark"] = len(dino_api.get_all_wild_by_class([Dinos.alpha_karkinos])) > 0
            STATS["nrOfReapersAbove130"] = len(dino_api.get_all_filtered(130, None, Dinos.reaper_queen, False))
            STATS["nrOfDodos"] = len(dino_api.get_all_wild_by_class([Dinos.abberant.dodo]))
            STATS["nrOfDeaths"] = self.player_api.get_deaths()
            STATS["combinedLevel"] = self.player_api.get_level()
            # "amountOfResource" : None,
            STATS["nrOfTamedDinos"] = len(dino_api.get_all_tamed())
            STATS["highestDeaths"] = self.player_api.get_player_with(PlayerApi.Stat.DEATHS, PlayerApi.StatType.HIGHEST)
            STATS["highestLevel"] = self.player_api.get_player_with(PlayerApi.Stat.LEVEL, PlayerApi.StatType.HIGHEST)
            STATS["nrOfMetalStructures"] = structure_api.get_response_total_count(structure_api.get_by_class(PlacedStructures.metal.all_bps))
            STATS["nrOfTekStructures"] = structure_api.get_response_total_count(structure_api.get_by_class(PlacedStructures.tek.all_bps))
            STATS["nrOfStoneStructures"] = structure_api.get_response_total_count(structure_api.get_by_class(PlacedStructures.stone.all_bps))
            STATS["nrOfTurrets"] = structure_api.get_response_total_count(structure_api.get_by_class(PlacedStructures.turrets.all_bps))

        self.rcon.send_message(self.get_random_stat(STATS))

    def get_random_stat(self, STATS):
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
            
            lambda: (
                f"Is there an alpha reaper? Survey says... {'YESS!!' if STATS.get('isThereAlphaReaper', False) else 'Nope! (at least not yet)'}"
            ),
            
            lambda: (
                f"Is there an alpha basilisk? Survey says... {'YESS!!' if STATS.get('isThereAlphaBasilisk', False) else 'Nope! (at least not yet)'}"
            ),
            
            lambda: (
                f"Is there an alpha karkinos? Survey says... {'YESS!!' if STATS.get('isThereAlphaKark', False) else 'Nope! (at least not yet)'}"
            ),
            
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

