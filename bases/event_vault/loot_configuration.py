import random
from typing import List
from uuid import UUID

from arkparse import Classes
from arkparse import AsaSave
from arkparse.api import EquipmentApi
from arkparse.object_model.equipment import Armor, Saddle, Weapon, Shield
from arkparse.object_model.stackables import Resource
from arkparse.object_model.structures import StructureWithInventory
from arkparse.enums import ArkEquipmentStat

STACK_MULTIPLIER = 50

STACK_SIZES = {
    # Basic resources
    Classes.resources.Basic.black_pearl:      200,
    Classes.resources.Basic.chitin:           100,
    Classes.resources.Basic.silica_pearl:     100,
    Classes.resources.Basic.crystal:          100,
    Classes.resources.Basic.polymer_organic:   20,
    Classes.resources.Basic.rare_mushroom:    100,
    Classes.resources.Basic.rare_flower:      100,
    Classes.resources.Basic.oil:              100,
    Classes.resources.Basic.fiber:            300,
    Classes.resources.Basic.hide:             200,
    Classes.resources.Basic.pelt:             200,
    Classes.resources.Basic.stone:            100,
    Classes.resources.Basic.wood:             100,
    Classes.resources.Basic.flint:            100,
    Classes.resources.Basic.thatch:           200,
    Classes.resources.Basic.fungal_wood:      100,
    Classes.resources.Basic.keratin:          100,
    Classes.resources.Basic.metal:            200,
    Classes.resources.Basic.clay:             100,
    Classes.resources.Basic.blue_gem:         100,
    Classes.resources.Basic.red_gem:          100,
    Classes.resources.Basic.green_gem:        100,
    Classes.resources.Basic.gas:              100,
    Classes.resources.Basic.obsidian:         100,
    Classes.resources.Basic.sap:               30,
    Classes.resources.Basic.element:          100,
    Classes.resources.Basic.element_shard:   1000,

    # Crafted resources
    Classes.resources.Crafted.electronics:     100,
    Classes.resources.Crafted.metal_ingot:     200,
    Classes.resources.Crafted.gunpowder:       100,
    Classes.resources.Crafted.charcoal:        100,
    Classes.resources.Crafted.preserving_salt:   6,
    Classes.resources.Crafted.polymer:         100,
    Classes.resources.Crafted.gasoline:        100,
    Classes.resources.Crafted.sparkpowder:     100,
    Classes.resources.Crafted.propellant:      100,
    Classes.resources.Crafted.absorbent_substrate: 100,
}

RESOURCE_LOOT_TABLES = {
    "starter": [
        Classes.resources.Basic.fungal_wood,
        Classes.resources.Basic.fiber,
        Classes.resources.Basic.flint,
        Classes.resources.Basic.hide,
        Classes.resources.Basic.chitin,
        Classes.resources.Basic.keratin,
        Classes.resources.Basic.metal,
        Classes.resources.Basic.pelt,
        Classes.resources.Basic.stone,
        Classes.resources.Basic.thatch,
        Classes.resources.Basic.wood,
        Classes.resources.Basic.clay,
        Classes.resources.Crafted.charcoal,
    ],
    "medium": [
        Classes.resources.Basic.blue_gem,
        Classes.resources.Basic.red_gem,
        Classes.resources.Basic.green_gem,
        Classes.resources.Basic.gas,
        Classes.resources.Basic.obsidian,
        Classes.resources.Basic.rare_flower,
        Classes.resources.Basic.rare_mushroom,
        Classes.resources.Basic.crystal,
        Classes.resources.Basic.oil,
        Classes.resources.Basic.silica_pearl,
        Classes.resources.Basic.sap,
        Classes.resources.Crafted.gasoline,
        Classes.resources.Crafted.gunpowder,
        Classes.resources.Crafted.metal_ingot,
        Classes.resources.Crafted.sparkpowder,
        Classes.resources.Crafted.propellant,
        Classes.resources.Crafted.absorbent_substrate,
    ],
    "advanced": [
        Classes.resources.Basic.polymer_organic,
        Classes.resources.Crafted.electronics,
        Classes.resources.Crafted.polymer,
    ],
    "endgame": [
        Classes.resources.Basic.black_pearl,
    ],
    "alpha": [
        Classes.resources.Basic.element,
        Classes.resources.Basic.element_shard,
    ],
}

