import json
import argparse
import os

from arkparse.ftp.ark_ftp_client import ArkFtpClient, ArkMaps
from arkparse.api.player_api import PlayerApi
from arkparse.objects.player.ark_profile import ArkProfile

argparser = argparse.ArgumentParser()
argparser.add_argument("--reset_playtime", action="store_true")
args = argparser.parse_args()

FTP = ArkFtpClient.from_config("../ftp_config.json", ArkMaps.ABERRATION)
PLAYER_API = PlayerApi(FTP)

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
    player: ArkProfile = player
    players[player.player_data.unique_id] = {
        "steam_name": player.player_data.name,
        "char_name": player.player_data.char_name,
        "id": player.player_data.id_,
        "playtime": 0,
        "tribe": player.player_data.tribe
    }

    # Add real name if available
    if player.player_data.unique_id in player_ids_to_name:
        players[player.player_data.unique_id]["real_name"] = player_ids_to_name[player.player_data.unique_id]

    # Add current playtime if available
    if player.player_data.unique_id in playtimes:
        players[player.player_data.unique_id]["playtime"] = playtimes[player.player_data.unique_id]

with open("../players.json", 'w') as f:
    json.dump(players, f, indent=4)

    