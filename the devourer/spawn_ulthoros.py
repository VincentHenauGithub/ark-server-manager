
from pathlib import Path
from arkparse import AsaSave
from arkparse.enums import ArkStat, ArkMap
from arkparse.api import EquipmentApi, PlayerApi, DinoApi
from arkparse.parsing.struct import ActorTransform, ArkVector, ArkRotator
from arkparse.ftp.ark_ftp_client import ArkFtpClient
from arkparse.object_model.misc.dino_owner import DinoOwner
from arkparse.object_model.dinos.tamed_dino import TamedDino
from loot_configuration import add_loot

# store_path = Path("D:\\SteamLibrary\\steamapps\\common\\ARK Survival Ascended\\ShooterGame\\Saved\\SavedArksLocal\\Ragnarok_WP\\Ragnarok_WP.ark")
# save_path = Path("D:\\SteamLibrary\\steamapps\\common\\ARK Survival Ascended\\ShooterGame\\Saved\\SavedArksLocal\\Ragnarok_WP\\_Ragnarok_WP.ark")

spawn = ActorTransform(vector=ArkVector(x=-628340, y=-630649, z=77636), rotator=ArkRotator(yaw=-0.0001, roll=0.38))
path = Path.cwd() / "dodow"
# save = AsaSave(save_path)
ftp_client = ArkFtpClient.from_config("../ftp_config.json", ArkMap.RAGNAROK)
save = AsaSave(contents=ftp_client.download_save_file(map=ArkMap.RAGNAROK), read_only=False)
d_api = DinoApi(save)
e_api = EquipmentApi(save)
p_api = PlayerApi(save)

# owner = DinoOwner()
# owner.set_tribe(p_api.generate_tribe_id(), "The end of worlds")
# owner.set_player(p_api.generate_player_id(), "The Admin")

# dino: TamedDino = d_api.import_dino(path, spawn)
# dino.disable_wandering()
# dino.set_name("Ulthoros, the Devourer")
# dino.stats.set_levels(43, ArkStat.HEALTH)
# dino.stats.set_tamed_levels(255, ArkStat.HEALTH)
# dino.stats.set_levels(255, ArkStat.MELEE_DAMAGE)
# dino.stats.set_tamed_levels(255, ArkStat.MELEE_DAMAGE)
# dino.stats.set_levels(255, ArkStat.WEIGHT)
# dino.stats.set_tamed_levels(255, ArkStat.WEIGHT)
# dino.stats.set_levels(255, ArkStat.STAMINA)
# dino.stats.set_tamed_levels(255, ArkStat.STAMINA)
# dino.set_owner(owner)
# dino.heal()


# add_loot(None, 100, save, dino, e_api, mixed=True)

# save.store_db(store_path)
save.store_db(Path.cwd() / "Ragnarok_WP.ark")
# print("Removing old save file from FTP...")
# ftp_client.remove_save_file(ArkMap.RAGNAROK)
# print("Uploading new save file to FTP...")
# ftp_client.upload_save_file(Path.cwd() / "Ragnarok_WP.ark", map=ArkMap.RAGNAROK)
# print("Save file uploaded successfully.")