from pathlib import Path
import json

path = Path("C:\\Users\\Vincent\\AppData\\Local\\Temp\\.net\\ASA_Save_Inspector\\qv1RdhHoeNmT1qqljSPbHV4RkAGrRAA=\\data") / "json_exports" / "2_Ragnarok"

item_json = path  / "items.json"
dino_json = path / "dinos.json"
structure_json = path / "structures.json"

dinos = {}
items = {}
structures = {}
with open(dino_json, 'r') as f:
    dinos = json.load(f)

with open(item_json, 'r') as f:
    items = json.load(f)

with open(structure_json, 'r') as f:
    structures = json.load(f)

for item in dinos:
    item["DinoID1"] = int(item["DinoID1"])
    item["DinoID2"] = int(item["DinoID2"])
    if item["DinoID1"] > (2 ** 31 - 1):
        item["DinoID1"] = int(item["DinoID1"] / 2)
    if item["DinoID2"] > (2 ** 31 - 1):
        item["DinoID2"] = int(item["DinoID2"] / 2)

for item in items:
    if "ItemID" not in item:
        continue
    item["ItemID"]["ItemID1"] = int(item["ItemID"]["ItemID1"])
    item["ItemID"]["ItemID2"] = int(item["ItemID"]["ItemID2"])
    if item["ItemID"]["ItemID1"] > (2 ** 31 - 1):
        item["ItemID"]["ItemID1"] = int(item["ItemID"]["ItemID1"] / 2)
    if item["ItemID"]["ItemID2"] > (2 ** 31 - 1):
        item["ItemID"]["ItemID2"] = int(item["ItemID"]["ItemID2"] / 2)

for item in structures:
    if "StructureID" not in item:
        continue
    if item["StructureID"] is None:
        item["StructureID"] = 0
    if item["StructureID"] >= (2 ** 31 - 1):
        item["StructureID"] = int(item["StructureID"] / 2)

with open(dino_json, 'w') as f:
    json.dump(dinos, f, indent=4)

with open(item_json, 'w') as f:
    json.dump(items, f, indent=4)

with open(structure_json, 'w') as f:
    json.dump(structures, f, indent=4)