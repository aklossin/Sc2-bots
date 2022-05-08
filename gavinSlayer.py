from types import UnionType
from sc2 import maps
from sc2.player import Bot, Computer
from sc2.main import run_game
from sc2.data import Race, Difficulty
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.upgrade_id import UpgradeId
import random

class GavinDestroyer(BotAI):
    async def on_step(self, iteration:int):
        
        print(f"the iteration is {iteration}")

        CCS = self.townhalls
        CC = self.townhalls.ready.random

        #macro
        if self.structures(UnitTypeId.BARRACKS).ready:
            for CC in self.townhalls(UnitTypeId.COMMANDCENTER).idle:
                if self.can_afford(UnitTypeId.ORBITALCOMMAND):
                    CC.build(UnitTypeId.ORBITALCOMMAND)

        if self.can_afford(UnitTypeId.SCV) and CCS.idle and not self.supply_workers + self.already_pending(UnitTypeId.SCV) > 80:
                CC.train(UnitTypeId.SCV)

        for orbital in self.townhalls(UnitTypeId.ORBITALCOMMAND).filter(lambda x: x.energy >= 50):
            mule_points = self.mineral_field.closer_than(50, orbital)
            if mule_points:
                mule_point = max(mule_points, key=lambda x: x.mineral_contents)
                orbital(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mule_point)
                
        if self.structures(UnitTypeId.BARRACKS).amount >= 2:
            if self.structures(UnitTypeId.REFINERY).amount < 2:
                vgs = self.vespene_geyser.closer_than(15, CC)
                for vg in vgs:
                    if self.can_afford(UnitTypeId.REFINERY) and not self.already_pending(UnitTypeId.REFINERY):
                        await self.build(UnitTypeId.REFINERY, vg)
        
        #supply management
        if self.structures(UnitTypeId.BARRACKS).ready:
            if self.supply_cap < 200:
                if self.supply_left < 3 and self.already_pending(UnitTypeId.SUPPLYDEPOT) < self.townhalls.amount * 2:
                    if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                        await self.build(UnitTypeId.SUPPLYDEPOT, near=CC.position.towards(self.game_info.map_center, 5))
        else:
            if self.can_afford(UnitTypeId.SUPPLYDEPOT) and not self.already_pending(UnitTypeId.SUPPLYDEPOT) and self.supply_left < 3:
                    await self.build(UnitTypeId.SUPPLYDEPOT, near=CC.position.towards(self.game_info.map_center, 5))

        #expanding
        if self.can_afford(UnitTypeId.COMMANDCENTER) and not self.already_pending(UnitTypeId.COMMANDCENTER) and self.supply_workers >= self.townhalls.amount * 15:
            await self.expand_now()

        #production
        if self.townhalls.amount >= 2:
            if self.can_afford(UnitTypeId.BARRACKS) and self.structures(UnitTypeId.SUPPLYDEPOT).ready and self.structures(UnitTypeId.BARRACKS).amount + self.already_pending(UnitTypeId.BARRACKS) < self.townhalls.amount * 3:
                await self.build(UnitTypeId.BARRACKS, near = self.start_location.towards(self.main_base_ramp.barracks_in_middle, 15))

        if self.structures(UnitTypeId.BARRACKS).ready and self.can_afford(UnitTypeId.MARINE):
            for Barrack in self.structures(UnitTypeId.BARRACKS).ready.idle:
                if self.structures(UnitTypeId.BARRACKSTECHLAB).amount + self.already_pending(UnitTypeId.BARRACKSTECHLAB) < 2:
                    Barrack.build(UnitTypeId.BARRACKSTECHLAB)
                Barrack.train(UnitTypeId.MARINE)

        #upgrades
        if self.townhalls.amount >= 2 and self.structures(UnitTypeId.BARRACKS).amount > 3:
            if self.can_afford(UnitTypeId.ENGINEERINGBAY) and self.already_pending(UnitTypeId.ENGINEERINGBAY) + self.structures(UnitTypeId.ENGINEERINGBAY).amount < 2:
                await self.build(UnitTypeId.ENGINEERINGBAY, near = self.start_location.towards(self.game_info.map_center, 10))
            if self.structures(UnitTypeId.ENGINEERINGBAY).ready.amount == 2:
                for ebay in self.structures(UnitTypeId.ENGINEERINGBAY).idle:
                    ebay.research(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1)
                    if self.already_pending_upgrade(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1):
                        ebay.research(UpgradeId.TERRANINFANTRYARMORSLEVEL1)
                if self.already_pending_upgrade(UpgradeId.TERRANINFANTRYARMORSLEVEL1):
                    for racklab in self.structures(UnitTypeId.BARRACKSTECHLAB).idle:
                        racklab.research(UpgradeId.STIMPACK)
                        if self.already_pending_upgrade(UpgradeId.STIMPACK):
                            racklab(AbilityId.RESEARCH_COMBATSHIELD)

        await self.distribute_workers()

        for marine in self.units(UnitTypeId.MARINE):
            if self.enemy_units.closer_than(6, marine) and (marine.is_attacking or marine.is_moving) and not marine.has_buff(BuffId.STIMPACK) and marine.health >= 30:
                marine(AbilityId.EFFECT_STIM_MARINE)
        
        if self.units(UnitTypeId.MARINE).amount >= 40:
            if self.enemy_units:    
                for unit in self.units(UnitTypeId.MARINE).idle:
                    unit.attack(random.choice(self.enemy_units))
            
            elif self.enemy_structures:
                for unit in self.units(UnitTypeId.MARINE).idle:
                    unit.attack(random.choice(self.enemy_structures))

            elif self.enemy_start_locations:
                for unit in self.units(UnitTypeId.MARINE).idle:
                    unit.attack(self.enemy_start_locations[0])
            
            else:
                for unit in self.units(UnitTypeId.MARINE).idle:
                    unit.attack(random.choice(self.mineral_field))

run_game(
    maps.get("ProximaStationLE"),
    [Bot(Race.Terran, GavinDestroyer()),
     Computer(Race.Protoss, Difficulty.Hard)],
     realtime=False
)