SADDLE_LOOT_TABLES = {
    "starter_only": [
        Classes.equipment.saddles.baryonyx,
        Classes.equipment.saddles.beelzebufo,
        Classes.equipment.saddles.bronto,
        Classes.equipment.saddles.bronto_platform,
        Classes.equipment.saddles.carno,
        Classes.equipment.saddles.castoroides,
        Classes.equipment.saddles.allo,
        Classes.equipment.saddles.dire_bear,
        Classes.equipment.saddles.doedi,
        Classes.equipment.saddles.equus,
        Classes.equipment.saddles.dolphin,
        Classes.equipment.saddles.iguanodon,
        Classes.equipment.saddles.kaprosuchus,
        # Classes.equipment.saddles.lymantria,
        Classes.equipment.saddles.mammoth,
        Classes.equipment.saddles.manta,
        Classes.equipment.saddles.megalania,
        Classes.equipment.saddles.parasaur,
        Classes.equipment.saddles.pelagornis,
        Classes.equipment.saddles.procoptodon,
        Classes.equipment.saddles.pulmonoscorpius,
        Classes.equipment.saddles.raptor,
        Classes.equipment.saddles.sabertooth,
        Classes.equipment.saddles.sarco,
        Classes.equipment.saddles.terror_bird,
        Classes.equipment.saddles.thorny_dragon,
        Classes.equipment.saddles.thylacoleo,
        Classes.equipment.saddles.xiphactinus,
    ],
    "starter": [
        Classes.equipment.saddles.ankylo,
        Classes.equipment.saddles.archelon,
        Classes.equipment.saddles.argentavis,
        Classes.equipment.saddles.deinosuchus,
        Classes.equipment.saddles.bison,
        Classes.equipment.saddles.megalodon,
        Classes.equipment.saddles.pachyrhino,
        Classes.equipment.saddles.ptero,
    ],
    "medium": [
        Classes.equipment.saddles.arthro,
        Classes.equipment.saddles.basilo,
        Classes.equipment.saddles.fasolasuchus,
        Classes.equipment.saddles.mantis,
        Classes.equipment.saddles.megalosaurus,
        Classes.equipment.saddles.megatherium,
        Classes.equipment.saddles.plesiosaur,
        Classes.equipment.saddles.therizinosaurus,
        Classes.equipment.saddles.rhino,
        Classes.equipment.saddles.ceratosaurus,
    ],
    "advanced": [
        Classes.equipment.saddles.carbo,
        Classes.equipment.saddles.deinotherium,
        Classes.equipment.saddles.daeodon,
        Classes.equipment.saddles.dunkleosteus,
        Classes.equipment.saddles.mosa,
        Classes.equipment.saddles.mosa_platform,
        Classes.equipment.saddles.paracer,
        Classes.equipment.saddles.paracer_platform,
        Classes.equipment.saddles.rex,
        Classes.equipment.saddles.quetz,
        Classes.equipment.saddles.spino,
        Classes.equipment.saddles.stego,
        Classes.equipment.saddles.tapejara,
        Classes.equipment.saddles.trike,
        Classes.equipment.saddles.yuty,
    ],
    "endgame": [
        Classes.equipment.saddles.carcha,
        Classes.equipment.saddles.giga,
        Classes.equipment.saddles.karkinos,
        Classes.equipment.saddles.rhynio,
        Classes.equipment.saddles.rock_golem,
        Classes.equipment.saddles.tuso,
    ],
}

WEAPON_LOOT_TABLES = {
    "starter_only": [
        Classes.equipment.weapons.gathering.sickle,
        Classes.equipment.misc.climb_pick,
        Classes.equipment.weapons.primitive.pike,
        Classes.equipment.weapons.primitive.simple_pistol,
    ],
    "starter": [
        Classes.equipment.weapons.primitive.crossbow,
        Classes.equipment.weapons.advanced.fabricated_pistol,
        Classes.equipment.weapons.advanced.assault_rifle,
        Classes.equipment.weapons.primitive.sword,
        Classes.equipment.shield.metal,
        Classes.equipment.weapons.primitive.stone_club,
    ],
    "medium": [
        Classes.equipment.misc.harpoon,
        Classes.equipment.weapons.gathering.metal_pick,
        Classes.equipment.weapons.gathering.metal_hatchet,
        Classes.equipment.weapons.advanced.longneck,
    ],
    "advanced": [
        Classes.equipment.weapons.advanced.chainsaw,
        Classes.equipment.shield.riot,
        Classes.equipment.weapons.advanced.flamethrower,
    ],
    "endgame": [
        Classes.equipment.weapons.advanced.fabricated_shotgun,
        Classes.equipment.weapons.advanced.compound_bow,
        Classes.equipment.weapons.advanced.fabricated_sniper,
    ]
}

