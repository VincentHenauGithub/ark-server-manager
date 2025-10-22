import json
import argparse
import os
from pathlib import Path

from arkparse.ftp.ark_ftp_client import ArkFtpClient, ArkMap
from arkparse.api.player_api import PlayerApi
from arkparse import AsaSave
from arkparse.player.ark_player import ArkPlayer
from arkparse.logging import ArkSaveLogger

argparser = argparse.ArgumentParser()
argparser.add_argument("--reset_playtime", action="store_true")
args = argparser.parse_args()

save_path = ArkFtpClient.from_config('../ftp_config.json', ArkMap.RAGNAROK).download_save_file(Path.cwd()) # download the save file from an FTP server
save_path = Path.cwd() / "Ragnarok_WP.ark"                                                                    # Or use a local path

save = AsaSave(save_path)  
# ArkSaveLogger.enable_debug = True
# FTP = ArkFtpClient.from_config("../ftp_config.json", ArkMap.RAGNAROK)
PLAYER_API = PlayerApi(save, ArkMap.RAGNAROK)
for player in PLAYER_API.players:
    player: ArkPlayer = player
    print(f"Player {player.name} with ID {player.unique_id} and tribe {player.tribe} found")

# Get real life names
if os.path.exists("../player_id_to_name.json"):
    with open("../player_id_to_name.json", 'r') as f:
        player_ids_to_name = json.load(f)
else:
    player_ids_to_name = {}

# Retrieve playtimes
playtimes = {}
if os.path.exists("../players.json"):
    with open("../players.json", 'r') as f:
        prev_players = json.load(f)
        for player_id in prev_players:
            playtimes[player_id] = prev_players[player_id].get("playtime", 0)


for player in PLAYER_API.players:
    player: ArkPlayer = player
    prev_players[player.unique_id] = {
        "steam_name": player.name,
        "char_name": player.char_name,
        "id": player.id_,
        "playtime": 0,
        "tribe": player.tribe
    }

    # Add real name if available
    if player.unique_id in player_ids_to_name:
        prev_players[player.unique_id]["real_name"] = player_ids_to_name[player.unique_id]

    # Add current playtime if available
    if player.unique_id in playtimes:
        prev_players[player.unique_id]["playtime"] = playtimes[player.unique_id]

    print(f"Retrieved player {player.name} with ID {player.unique_id} and playtime {prev_players[player.unique_id]['playtime']}")

with open("../players.json", 'w') as f:
    json.dump(prev_players, f, indent=4)

    