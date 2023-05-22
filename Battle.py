import pickle
import math
import random
import inspect
import os
from random import randint
from datetime import datetime

Version = 2.61
battle_cool_down = 60*60

drop = {0:{'minExp':200,'maxExp':300}, 1:{'minExp':300,'maxExp':400,'rune':87,'chance':5}, 2:{'minExp':600,'maxExp':750,'rune':88,'chance':5}, 3:{'minExp':750,'maxExp':1000,'rune':89,'chance':5}, 4:{'minExp':1000,'maxExp':1200,'rune':90,'chance':5}, 5:{'minExp':1500,'maxExp':1500}, 6:{'minExp':1500,'maxExp':3000}, 7:{'minExp':3000,'maxExp':5000}}

def update_bosses():
	bosses = get_items('bosses')

	for id_ in bosses:
		boss = bosses[id_]
		
		new_boss = Boss(boss.id, boss.name, boss.health.value)
			
		for item in boss.items:
			item.id = boss.id
			new_boss.add(item)

		bosses[id_] = new_boss

	with open('bosses', 'wb') as file:
		pickle.dump(bosses,file)
		

def get_items(name='items'):
	if not os.path.exists(name):
		items = {}	
		with open(name, 'wb') as file:
			pickle.dump(items,file)
		return
	
	with open(name,'rb') as file:
		return pickle.load(file)

def save_item(item, name='items'):
	items = get_items(name)
	#print(items)
	items[item.id] = item
	with open(name, 'wb') as file:
		pickle.dump(items,file)

def declination(num, root, end):
	last_digit = num%10
	if num%100 in range(10,21) or num%10 in range(5,10) or num%10 == 0:
		return root+end[-1]
	elif num%10 == 1:
		return root+end[0]
	
	return root+end[1]

class Battle(object):
	"""docstring for Battle"""
	def __init__(self, *players):
		self.members = players
		self.players = []
		self.move = 0
		self.boss = False
		self.message = ''
		self.dead_players = []
		self.is_over = False
		self.history = []
		
		items = get_items()
		
		self.weather = items[randint(500, 509)]
		self.arena = items[randint(600, 609)]

		#self.weather = items[507]
		#self.arena = items[609]

		del items
		print(self.weather.name, self.arena.name)
		for player in players:
			player.add(self.weather, self.arena)
			player.set_stats()
			print(player.health)
			player.max_health = Health(player.health.value)
			print('MAX HEALTH IS', player.max_health)
			player.in_battle = True

			if type(player) == Boss:
				self.boss = player
			else:
				self.players.append(player)

		self.index = random.randint(0, len(self.members)-1)

	def sort(self):
		self.players = []

		for member in self.members:
			if type(member) == Boss:
				self.boss = member
			else:
				self.players.append(member)

	def next(self):
		if self.boss:
			self.next_against_boss()
		elif len(self.members) == 2:
			self.next_duel()

	def next_duel(self):
		self.move_member = self.members[self.index]
		
		if self.move_member.health.value <= 0:
			index = (self.index + 1) % len(self.members)
			self.message = 'Битва окончена! Игрок '+self.members[index].name+' победил!'
			self.history.append(self.message)
			self.is_over = True
			return
		
		self.move += 1
		#"Место действие: {} / Условие: {}\n".format(self.arena.name,self.weather.name) +
		self.message = 'Ход '+str(self.move)+'\n'+'Атакует '+self.move_member.name+'\n\n\n'

		if self.move_member.stuned == True:
			self.move_member.stuned = False

			self.index = (self.index + 1) % len(self.members)
			self.message += 'Проводит раунд в ошеломление!'
			self.history.append(self.message)
			return
		
		if self.move_member in self.players:
			index = (self.index + 1) % len(self.members)
			self.message += self.move_member.attack(self.members[index])
			self.index = (self.index + 1) % len(self.members)

		self.history.append(self.message)
	

	def next_against_boss(self):
		print(self.boss.health)
		if self.players == []:
			print('Босс',self.boss.name,'победил!')
			self.message = 'Битва окончена! Босс '+self.boss.name+' победил!'
			self.history.append(self.message)
			self.is_over = True
			return

		elif self.boss.health.value == 0:
			names = []
			for player in self.players:
				names.append(player.name)
			
			print('Битва окончена! Игроки победили, выжили',','.join(names),'!')
			
			self.message = 'Битва окончена! Игроки победили, выжили '+ ','.join(names)+'!'
			self.history.append(self.message)
			self.is_over = True

			return

		self.move_member = self.members[self.index]
		
		if self.move_member.health.value == 0:
			self.index = (self.index + 1) % len(self.members)
			self.next()
			return

		self.move += 1
		#"Место действие: {} / Условие: {}\n".format(self.arena.name,self.weather.name) + 
		self.message = 'Ход '+str(self.move)+'\n'+'Атакует '+self.move_member.name+'\n\n\n'

		if self.move_member.stuned == True:
			self.move_member.stuned = False

			self.index = (self.index + 1) % len(self.members)
			self.message += 'Проводит раунд в ошеломление!'
			self.history.append(self.message)
			return
		
		if self.move_member in self.players:
			self.message += self.move_member.attack(self.boss)
		else:
			attacked_player = self.players[random.randint(0, len(self.players)-1)]
			self.message += self.move_member.attack(attacked_player)

			if attacked_player.health.value == 0:
				del self.players[self.players.index(attacked_player)]

		self.index = (self.index + 1) % len(self.members)
		self.history.append(self.message)
	
	def __str__(self):
		str_ = 'Ход '+str(self.move) + '. Место: '+self.arena.name+'/ Условие: '+self.weather.name+'\n'
			
		for member in self.members:			
			str_ += member.name + ' '

		return str_