ARMOR_LOOT_TABLES = {
    "starter": [
        Classes.equipment.armor.chitin.shirt,
        Classes.equipment.armor.chitin.pants,
        Classes.equipment.armor.chitin.helmet,
        Classes.equipment.armor.chitin.boots,
        Classes.equipment.armor.chitin.gloves,
        Classes.equipment.armor.ghillie.shirt,
        Classes.equipment.armor.ghillie.pants,
        Classes.equipment.armor.ghillie.helmet,
        Classes.equipment.armor.ghillie.boots,
        Classes.equipment.armor.ghillie.gloves
    ],
    "raider": [
        Classes.equipment.armor.flak.shirt,
        Classes.equipment.armor.flak.pants,
        Classes.equipment.armor.flak.helmet,
        Classes.equipment.armor.flak.boots,
        Classes.equipment.armor.flak.gloves,
        Classes.equipment.shield.riot,
    ],
    "explorer": [
        Classes.equipment.armor.riot.pants,
        Classes.equipment.armor.riot.helmet,
        Classes.equipment.armor.riot.boots,
        Classes.equipment.armor.riot.gloves,
        Classes.equipment.armor.riot.shirt,
        Classes.equipment.armor.hazard.shirt,
        Classes.equipment.armor.hazard.pants,
        Classes.equipment.armor.hazard.helmet,
        Classes.equipment.armor.hazard.boots,
        Classes.equipment.armor.hazard.gloves,
        Classes.equipment.shield.metal,
        Classes.equipment.armor.scuba.chest,
        Classes.equipment.armor.scuba.pants,
        Classes.equipment.armor.scuba.flippers,
        Classes.equipment.armor.scuba.goggles,
    ]
}

