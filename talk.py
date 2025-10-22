from arkparse.api.rcon_api import RconApi

rcon: RconApi = RconApi.from_config("rcon_config.json")

resp = rcon.send_cmd("DestroyWildDinos")
print(resp)
rcon.send_message("tst")