import json
import argparse
import os
from pathlib import Path

from arkparse.ftp.ark_ftp_client import ArkFtpClient, ArkMap
from arkparse.api.player_api import PlayerApi
from arkparse import ArkPlayer

argparser = argparse.ArgumentParser()
argparser.add_argument("--reset_playtime", action="store_true")
args = argparser.parse_args()

# FTP = ArkFtpClient.from_config("../ftp_config.json", ArkMap.ABERRATION)
PLAYER_API = PlayerApi("../ftp_config.json", ArkMap.ABERRATION)

# Get real life names
players = {}
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
            playtimes[player_id] = prev_players[player_id]["playtime"]


for player in PLAYER_API.players:
    player: ArkPlayer = player
    players[player.unique_id] = {
        "steam_name": player.name,
        "char_name": player.char_name,
        "id": player.id_,
        "playtime": 0,
        "tribe": player.tribe
    }

    # Add real name if available
    if player.unique_id in player_ids_to_name:
        players[player.unique_id]["real_name"] = player_ids_to_name[player.unique_id]

    # Add current playtime if available
    if player.unique_id in playtimes:
        players[player.unique_id]["playtime"] = playtimes[player.unique_id]

with open("../players.json", 'w') as f:
    json.dump(players, f, indent=4)

    