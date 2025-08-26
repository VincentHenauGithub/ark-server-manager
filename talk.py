from arkparse.api.rcon_api import RconApi

rcon: RconApi = RconApi.from_config("rcon_config.json")


rcon.send_message("RIP")