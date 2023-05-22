import sqlite3
import codecs
import pickle
from Battle import *
from datetime import datetime

class SQLighter:

	def __init__(self,database_file):
		"""Подключаемся к БД и сохраняем курсор соединения"""
		self.database_file = database_file
		self.connection = sqlite3.connect(database_file, timeout=30)
		self.cursor = self.connection.cursor()
		self.execute = self.cursor.execute
 	
	def set_not_relevant(self,name,inn,date):
		with self.connection:
			self.execute("UPDATE `Admin` SET `is_relevant` = 0 WHERE `inn` = ? AND `name` = ? AND `date` = ?",(inn,name,date,)).fetchall()

	def get_estamate(self,name,inn,date):
		"""Получаем оценки"""
		with self.connection:
			result = self.execute("SELECT `estamate_1`,`estamate_2` FROM `Admin` WHERE `inn` = ? AND `name` = ? AND `date` = ?",(inn,name,date,)).fetchall()
			return result[0]

	def set_estamate(self,name,inn,date,estamate,number):
		"""Ставим оценки"""
		with self.connection:
			estamate_param = 'estamate_' + str(number)
			self.execute("UPDATE `Admin` SET '%s' = ? WHERE `inn` = ? AND `name` = ? AND `date` = ?" % estamate_param,(estamate,inn,name,date,)).fetchall()
	
	def get_orders_by_inn(self,inn):
		"""Находим заказы по инн"""
		with self.connection:
			result = self.execute("SELECT `name`,`date` FROM `Admin` WHERE `inn` = ? AND `is_relevant` = 1",(inn,)).fetchall()
			return result
	
	def user_exists(self,user_id):
		"""Проверяем есть ли пользователь в базе"""
		with self.connection:
			result = self.execute("SELECT * FROM `Exp` WHERE `user_id` = ?",(user_id,)).fetchall()
			return bool(len(result))

	def make_order(self,name,inn,date):
		"""Добавляем заказ в базу"""
		with self.connection:
			return self.execute("INSERT INTO `Admin` (`name`,`inn`,`date`) VALUES (?,?,?)",(name,inn,date))

	def get_all_data(self):
		""" Получаем все даты и инн заказов """
		with self.connection:
			result = self.execute("SELECT `date`,`inn`,`name` FROM `Admin` WHERE `is_relevant` = 1",()).fetchall()
			return result
	
	def add_user(self,user_id,next_message_date):
		"""Добавляем пользователя в базу"""
		next_message_date = next_message_date.strftime("%d/%m/%y/%H/%M/%S")
		print(next_message_date)
		with self.connection:
			return self.execute("INSERT INTO `Exp` (`user_id`,`next_message_date`) VALUES (?,?)",(user_id,next_message_date,))

	def add_battle(self,battle):
		"""Добавляем битву в базу"""
		with self.connection:
			players_names = ''

			for player in battle.players:
				players_names += player.name

			battle_enc = codecs.encode(pickle.dumps(battle), "base64").decode()
			if battle.boss:
				boss_name = battle.boss.name
			else:
				boss_name = '-'
		
			result = self.execute("INSERT INTO `Battles` (`players_names`,`boss_name`,`battle`) VALUES (?,?,?)",(players_names,boss_name,battle_enc,)).fetchone()
			return self.cursor.lastrowid

	def update_battle(self,battle_id,battle):
		battle = codecs.encode(pickle.dumps(battle), "base64").decode()
		with self.connection:
			self.execute("UPDATE `Player` SET `Battles` = ? WHERE `id` = ?", (battle,battle_id,))


	def add_player(self,user_id,player):
		"""Добавляем пользователя в базу"""
		player = codecs.encode(pickle.dumps(player), "base64").decode()
		with self.connection:
			return self.execute("INSERT INTO `Player` (`user_id`,`player`) VALUES (?,?)",(user_id,player,))

	def update_player(self,user_id,player):
		player = codecs.encode(pickle.dumps(player), "base64").decode()
		with self.connection:
			self.execute("UPDATE `Player` SET `player` = ? WHERE `user_id` = ?", (player,user_id,))


	def add_channel(self,name, channel_id):
		"""Добавляем пользователя в базу"""
		with self.connection:
			return self.execute("INSERT INTO `Channel` (`name`,`channel_id`) VALUES (?,?)",(name,channel_id,))

	def add_role(self, name, role_id):
		"""Добавляем пользователя в базу"""
		with self.connection:
			return self.execute("INSERT INTO `Roles` (`name`,`role_id`) VALUES (?,?)",(name,role_id,))

	def find_roles(self, name):
		with self.connection:
			result = self.execute("SELECT * FROM `Roles` WHERE `name` = ?",(name,)).fetchall()
			if result != []:
				roles = []
				for role in result:
					roles.append(int(role[-1]))

				return roles
			else:			
				None

	def find_channel(self, name):
		with self.connection:
			result = self.execute("SELECT * FROM `Channel` WHERE `name` = ?",(name,)).fetchall()
			if result != []:
				return result[0][-1]
			else:
				None

	def get_user(self,user_id):
		"""Находим user_id по инн"""
		with self.connection:
			result = self.execute("SELECT * FROM `Exp` WHERE `user_id` = ?",(user_id,)).fetchall()
			result = list(result[0])
			result[1] = datetime.strptime(result[1], "%d/%m/%y/%H/%M/%S")
			
			return result

	def get_players(self):
		"""Находим user_id по инн"""
		with self.connection:
			players = []
			result = self.execute("SELECT * FROM `Player`").fetchall()

			for player in players:
				player = pickle.loads(codecs.decode(player[-1].encode(),'base64'))
				players.append(player)
			
			return players

	def get_battles(self):
		"""Находим user_id по инн"""
		with self.connection:
			battles = []
			result = self.execute("SELECT * FROM `Battles`").fetchall()

			for battle in result:
				battle_obj = pickle.loads(codecs.decode(battle[-1].encode(),'base64'))
				battles.append(list(battle[:-1])+[battle_obj])
			
			return battles

	def get_player(self,user_id):
		"""Находим user_id по инн"""
		with self.connection:
			result = self.execute("SELECT * FROM `Player` WHERE `user_id` = ?",(user_id,)).fetchone()
			print( self.database_file)
			player = pickle.loads(codecs.decode(result[-1].encode(),'base64'))

			if len(player.favorite) > 5:
				player.favorite = player.favorite[-5:]
			
			if player.last_raid and (datetime.now() - player.last_raid).seconds >= 20*60:
				player.in_battle = False

			if Version != player.version:
				player.set_items()
				new_player = Player(player.id, player.name, player.health.value)
				atr = player.magic_attribute
				all_items = get_items()
				
				for items in [player.inventory, player.bag, player.equipment, player.runes, player.consumables, player.different]:
					for item in items.items:
						if item.id in all_items:
							new_player.add(all_items[int(item.id)])

				new_player.magic_attribute = player.magic_attribute
				new_player.last_raid = player.last_raid
				new_player.level = player.level
				new_player.favorite = player.favorite
				player = new_player
				self.update_player(user_id, player)
					
			player.set_stats()

			return player

	def update_user(self,user_id,data):
		with self.connection:
			for name in data:
				"""Обновляем значение"""
				print(name,data[name])
				if name == 'next_message_date':
					data[name] = data[name].strftime("%d/%m/%y/%H/%M/%S")
				elif name == 'exp' and int(data[name]) < 0:
					data[name] = 0

				self.execute("UPDATE `Exp` SET '%s' = ? WHERE `user_id` = ?" % name,(data[name],user_id,))

	def get_all_users(self):
		with self.connection:	
			result = self.execute("SELECT `user_id` FROM `Users`",()).fetchall()
			return result
	
	def get_params(self,user_id,*params):
		"""Получеаем значения"""
		values = []
		with self.connection:
			for param in params:
				result = self.execute("SELECT `%s` FROM `Users` WHERE `user_id` = ?" % param,(user_id,))
				result = result.fetchall()[0][0]
				values.append(result)
			
		if len(values) == 1:
			return values[0]
		
		return values

	def inn_exists(self,inn):
		"""Проверяем есть ли пользователь в базе"""
		with self.connection:
			result = self.execute("SELECT * FROM `Admin` WHERE `inn` = ? AND `is_relevant` = 1",(inn,)).fetchall()
			return bool(len(result))

	def close(self):
		self.connection.close()