class Player(object):
	def __init__(self, id_, name, health):
		self.id = id_
		self.name = name
		self.health = Health(health)
		self.start_health = self.health
		self.magic_attribute = Magic_attribute()
		self.magic_attribute_is_on = True
		self.level = 1
		self.premium = False
		self.in_battle = False
		self.energy = Energy(100)
		self.last_raid = None
		self.last_raid_call = None
		self.raid_limit = True
		self.last_energy_updated = datetime.now()
		self.last_raid_ready = True
		self.create_arsenal()
		self.set_default()
		self.items = []
		self.ids = []
		self.favorite = []
		self.last_battls = []
		self.save_health = False
		self.stuned = False
		self.fire_damage_per_move = Fire_damage(0)
		self.bleeding_damage_per_move = Bleeding_damage(0)
		self.version = Version

	def set_default(self):
		self.health = Health(int(self.level) + int(self.level)**2//10)
		self.damage = Damage(10)
		self.heal = Heal(0)
		self.damage_precent = Damage_precent(0)
		self.health_precent = Health_precent(0)
		self.energy_regen = Energy_regen(5)
		self.defence = Defence(0)
		self.price = Price(0)
		self.anti_defence = Anti_defence(0)
		self.armor_break = Armor_break(0)
		self.crit_damage = Crit_damage(200)
		self.crit_chance = Crit_chance(10)
		self.anti_crit = Anti_crit(0)
		self.other_anti_crit = Anti_crit(0) 
		self.stun = Stun(50)
		self.accuracy = Accuracy(30)
		self.bubble = Bubble(0)
		self.poison_damage = Poison_damage(0)
		self.immunity = Immunity(0)
		self.bleeding_damage = Bleeding_damage(0)
		self.coagulation = Coagulation(0)
		self.fire_damage = Fire_damage(0)
		self.multiplyer = Multiplyer(100)
		self.vampirism = Vampirism(0)
		self.darkness_awaits = Darkness_awaits(False)
		self.enemy_item = None

	def __str__(self):
		self.set_stats()
		str_ = ''
		count = 0
		
		for attr in difines_stat:
			#print(attr, self.__dict__[attr].value)
			count += 1
			text = difines_stat[attr]
			attr_data = self.__dict__[attr]
			
			if '->' in text:
				text = text.split('->')
			else:
				text = [text,'']  
			
			if attr_data .value != 0 or count < 9:
				extra = ''
				extra_attr = None
				if attr == 'health' or attr == 'bubble':
					standart = self.__dict__['full_'+attr]
				else:
					standart = attr_data + type(attr_data)(0)

				if standart.value != attr_data.value:
					attr_data, extra_attr = standart.value, attr_data.value
				
				if extra_attr:
					extra = ' ({})'.format(str(extra_attr))
				
				str_ += text[0]+' — '+str(attr_data)+extra+text[1]+'\n'
		
		str_ += 'Атрибут — '+self.magic_attribute.name 
		return str_

	def create_arsenal(self):
		self.equipment = Equipment()
		self.inventory = Inventory()
		self.runes = Runes()
		self.consumables = Consumables()
		self.different = Different_effects()
		self.in_battle_effects = Different_effects()
		self.bag = Bag()

		self.arsenal = [self.equipment, self.runes, self.consumables, self.different, self.in_battle_effects]
		self.order = [self.inventory, self.bag, self.equipment, self.runes, self.consumables, self.different]

	def add(self, *args):
		for item in args:
			if not item:
				continue

			if Outfit in inspect.getmro(type(item)):
				had_eq = self.equipment.append(item)
				if had_eq:
					self.inventory.append(had_eq)
			
			elif Consumable in inspect.getmro(type(item)):
				self.bag.append(item)

			elif type(item) == Rune:
				self.runes.append(item)
			
			elif type(item) == Different:
				if 'id' in item.__dict__ and item.id and item.id < 0 and item.id != -3:
					self.in_battle_effects.append(item)
				else:
					self.different.append(item)

			self.items.append(item)
			self.ids.append(item.id)
		
		self.set_stats()

	def use_consumables(self, id_):
		for i in range(len(self.bag.items)):
			if int(id_) == self.bag.items[i].id:
				self.consumables.append(self.bag.items[i])
				
				del self.bag.items[i]
				del self.bag.names[i]
				del self.bag.ids[i]
				
				return True

	def clear(self, name):
		if not hasattr(self,name):
			return
		
		data = getattr(self,name)
		for item in data.items:
			for i in range(len(self.items)):
				if self.items[i].id == item.id:
					del self.items[i]
					del self.names[i]
					del self.ids[i]
					break

		setattr(self, name ,type(data)()) 

		self.set_stats()

	def delete(self, id_):
		if not id_ in self.ids:
			return None

		for i in range(len(self.items)):
			if self.items[i].id == int(id_):
				if self.items[i].name in self.inventory.names:
					self.inventory.delete(self.items[i].id)
				else:
					for items_ars in self.arsenal:
						if self.items[i].name in items_ars.names:
							items_ars.delete(self.items[i].id)
							break
					else:
						return
				
				del self.items[i]
				del self.names[i]
				del self.ids[i]

				self.set_stats()

				return True

		return False


	def equip(self,id_):
		for i in range(len(self.inventory.items)):
			if int(id_) == self.inventory.items[i].id:
				had_eq = self.equipment.append(self.inventory.items[i])
				del self.inventory.items[i]
				del self.inventory.names[i]
				del self.inventory.ids[i]
				
				if had_eq:
					self.inventory.append(had_eq)

				return True

	def set_items(self):
		arsenal = [self.inventory, self.equipment, self.runes, self.different, self.bag]
		self.items = []
		self.names = []
		self.ids = []

		for items in arsenal:
			for item in items.items:
				self.items.append(item)
				self.names.append(item.name)
				self.ids.append(item.id)

	def set_stats(self, attribute=True, save_health=False):
		if self.in_battle and 'max_health' in self.__dict__:
			old_max_health = Health(self.max_health.value)
			old_health = Health(self.health.value)
			old_bubble = Bubble(self.bubble.value)
		
		self.set_default()

		if not type(self) == Boss:
			self.set_items()
		arsenal = self.arsenal + [self.magic_attribute]
		#print('-----------------------------------------------')
		enemy_attrs = []
		upgrade_attrs = []
		
		for items in arsenal:
			#print(type(items))
			if Magic_attribute in inspect.getmro(type(items)):
				if not attribute or type(self) == Boss:
					continue
			else:
				items.set_stats()
			
			for attr in items.__dict__:
				if Stat in inspect.getmro(type(getattr(items,attr))):
					if hasattr(self, attr):
						#print(type(items), attr, getattr(items,attr).value)
						if 'enemy_' in attr:
							if attr in enemy_attrs:
								getattr(self,attr).value += getattr(items,attr).value
							else:
								setattr(self,attr,getattr(items,attr))
								enemy_attrs.append(attr)
						else:
							getattr(self,attr).value += getattr(items,attr).value
							upgrade_attrs.append(attr)
					else:
						setattr(self,attr,getattr(items,attr))
						upgrade_attrs.append(attr)

		for items in self.arsenal:
			self.make_special_effect(items)

		if self.in_battle or type(self) == Boss:
			for attr in upgrade_attrs:
				value = getattr(self,attr) - type(getattr(self,attr))(0)
				setattr(self,attr,value) 
		
		if type(self) == Boss or not 68 in self.equipment.ids:
			self.damage.value += self.damage_precent.value*self.damage.value//100

		item = Different(id=-1, name='Подарок врага')
		
		for attr in self.__dict__:
			if 'enemy_' in attr and not Item in inspect.getmro(type(getattr(self,attr))):
				stat_attr = attr.replace('enemy_','')
				class_attr = stat_attr[0].upper()+stat_attr[1:]
				
				if class_attr in globals():
					setattr(item, stat_attr, getattr(self,attr))

		self.enemy_item = item
		
		#print('-----------------------------------------------')
		
		if self.in_battle and 'max_health' in self.__dict__:
			self.health = old_health
			self.bubble = old_bubble
			self.max_health = old_max_health
		else:
			if self.last_raid:
				self.last_raid_ready = (datetime.now() - self.last_raid).seconds > battle_cool_down
			else:
				self.last_raid_ready = True
			
			self.health += self.health_precent.value*self.health.value//100
			time_left = (datetime.now() - self.last_energy_updated).seconds
			self.full_health = Health(self.health.value)
			self.full_bubble = Bubble(self.bubble.value)
			
			if self.energy.value != 100:
				if self.energy.value > 60:
					precent = 20
				elif self.energy.value > 30:
					precent = 30
				else:
					precent = 50

				self.health -= math.ceil(self.health.value * precent//100)
				self.start_health = Health(self.health.value)
				self.bubble -= math.ceil(self.bubble.value * precent//100)
			
			if time_left > 1/(self.energy_regen.value*3600):
				self.energy += self.energy_regen.value*(time_left/3600)
				self.last_energy_updated = datetime.now()

	
	def make_special_effect(self,items):
		#print(self.damage, type(items))
		if 51 in items.ids:
			self.poison_damage = Poison_damage(0)
			self.bleeding_damage = Bleeding_damage(0)
		if 56 in items.ids:
			self.crit_damage = Crit_damage(250)
		if 66 in items.ids:
			self.crit_chance = Crit_chance(40)
			self.crit_damage = Crit_damage(400)
		
		if 69 in items.ids:
			for i in range(0,self.defence.value,5):
				self.damage.value += 1

		if 70 in items.ids and not self.in_battle:
			for i in range(0,self.health.value,5):
				self.damage.value -= 1
		
		if 82 in items.ids:
			for attr in self.__dict__:
				basis = inspect.getmro(type(getattr(self,attr)))
				not_include = [Bleeding_damage, Fire_damage, Stun, Multiplyer, Heal, Energy, Energy_regen, Darkness_awaits]

				if Stat in basis and not 'enemy_' in attr:
					for stat in not_include:
						if stat in basis:
							break
					else:
						stat = getattr(self,attr)
						stat.value += 5
						#print(attr, stat)
						setattr(self, attr, stat)

		if 68 in items.ids:
			self.damage = Damage(self.accuracy.value)

	def battle_special_effect(self,other):
		item = Different(id=-2, name='battle_effects')
		for arsenal in self.arsenal[:-1]:
			
			if 70 in arsenal.ids:
				damage = 0
				for i in range(0,self.health.value,5):
					damage -= 1
				
				item.damage = Damage(damage)
			
			if 34 in arsenal.ids:
				item.health, item.defence = Health(100), Defence(15)
				if other.level > 10:
					item.health += 25
					item.defence += 10
					item.anti_defence = Anti_defence(5)
				if other.level > 20:
					item.health += 25
					item.defence += 10
					item.anti_defence += 20
					item.accuracy = Accuracy(10)
				
			if 30 in arsenal.ids:
				if self.level > other.level:
					if not 'damage' in item.__dict__:
						item.damage = Damage(0)
					if not 'anti_defence' in item.__dict__:
						item.anti_defence = Anti_defence(0)
					
					item.damage.value += 5
					item.anti_defence += 50

		if not item == Different(id_=-2, name='battle_effects'):
			self.add(item)
		self.add(other.enemy_item)


	def attack(self, other):
		#rand = random.randint(0, 100)
		text = ''
		damage_text = ''
		darkness = None
		damage = Damage(0)
		hand_damage = Damage(0)
		
		if not self.magic_attribute.name == 'нет' and self.magic_attribute.is_opposite(other.magic_attribute) and self.magic_attribute_is_on:
			self.set_stats(False)
			self.magic_attribute_is_on = False

		elif self.magic_attribute_is_on == False:
			self.set_stats()
			self.magic_attribute_is_on = True

		self.battle_special_effect(other)
		other.battle_special_effect(self)
		#print(self)	
		if self.check_rand(self.accuracy):
			damage_text += 'Попадание!\n\n\n'
			damage = self.damage
			print('FFFFFFFFFF', damage)
			
			if self.check_rand(self.crit_chance - other.anti_crit):
				damage = Damage((self.crit_damage - other.anti_crit).value//100*damage.value)

				damage_text += 'Критический удар!\n\n'

				if other.bubble.value <= 0:
					if self.check_rand(self.stun):
						other.stuned = True
						damage_text += 'Ошеломление!\n\n'
				
			print(other.defence, self.anti_defence, other.defence - self.anti_defence, 'Туууууууууууууууут')
			damage -= (other.defence - self.anti_defence)

			if other.bubble.value > 0 and damage:
				other.bubble -= Bubble(1)
				damage_text += 'Божественный щит отразил {} {}, {} {} {}\n\n\n'.format(damage.value,declination(damage.value, 'урон',['','а','а']), other.bubble.value, declination(other.bubble.value, 'щит',['','а','ов']), declination(other.bubble.value, 'остал',['ся','ось','ось']))
				damage = Damage(0)
			elif damage.value != 0:
				damage_text += '{} {} {}\n\n\n'.format(declination(damage.value, 'Нанес',['ён','ено','ено']) , damage.value, declination(damage.value, 'урон',['','а','а']))
			
			hand_damage = Damage(damage.value)
			print('Сначала',hand_damage)
			
		else:
			damage_text += 'Промах!\n\n\n'

		poison_damage = self.poison_damage - other.immunity
		bleeding_damage = other.bleeding_damage_per_move - other.coagulation
		damages = [poison_damage, bleeding_damage, other.fire_damage_per_move]
		print(self.darkness_awaits.value,'daaaaark')
		if self.darkness_awaits.value > 0:
			damages_name = ['тёмной энергией и столько же восстановлено','кровотечением','огнём']
		else:
			damages_name = ['ядом','кровотечением','огнём']

		for i in range(len(damages)):
			if damages[i].value > 0:
				damage += damages[i].value
				text += '{} {} {} {}\n\n'.format(declination(damages[i].value, 'Нанес',['ён','ено','ено']), damages[i], declination(damages[i].value, 'урон',['','а','а']), damages_name[i])

				if self.darkness_awaits.value > 0 and i == 0:
					darkness = damages[i]

		print('Другие',hand_damage)
		
		if hand_damage.value != 0:
			other.bleeding_damage_per_move += self.bleeding_damage
		
		other.fire_damage_per_move += self.fire_damage	

		if damage_text != '':
			text += '\n\n\n'+damage_text
	
		print('Хил',hand_damage)
		if self.heal.value != 0:
			self.health += Health(self.heal.value)
			text += 'Восстановлено - {} {}\n\n\n'.format(self.heal.value, declination(self.heal.value, 'здоровь',['е','я','я']))

		if damage:
			if hand_damage and self.vampirism.value != 0:
				value = int(hand_damage.value * self.vampirism.value/100)
				self.health += Health(value)
				
				if value != 0: 
					text += 'Поглощено {} {}\n\n\n'.format(value, declination(value, 'здоровь',['е','я','я']))

			if darkness:
				self.health += Health(darkness.value)

			if damage.value >= other.max_health.value//2 and 83 in self.ids and type(self) != Boss:
				other.health = Health(1)
			else:
				other.health -= damage.value

		if other.health.value <= 0 and (not damage or hand_damage.value == 0):
			other.health = Health(1)

		print('MAX HEALTH IS',self.max_health)

		if self.health.value > self.max_health.value:
			self.health = Health(self.max_health.value)
		
		text += '\n\n'
		if other.health.value != 0:
			text +=  'У '+ other.name+' '+str(other.health.value)+' '+declination(other.health.value, 'здоровь',['е','я','я'])
		else:
			text += other.name + ' Погиб!'
		

		self.clear('in_battle_effects')
		other.clear('in_battle_effects')
		
		return text

	
	def check_rand(self,stat):
		rand = random.randint(0, 100)
		print('check_rand',type(stat), rand, stat.value)
		return rand <= stat.value


class Boss(Player):
	def set_default(self):
		self.level = self.id*5
		self.health = self.start_health
		self.damage = Damage(0)
		self.heal = Heal(0)
		self.damage_precent = Damage_precent(0)
		self.health_precent = Health_precent(0)
		self.defence = Defence(0)
		self.anti_defence = Anti_defence(0)
		self.armor_break = Armor_break(0)
		self.crit_damage = Crit_damage(0)
		self.crit_chance = Crit_chance(0)
		self.anti_crit = Anti_crit(0)
		self.energy_regen = Energy_regen(5)
		self.other_anti_crit = Anti_crit(0) 
		self.stun = Stun(0)
		self.accuracy = Accuracy(0)
		self.bubble = Bubble(0)
		self.poison_damage = Poison_damage(0)
		self.immunity = Immunity(0)
		self.bleeding_damage = Bleeding_damage(0)
		self.coagulation = Coagulation(0)
		self.fire_damage = Fire_damage(0)
		self.multiplyer = Multiplyer(100)
		self.vampirism = Vampirism(0)
		self.darkness_awaits = Darkness_awaits(False)
		self.enemy_item = None
	
	def create_arsenal(self):
		self.different = Different_effects()
		self.in_battle_effects = Different_effects()
		self.arsenal = [self.different, self.in_battle_effects]

class Items:		
	def __init__(self, *args):
		self.names = []
		self.items = []
		self.ids = []

		self.append(*args)

	def append(self,*args):
		for item in args:
			had_eq = self.check_item(item)
			if had_eq == None:
				return

			self.names.append(item.name)
			
			self.items.append(item)
			self.ids.append(item.id)
			self.set_stats()

			return had_eq

	def delete(self, id_):
		for i in range(len(self.items)):
			if self.items[i].id == id_:
				type_ = type(self.items[i]).__name__
				del self.items[i]
				del self.names[i]
				del self.ids[i]

				return type_

	def check_item(self, item):
		return True

	def set_stats(self):
		self.ids = []
		self.names = []
		
		for attr in self.__dict__:
			if Stat in inspect.getmro(type(getattr(self,attr))):
				value = type(getattr(self,attr))(0)
				setattr(self,attr,value)
				
		for item in self.items:
			for attr in item.__dict__:
				if Stat in inspect.getmro(type(getattr(item,attr))):
					if hasattr(self, attr):
						getattr(self,attr).value += getattr(item,attr).value
					else:
						setattr(self,attr,getattr(item,attr))

			self.ids.append(item.id)
			self.names.append(item.name)

	
	def get_stats(self):
		data = self.__dict__
		del data['items']
		del data['names']

		return data

	def __str__(self):
		text = ''
		items_list = []
		for item in self.items:
			#print(item, item.id)
			if not item.name in items_list:
				text += str(item.id)+' . '+ item.name

				if self.names.count(item.name) > 1:
					text += ' '+str(self.names.count(item.name)) + ' шт.\n'
				else:
					text +='\n'

				items_list.append(item.name)

		if text == '':
			text = 'Нет предметов'

		#print(text)
		return text

class Equipment(Items):
	def check_item(self,item):
		had_eq = False
		type_ = type(item).__name__

		if hasattr(self, type_):
			index = self.items.index(getattr(self,type_))
			had_eq = self.items[index]
			del self.items[index]
			self.items = self.items
			del self.names[index]
			del self.ids[index]
		
		setattr(self,type_,item)

		return had_eq

	def delete(self, id_):
		type_ = super().delete(id_)
		delattr(self,type_)

	def __str__(self):
		text = ''
		for item in self.items:
			#print(item, item.id)
			text += str(item.id)+' . '+difines_outfit[type(item)] +' — '+item.name+'\n'

		if text == '':
			text = 'Нет предметов'
		
		#print(text)
		return text

class Inventory(Items):
	pass

class Consumables(Equipment):
	pass

class Bag(Inventory):
	pass

class Runes(Items):
	def check_item(self,item):
		if item.name in self.names:
			return None

		return item.name

class Different_effects(Items):
	pass

class In_battle_effects(Different_effects):
	pass

class Item(object):
	def __init__(self, **kwargs):
		for attr in kwargs:
			class_attr = attr.replace('enemy_','')
			class_attr = (class_attr[0].upper()+class_attr[1:])
			
			if class_attr in globals() and Stat in inspect.getmro(globals()[class_attr]):
				setattr(self, attr, globals()[class_attr](kwargs[attr]))	
			else:
				setattr(self, attr, kwargs[attr])
		if not hasattr(self,'id'):
			self.id = None
	
	def get_type(self):
		return type(self).__name__

	def __str__(self):
		return str(self.__dict__)

class Outfit(Item):
	pass

class Weapon(Outfit):
	pass

class Armor(Outfit):
	pass

class Ring(Outfit):
	pass

class Belt(Outfit):
	pass

class Pet(Outfit):
	pass

class Necklace(Outfit):
	pass

class Rune(Item):
	pass

class Consumable(Item):
	pass

class Different(Item):
	pass

class Food(Consumable):
	pass

class Potion(Consumable):
	pass

class Trophies(Consumable):
	pass


class Magic_attribute(Item):
	def __init__(self):
		self.opposite = None
		self.is_attribute = True
		self.stun_constant = None
		self.is_attribute = None
		self.name = 'нет'
		
	def is_opposite(self,other):
		if type(other) == self.opposite:
			return True
		
		return False

class Ice(Magic_attribute):
	def __init__(self):
		super().__init__()
		self.opposite = Lightning
		self.stun = Stun(100)
		self.other_anti_crit = Anti_crit(10)
		self.name = 'Лёд'

class Fire(Magic_attribute):
	def __init__(self):
		super().__init__()
		self.opposite = Ice
		self.fire_damage = Fire_damage(1)
		self.name = 'Огонь'

class Wind(Magic_attribute):
	def __init__(self):
		super().__init__()
		self.opposite = Fire
		self.accuracy = Accuracy(10)
		self.name = 'Ветер'

class Earth(Magic_attribute):
	def __init__(self):
		super().__init__()
		self.opposite = Plants
		self.defence = Defence(25)
		self.Anti_crit = Anti_crit(10)
		self.damage = Damage(10)
		self.name = 'Земля'

class Plants(Magic_attribute):
	def __init__(self):
		super().__init__()
		self.opposite = Wind
		self.immunity = Immunity(5)
		self.anti_defence = Anti_defence(10)
		self.vampirism = Vampirism(50)
		self.name = 'Растительность'


class Lightning(Magic_attribute):
	def __init__(self):
		super().__init__()
		self.opposite = Earth
		self.crit_damage = Crit_damage(300)
		self.other_anti_crit = Anti_crit(15)
		self.name = 'Молния'

class Light(Magic_attribute):
	def __init__(self):
		super().__init__()
		self.opposite = Earth
		self.bubble = Bubble(2)
		self.name = 'Свет'

class Darkness(Magic_attribute):
	def __init__(self):
		super().__init__()
		self.opposite = Earth
		self.name = 'Тьма'
		self.darkness_awaits = Darkness_awaits(True)

class Stat(object):
	def __init__(self, value):
		self.value = value

	def __add__(self, other):		
		if type(other) == int:
			value = int(self.value) + other
		else:
			value = int(self.value) + int(other.value)

		if value < 0:
			value = 0

		return type(self)(value)

	def __sub__(self, other):
		return self + other*-1

	def __mul__(self, other):
		if type(other) == int:
			self.value *= other
		else:
			self.value *= other.value

		return type(self)(self.value)

	def __rmul__(self, other):
		if type(other) == int:
			self.value *= other
		else:
			self.value *= other.value

		return self.value
	
	def __gt__(self,other):
		if self.value > other.value:
			return True
		else:
			return False

	def __lt__(self,other):
		if self.value < other.value:
			return True
		else:
			return False

	def __eq__(self,other):
		if self.value == other.value:
			return True
		else:
			return False

	def __str__(self):
		return str(self.value)


class Price(Stat):
	pass

class Health(Stat):
	pass

class Health_precent(Stat):
	pass

class Damage(Stat):
	def __init__(self,value):
		self.value = value
		self.opposite = Defence
		self.minimum = 1
	
	def __add__(self, other):		
		if type(other) == int:
			value = int(self.value) + other
		else:
			value = int(self.value) + int(other.value)

		if value < self.minimum:
			value = self.minimum

		print(value,'hereeeeeeeeeeeeeeeeeee')
		return type(self)(value)

	def __sub__(self, other):
		if type(other) == self.opposite:
			if other.value > 95:
				value = 95
			else:
				value = other.value
			
			print(1-value*0.01)
			value = math.ceil(self.value * (1-value*0.01))
			print(value)
		
		elif type(other) == int or type(other) == float:
			value = self.value - other
		else:
			value = self.value - other.value

		print(value,'hereeeeeeeeeeeeeeeeeee')
		if value < self.minimum:
			value = self.minimum
		
		print(type(self),self.minimum)
		
		return type(self)(value)

class Defence(Damage):
	def __init__(self,value):
		self.value = value
		self.opposite = Anti_defence
		self.minimum = 0

class Anti_defence(Stat):
	pass

class Сrit(Damage):	
	def __init__(self,value):
		self.value = value
		self.opposite = Anti_crit
		self.minimum = 0
		
class Crit_damage(Сrit):
	def __init__(self,value):
		super().__init__(value)
		self.minimum = 100

class Crit_chance(Сrit):
	pass
		
class Anti_crit(Stat):
	pass

class Accuracy(Stat):
	pass

class Heal(Stat):
	pass

class Vampirism(Stat):
	pass

class Bubble(Stat):
	pass

class Poison_damage(Stat):
	pass

class Immunity(Stat):
	pass

class Bleeding_damage(Stat):
	pass

class Coagulation(Stat):
	pass

class Fire_damage(Stat):
	pass

class Armor_break(Stat):
	pass

class Stun(Stat):
	pass

class Multiplyer(Stat):
	pass

class Damage_precent(Stat):
	pass

class Health_precent(Stat):
	pass		

class Darkness_awaits(Stat):
	pass

class Energy_regen(Stat):
	pass

class Adapt(Stat):
	def __add__(self, other):		
		if type(other) == int:
			value = int(self.value) + other
		else:
			value = int(self.value) + int(other.value)

		if value < 0:
			value = 0
		elif value > 100:
			value = 100

		return type(self)(value)

class Energy(Stat):
	def __add__(self, other):		
		if type(other) == int or type(other) == float:
			value = int(self.value) + other
		else:
			value = int(self.value) + int(other.value)

		if value > 100:
			value = 100

		elif value < 0:
			value = 0

		return type(self)(value)

	def __sub__(self, other):
		return self + other*-1

	def __mul__(self, other):
		if type(other) == int:
			self.value *= other
		else:
			self.value *= other.value

		return type(self)(self.value)

	def __str__(self):
		return str(int(self.value))

def import_from_file():
	with open('test.txt', 'r', encoding='utf-8-sig') as file:
		data = file.read().splitlines()
	for el in data:
		if 'Полуторный Меч' in el:
			kind = 'Weapon'
		elif 'Набедренная Броня' in el:
			kind = 'Armor'
		elif 'Кольцо Рыцаря' in el:
			kind = 'Ring'
		elif 'Пояс Кобольта' in el:
			kind = 'Belt'
		elif 'Грязекраб' in el:
			kind = 'Pet'
		elif 'Руна Кошки' in el:
			kind = 'Rune'
		elif 'Бусы Монаха' in el:
			kind = 'Necklace'

		print(el)
		if '(id' in el:
			func = "item = "+ kind + el.replace(',,',',')+'; save_item(item)'
			print(func)
			input('Окей?')
			exec(func)
	
	save_item(item)


difines_outfit = {Weapon:'Оружие', Armor:'Броня', Ring:'Кольцо', Belt:'Пояс', Pet:'Питомец', Necklace:'Ожерелье', Trophies:"Трофей", Food:"Еда", Potion:"Зелье"}
difines_stat = {'health':'Здоровье', 'damage':'Урон', 'defence':'Защита->%', 'crit_chance':'Крит шанс->%', 'crit_damage':'Крит урон->%', 'accuracy':'Меткость->%', 'anti_defence':'Бронебробитие->%', 'anti_crit':'Стойкость->%', 'vampirism':'Вампиризм->%', 'poison_damage':'Урон ядом->/ход', 'bleeding_damage':'Урон кровотечением->/ход', 'fire_damage':'Урон огнём->/ход', 'immunity':'Иммунитет', 'coagulation':'Коагуляция', 'bubble':'Божественный щит', 'stun':'Оглушение->%', 'multiplyer':'Множитель опыта->%', 'energy_regen':'Эффективность отдыха->/час'}


if __name__ == '__main__':
	effects = ['damage','armor_penetration','krit','vampirism','accuracy','bleeding','stamina','poison','defence']
	items = get_items()
	print(items[49])
	#print(items[3])
	#exit()
	#print(items[30])
	
	for item in sorted(list(items.keys())):
		print(item, items[item].name)

	#print(items[602].anti_crit)
	#item = items[87]
	#item.bleeding_damage = Bleeding_damage(2)
	#item.name = 'Руна жертвы'

	#save_item(item)
	#print(items[609])
	#print(sorted(items.keys()))
	#print(items[609])
	#item = Different(id=607, name='Сумеречный лес', vampirism=50)
	#save_item(item)
	#print(items[16].name)
	#print(items[6].__dict__)
	#print(items.keys())
	#item = items[503]
	#item.name = 'Гроза'
	#item = items[609]
	#item.name = 'Побережье'
	#save_item(item)
	#item = items[27]
	#print(item)
	#item.damage = Damage(5)
	#save_item(item)
	#item.anti_defence = Anti_defence(0)
	#item.damage = Damage(0)
	#save_item(item)
	#item.bleeding_damage = Bleeding_damage(1)
	#save_item(item)
	#b = Boss(id_=7, name='Сумеречный Дракон 👑', health=2500)
	#b.magic_attribute = Lightning()
#	b.add(diff)
	#print(b.crit_damage)
	#item = Rune(id=0, price=0, rating='Мифический', name='Руна новичка', accuracy=10, damage=5)
	#save_item(b,'bosses')
	#bosses = get_items('bosses')
	#bosses[4].items[0].bleeding_damage = Bleeding_damage(5)
	#bosses[4].different.items[0].bleeding_damage = Bleeding_damage(5)
	
	#bosses[4].set_stats()
	#print(bosses[4])
	#bosses[4].different.items[0].poison_damage = Poison_damage(0)
	#print(bosses[4].items)
	#save_item(bosses[4], 'bosses')
	#p = Player(id_=11, name='Витя', health=0)
	#p.level = 50
	#item = Weapon(id=1,name='Огонь',damage=15)

	#p.add(item)
	#p.clear('equipment')
	#print(p.equipment)
	#print(p)
	#p2 = Player(id_=11, name='Вася',health=0)
	#p1 = Player(id_=10, name='Вася',health=0)
	#p1.level = 70
	#p2.level = 70
	#print(get_items()[34])
	#p2.add(get_items()[34])
	#print(p2)

	#b = Battle(p1,p2)
	#while True:
	#	b.next()
	#	print(b.message)
	#	input()
	#battle = Battle(p,b)
	#items = get_items()
	#print(items.keys())
	#item = Rune(id=0, name='Руна новичка', accuracy=5, price=0)
	#save_item(item)
	#update_bosses()
	#print(battle)
	#battle.next()
	#print(battle)
	