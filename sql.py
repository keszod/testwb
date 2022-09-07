import sqlite3

class SQLighter:

	def __init__(self,database_file):
		"""Подключаемся к БД и сохраняем курсор соединения"""
		self.connection = sqlite3.connect(database_file,check_same_thread=False)
		self.execute = self.connection.cursor().execute

	def user_exists(self,chat_id):
		with self.connection:
			result = self.execute("SELECT * FROM `user_condition` WHERE `chat_id` = ?",(chat_id,)).fetchall()
			return bool(len(result))

	def get_status(self,chat_id):
		result = self.execute("SELECT `status` FROM `user_condition` WHERE `chat_id` = ?",(chat_id,)).fetchall()
		
		return result[0][0]

	def get_temp(self,chat_id):
		result = self.execute("SELECT `temp_product` FROM `user_condition` WHERE `chat_id` = ?",(chat_id,)).fetchall()
		
		return result[0][0]

	def get_nick(self,chat_id):
		result = self.execute("SELECT `nick_name` FROM `user_condition` WHERE `chat_id` = ?",(chat_id,)).fetchall()
		
		return result[0][0]
	
	def get_users(self):
		users = self.execute("SELECT * FROM `user_condition`").fetchall()
		
		return users 

	def get_user(self,chat_id):
		user = self.execute("SELECT * FROM `user_condition` WHERE `chat_id` = ?",(chat_id,)).fetchall()
		
		return user[0]

	def update_user(self,days_max,days_past,chat_id):
		with self.connection:
			return self.execute("UPDATE `user_condition` SET `days_max` = ?,`days_past` = ? WHERE `chat_id` = ?",(days_max,days_past,chat_id,))
	
	def add_user(self,chat_id,nick_name):
		"""Добавляем пользователя в базу"""
		with self.connection:
			return self.execute("INSERT INTO `user_condition` (`chat_id`,`nick_name`) VALUES (?,?)",(chat_id,nick_name,))

	def update_status(self,chat_id,value):
		"""Обновляем значение"""
		with self.connection:
			return self.execute("UPDATE `user_condition` SET `status` = ? WHERE `chat_id` = ?",(value,chat_id,))

	def update_temp(self,chat_id,value):
		"""Обновляем значение"""
		with self.connection:
			return self.execute("UPDATE `user_condition` SET `temp_product` = ? WHERE `chat_id` = ?",(value,chat_id,))

	def add_nick_name(self,chat_id,nick_name):
		"""Обновляем значение"""
		with self.connection:
			return self.execute("UPDATE `user_condition` SET `nick_name` = ? WHERE `chat_id` = ?",(nick_name,chat_id,))
	
	def get_chat_from_nick(self,nick):
		result = self.execute("SELECT `chat_id` FROM `user_condition` WHERE `nick_name` = ?",(nick,)).fetchall()
		
		return result[0]

	def add_shared(self,chat_id,shared):
		"""Обновляем значение"""
		with self.connection:
			return self.execute("UPDATE `user_condition` SET `shared` = ? WHERE `chat_id` = ?",(shared,chat_id,))

	def update_regions(self,chat_id,regions):
		"""Обновляем значение"""
		with self.connection:
			return self.execute("UPDATE `user_condition` SET `regions` = ? WHERE `chat_id` = ?",(regions,chat_id,))

	def get_shared(self,chat_id):
		result = self.execute("SELECT `shared` FROM `user_condition` WHERE `chat_id` = ?",(chat_id,)).fetchall()
		
		return result[0][0]
	
	def close(self):
		self.connection.close()