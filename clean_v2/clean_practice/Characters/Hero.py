import pygame
pygame.init()
from dataclasses import dataclass
from Character import Character
from Config.Constants import *
from Config.Character_Dict import *
C = Constants()
CD = Character_Dict()


@dataclass
class Hero(Character):
    exp: int = 0
    weapon: any = None
    armor: any =  None

    def update_stats(self):
        dict = CD.HERO_STATS.get(self.name)
        self.max_health = dict.get("health") * self.level
        self.attack = dict.get("attack") * self.level
        self.defense = dict.get("defense") * self.level
        self.max_skill = dict.get("skill") * self.level
        self.health = self.max_health
        self.skill = self.max_skill

    def stats_text(self):
        text = str(self.name+"~ HP: "+str(self.health)+" ATK: "+str(self.attack)+" DEF: "+str(self.defense)+" SKL: "+str(self.skill))
        return text

    def update_skill_list(self):
        dict = CD.HERO_SKILLS.get(self.name)
        for number in range(0, self.level):
            new_skill = dict.get(number)
            if new_skill != None:
                self.learn_skill(new_skill)

    def learn_skill(self, skill: str):
        if skill not in self.skill_list:
            self.skill_list.append(skill)

    def level_up(self):
        if self.exp > self.level ** 3 and self.level < C.LEVEL_LIMIT:
            self.level += 1
            self.update_stats()
            self.update_skill_list()

    def choose_action(self):
        choose = True
        choice = None
        while choose:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    choose = False
                    pygame.quit()
                if event.type == pygame.KEYDOWN:
                    pygame.event.clear()
                    if event.key == pygame.K_a:
                        choice = "Attack"
                        return choice
                    if event.key == pygame.K_s:
                        choice = "Skill"
                        return choice
