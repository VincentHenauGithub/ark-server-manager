from pathlib import Path
from uuid import UUID
from typing import Dict
import json

from arkparse import AsaSave, Classes
from arkparse.api import StructureApi
from arkparse.ftp import ArkFtpClient
from arkparse.enums import ArkMap
from arkparse.utils import draw_heatmap
from arkparse.object_model.structures import Structure

# retrieve the save file (can also retrieve it from a local path)
save_path = ArkFtpClient.from_config(Path("../ftp_config.json"), ArkMap.RAGNAROK).download_save_file(Path.cwd())
save = AsaSave(save_path)

min_in_section = 1

structure_api = StructureApi(save)
all_structures: Dict[UUID, Structure] = structure_api.get_all()


# seperate_owners = {}

# for key, structure in all_structures.items():
#     # remove invalid structures (e.g., foundations without supports)
#     if structure.owner.tribe_id not in seperate_owners:
#         seperate_owners[structure.owner.tribe_id] = {
#             "count": 0,
#             "name": "Unknown"
#         }

#     if structure.owner.tribe_name:
#         seperate_owners[structure.owner.tribe_id]["name"] = structure.owner.tribe_name
#     seperate_owners[structure.owner.tribe_id]["count"] += 1

# print(json.dumps(seperate_owners, indent=4))



to_be_removed = [
    "Turok",
    "De bad hoertjes",  
    "The beach bobs",
    "Barthen's provisions and cheater rolls",
    "Embers of the searing blaaaaaze",
    "Beelzebufo boys",
    "Pyropussies",
    "Mesh masters",
    "The administration",
    "The Ascended",
    "Lya's Court"
]

for key, structure in all_structures.items():
    # remove invalid structures (e.g., foundations without supports)
    if structure.owner.tribe_name in to_be_removed:
        structure.remove_from_save(save)

save.store_db(Path.cwd() / "Ragnarok_WP.ark")