LOOT_DISTRIBUTIONS = [
    {
      "min_turrets": 0,
      "max_turrets": 15,
      "mixed": False,
      "saddles": {
        "starter_only": [1.1, 12.0],
        "starter": [1.1, 4.63]
      },
      "weapons": {
        "starter_only": [175, 225],
        "starter": [150, 200]
      },
      "resources": {
        "starter": [1000, 3000],
        "medium": [500, 1000]
      },
      "armor": {
        "starter": [1.5, 9.5],
        "raider": [1.5, 4.0],
        "explorer": [1.5, 4.0]
      }
    },
    {
      "min_turrets": 15,
      "max_turrets": 30,
      "mixed": False,
      "saddles": {
        "starter_only": [10.0, 19.5],
        "starter": [4.63, 12.0],
        "medium": [1.1, 4.63]
      },
      "weapons": {
        "starter_only": [225, 325],
        "starter": [200, 250],
        "medium": [150, 200]
      },
      "resources": {
          "starter": [2000, 5000],
          "medium": [1000, 2000],
          "advanced": [500, 1000]
      },
      "armor": {
        "starter": [7.0, 10.0],
        "raider": [2.5, 5.5],
        "explorer": [2.5, 5.5]
      }
      
    },
    {
      "min_turrets": 30,
      "max_turrets": 40,
      "mixed": False,
      "saddles": {
        "starter_only": [17.5, 21.3],
        "starter": [8.33, 17.59],
        "medium": [4.63, 12.0]
      },
      "weapons": {
        "starter": [250, 325],
        "medium": [200, 250],
        "advanced": [150, 200],
        "endgame": [150, 200]
      },
      "resources": {
          "starter": [3000, 6000],
          "medium": [2000, 4000],
          "advanced": [1000, 2000]
      },
      "armor": {
        "starter": [10.0, 13.0],
        "raider": [4.0, 9.5],
        "explorer": [4.0, 9.5]
      }
    },
    {
      "min_turrets": 40,
      "max_turrets": 50,
      "mixed": False,
      "saddles": {
        "starter": [13.89, 21.3],
        "medium": [8.33, 17.59],
        "advanced": [1.1, 4.63]
      },
      "weapons": {
        "medium": [225, 325],
        "advanced": [200, 325],
        "endgame": [150, 225]
      },
        "resources": {
            "starter": [8000, 15000],
            "medium": [5000, 10000],
            "advanced": [3000, 5000]
        },
      "armor": {
        "starter": [13.0, 25.0],
        "raider": [6.0, 12.0],
        "explorer": [6.0, 12.0]
      }
    },
    {
        "min_turrets": 50,
        "max_turrets": 75,
        "mixed": False,
        "saddles": {
          "medium": [13.89, 21.3],
          "advanced": [4.63, 12.0],
          "endgame": [1.1, 4.63]
        },
        "weapons": {
          "medium": [275, 325],
          "advanced": [200, 325],
          "endgame": [150, 225]
        },
        "resources": {
            "starter": [15000, 25000],
            "medium": [10000, 20000],
            "advanced": [2000, 5000]
        },
      "armor": {
        "raider": [9.0, 14.0],
        "explorer": [9.0, 14.0]
      }
    },
    {
      "min_turrets": 50,
      "max_turrets": 75,
      "mixed": True,
      "saddles": {
        "advanced": [8.33, 17.59],
        "endgame": [4.63, 12.0]
      },
      "weapons": {
        "advanced": [250, 325],
        "endgame": [200, 250]
      },
        "resources": {
            "starter": [20000, 30000],
            "medium": [15000, 25000],
            "advanced": [5000, 7500],
            "endgame": [500, 500]
        },
      "armor": {
        "raider": [11.0, 18.0],
        "explorer": [11.0, 18.0]
      }
    },
    {
      "min_turrets": 75,
      "max_turrets": 100,
      "mixed": False,
      "saddles": {
        "advanced": [13.89, 21.3],
        "endgame": [8.33, 17.59]
      },
      "weapons": {
        "advanced": [275, 325],
        "endgame": [250, 275]
      },
        "resources": {
            "starter": [30000, 50000],
            "medium": [25000, 35000],
            "advanced": [10000, 15000],
            "endgame": [1000, 1000],
            "alpha": [1, 100]
        },
      "armor": {
        "raider": [14.0, 22.0],
        "explorer": [14.0, 22.0]
      }
    },
    {
      "min_turrets": 75,
      "max_turrets": 100,
      "mixed": True,
      "saddles": {
        "advanced": [19.45, 21.3],
        "endgame": [13.89, 21.3]
      },
      "weapons": {
        "endgame": [275, 325]
      },
        "resources": {
            "starter": [50000, 100000],
            "medium": [40000, 60000],
            "advanced": [25000, 50000],
            "endgame": [4000, 4000],
            "alpha": [50, 300]
        },
      "armor": {
        "raider": [16.0, 26.0]
      }
    }
  ]


def _get_loot_distribution(turrets: int) -> dict:
    """
    Returns the loot distribution based on the number of turrets.
    """
    for distribution in LOOT_DISTRIBUTIONS:
        if distribution["min_turrets"] <= turrets <= distribution["max_turrets"]:
            return distribution
    return None

def _get_random_category() -> str:
    """
    Returns a random loot category.
    """
    categories = ["saddles", "weapons", "resources", "armor"]
    return random.choice(categories)

def _get_saddle_loot(distribution: dict, equipment_api: EquipmentApi):
    """
    Returns a random saddle and its chance based on the distribution.
    """
    keys = list(distribution["saddles"].keys())
    random_key = random.choice(keys)
    range_ = distribution["saddles"][random_key]
    get_random_bp = random.choice(SADDLE_LOOT_TABLES[random_key])
    # print(get_random_bp)

    saddle: Saddle = equipment_api.generate_equipment(
        EquipmentApi.Classes.SADDLE,
        get_random_bp,
        ArkEquipmentStat.ARMOR,
        min_value=range_[0],
        max_value=range_[1],
        from_rating=True,
        bp_chance=0.15
    )

    return saddle

