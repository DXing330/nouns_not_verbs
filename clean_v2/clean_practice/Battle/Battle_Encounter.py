import copy
from Battle.Skill_Effect_Factory import *
from Characters.Party import *
from Characters.Monster import *
from Utility.Pick import *
from Skills.Skill import *
from Config.Skill_Dict import *
S = Skill_Dict()

@dataclass
class Monster_Encounter:
    party: any
    location: str
    monsters: list

    def generate_monsters(self):
        if len(self.monsters) <= 0:
            pass
        for monster in self.monsters:
            battle_skills = []
            for word in CD.MONSTER_SKILLS.get(monster.name):
                bskill = Skill(**S.ALL_SKILLS.get(word))
                battle_skills.append(bskill)
            monster.update_skills(battle_skills)
            battle_passives = []
            for word in CD.MONSTER_PASSIVES.get(monster.name):
                if word != None:
                    bpassive = Skill(**S.ALL_SKILLS.get(word))
                    battle_passives.append(bpassive)
            monster.update_passive_skills(battle_passives)

@dataclass
class Monster_Encounter:
    party: Party
    location: str
    heroes: list
    spirits: list
    monsters: list
    battle: bool = True

    def prepare_for_battle(self):
        self.heroes = copy.deepcopy(self.party.battle_party)
        for hero in self.heroes:
            battle_skills = []
            for skill in hero.skill_list:
                bskill = Skill(**S.ALL_SKILLS.get(skill))
                battle_skills.append(bskill)
            hero.update_skills(battle_skills)
            battle_passives = []
            for skill in hero.passive_skills:
                bpassive = Skill(**S.ALL_SKILLS.get(skill))
                battle_passives.append(bpassive)
            hero.update_passive_skills(battle_passives)
        self.spirits = self.party.spirits
        for spirit in self.spirits:
            battle_skills = []
            for skill in spirit.skill_list:
                bskill = Skill(**S.ALL_SKILLS.get(skill))
                battle_skills.append(bskill)
                spirit.update_skills(battle_skills)

    def update_monster_for_battle(self, monster: Monster):
        monster.update_stats()
        battle_skills = []
        for word in CD.MONSTER_SKILLS.get(monster.name):
            bskill = Skill(**S.ALL_SKILLS.get(word))
            battle_skills.append(bskill)
        monster.update_skills(battle_skills)
        battle_passives = []
        for word in CD.MONSTER_PASSIVES.get(monster.name):
            bpassive = Skill(**S.ALL_SKILLS.get(word))
            battle_passives.append(bpassive)
        monster.update_passive_skills(battle_passives)

    def skill_cost_cooldown(self, user, skill: Skill, pick_randomly = True):
        if skill.cooldown <= 0:
            skill.cooldown += skill.cooldown_counter
            user.skill -= skill.cost
            if user.skill >= 0:
                self.skill_activation(user, skill, pick_randomly)

    def skill_targetting(self, user, skill, pick_randomly = True):
        target_list = []
        if skill.target == "Self":
            target_list.append(user)
        elif skill.target == "Hero":
            pick_from = Pick(self.heroes, pick_randomly)
            target = pick_from.pick()
            target_list.append(target)
        elif skill.target == "All_Hero":
            target_list = self.heroes
        elif skill.target == "Monster":
            pick_from = Pick(self.monsters, pick_randomly)
            target = pick_from.pick()
            target_list.append(target)
        elif skill.target == "All_Monster":
            target_list = self.monsters
        elif skill.target == "Spirit":
            pick_from = Pick(self.spirits, pick_randomly)
            target = pick_from.pick()
            target_list.append(target)
        elif skill.target == "All_Spirit":
            target_list = self.spirits
        return target_list

    def skill_activation(self, user, skill: Skill, pick_randomly = True):
        targets = self.skill_targetting(user, skill, pick_randomly)
        if skill.effect == "Summon":
            summon = Monster(skill.effect_specifics, max(user.level - 1, skill.power))
            self.update_monster_for_battle(summon)
            if skill.power < 0:
                self.monsters.append(summon)
            else:
                self.heroes.append(summon)
        elif skill.effect == "Command":
            for target in targets:
                if skill.effect_specifics == "Spirit":
                    self.spirit_turn(target)
                elif skill.effect_specifics == "Hero":
                    self.hero_turn(target)
                elif skill.effect_specifics == "Monster":
                    self.monster_turn(target)
        elif skill.effect == "Skill":
            for word in S.COMPOUND_SKILLS.get(skill.effect_specifics):
                new_skill = Skill(**S.ALL_SKILLS.get(word))
                self.skill_activation(user, new_skill, pick_randomly)
        elif skill.effect == "Attack":
            for target in targets:
                for number in range(0, skill.power):
                    self.attack_step(user, target)
        else:
            activate = Effect_Factory(skill.effect, skill.effect_specifics, skill.power * user.level, targets)
            activate.make_effect()

    def hero_turn(self, hero: Hero):
        if len(self.monsters) > 0 and hero.turn:
            pass

    def spirit_turn(self, spirit: Spirit):
        if len(self.heroes) > 0 and len(self.monsters) > 0:
            skill = spirit.choose_action()
            self.skill_activation(spirit, skill)

    def monster_turn(self, monster: Monster):
        if len(self.heroes) > 0 and monster.turn:
            skill = monster.choose_action()
            if skill != None:
                self.skill_cost_cooldown(monster, skill)
            else:
                target = self.heroes[random.randint(0, len(self.heroes) - 1)]
                self.attack_step(monster, target)

    def attack_step(self, attacker, defender):
        damage = attacker.attack
        if attacker.weapon != None:
            attack_effect = Effect_Factory(attacker.weapon.effect, attacker.weapon.effect_specifics, attacker.weapon.power, [defender])
            attack_effect.make_effect()
        damage -= defender.defense
        if defender.armor != None:
            defense_effect = Effect_Factory(defender.armor.effect, defender.armor.effect_specifics, defender.armor.power, [attacker])
            defense_effect.make_effect()
        defender.health -= min(damage, 1)

    def passive_step(self, character):
        character.turn = True
        character.skills = True
        for skill in character.skill_list:
            if skill.cooldown > 0:
                skill.cooldown -= 1
        for buff in character.buffs:
            passive = Effect_Factory(buff.effect, buff.effect_specifics, buff.power * character.level, [character])
            passive.make_effect()
            done = buff.check_turns()
            if done:
                character.buffs.remove(buff)
        for status in character.statuses:
            passive = Effect_Factory(status.effect, status.effect_specifics, status.power * character.level, [character])
            passive.make_effect()
            done = status.check_turns()
            if done:
                character.statuses.remove(status)
        for skill in character.passive_skills:
            self.skill_activation(character, skill)

    def standby_phase(self):
        for hero in self.heroes:
            self.passive_step(hero)
        for monster in self.monsters:
            self.passive_step(monster)

    def cleanup_phase(self):
        for hero in self.heroes:
            if hero.health <= 0:
                self.heroes.remove(hero)
        for monster in self.monsters:
            if monster.health <= 0:
                self.monsters.remove(monster)
        if len(self.monsters) <= 0 or len(self.heroes) <= 0:
            self.battle = False

    def battle_phase(self):
        while self.battle:
            self.standby_phase()
            for hero in self.heroes:
                self.hero_turn(hero)
                self.cleanup_phase()
            for spirit in self.spirits:
                self.spirit_turn(spirit)
                self.cleanup_phase()
            for monster in self.monsters:
                self.monster_turn(monster)
                self.cleanup_phase()
        self.end_phase()

    def end_phase(self):
        if len(self.heroes) > 0:
            pass
        for hero in self.party.battle_party:
            pass