def _get_weapon_loot(distribution: dict, equipment_api: EquipmentApi) -> Weapon:
    """
    Returns a random weapon and its chance based on the distribution.
    """
    keys = list(distribution["weapons"].keys())
    random_key = random.choice(keys)
    range_ = distribution["weapons"][random_key]
    get_random_bp = random.choice(WEAPON_LOOT_TABLES[random_key])

    weapon: Weapon = equipment_api.generate_equipment(
        EquipmentApi.Classes.WEAPON,
        get_random_bp,
        ArkEquipmentStat.DAMAGE,
        min_value=range_[0],
        max_value=range_[1],
        bp_chance=0.15
    )

    return weapon

def _get_armor_loot(distribution: dict, equipment_api: EquipmentApi):
    """
    Returns a random armor piece and its chance based on the distribution.
    """
    keys = list(distribution["armor"].keys())
    random_key = random.choice(keys)
    range_ = distribution["armor"][random_key]
    get_random_bp = random.choice(ARMOR_LOOT_TABLES[random_key])

    if get_random_bp in Classes.equipment.shield.all_bps:
        shield: Shield = equipment_api.generate_equipment(
            EquipmentApi.Classes.SHIELD,
            get_random_bp,
            ArkEquipmentStat.DURABILITY,
            min_value=range_[0],
            max_value=range_[1],
            from_rating=True,
            bp_chance=0.15
        )
        return shield
    else:
        armor: Armor = equipment_api.generate_equipment(
            EquipmentApi.Classes.ARMOR,
            get_random_bp,
            ArkEquipmentStat.ARMOR,
            min_value=range_[0],
            max_value=range_[1],
            from_rating=True,
            bp_chance=0.15
        )

        return armor

def _get_resource_loot(distribution: dict, save: AsaSave, vault_id: UUID) -> List[Resource]:
    """
    Returns a list of random resources and their chances based on the distribution.
    """
    resources = []
    keys = list(distribution["resources"].keys())
    random_key = random.choice(keys)
    range_ = distribution["resources"][random_key]
    
    for _ in range(6):
        full_amount = random.uniform(range_[0], range_[1])
        bp = random.choice(RESOURCE_LOOT_TABLES[random_key])
        stack_size = STACK_SIZES.get(bp) * STACK_MULTIPLIER
        while full_amount > stack_size:
            full_amount -= stack_size
            resource: Resource = Resource.generate_from_template(bp, save, vault_id)
            resource.set_quantity(stack_size)
            resources.append(resource)

        resource: Resource = Resource.generate_from_template(bp, save, vault_id)
        resource.set_quantity(int(full_amount))
        resources.append(resource)

    return resources


def add_loot(raid_base_manager, turrets: int, save: AsaSave, vault: StructureWithInventory, equipment_api: EquipmentApi, mixed: bool = False) -> None:
    """
    Generates loot based on the number of turrets.
    """
    distribution = _get_loot_distribution(turrets)
    if not distribution:
        raise ValueError(f"No loot distribution found for {turrets} turrets")

    loot: List[Resource | Armor | Weapon | Saddle | Shield] = []
    for _ in range(6):
        category = _get_random_category()
        if category == "saddles":
            s: Saddle = _get_saddle_loot(distribution, equipment_api)
            loot.append(s)
            if raid_base_manager:
                raid_base_manager._print(f"Added saddle: {s.get_short_name()} with armor {s.armor:.2f} and durability {s.durability:.2f}")
        elif category == "weapons":
            w: Weapon = _get_weapon_loot(distribution, equipment_api)
            loot.append(w)
            if raid_base_manager:
                raid_base_manager._print(f"Added weapon: {w.get_short_name()} with damage {w.damage:.2f} and durability {w.durability:.2f}")
        elif category == "resources":
            loot.extend(_get_resource_loot(distribution, save, vault.object.uuid))
        elif category == "armor":
            a_o_s: Armor | Shield = _get_armor_loot(distribution, equipment_api)
            if isinstance(a_o_s, Shield):
                s: Shield = a_o_s
                if raid_base_manager:
                  raid_base_manager._print(f"Added shield: {s.get_short_name()} with durability {s.durability:.2f}")
            else:
                a: Armor = a_o_s
                if raid_base_manager:
                    raid_base_manager._print(f"Added armor: {a.get_short_name()} with armor {a.armor:.2f} and durability {a.durability:.2f}")

            loot.append(a_o_s)

    for item in loot:
        vault.add_item(item.object.uuid)
        item.update_binary()
    vault.update_binary()
