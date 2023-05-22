import discord
import os
import shutil
from Battle import *
import asyncio
from datetime import datetime
from datetime import timedelta
from config import bot_data
from discord.ext import commands as discord_commands
from sql import SQLighter
from random import randint
import pickle
import codecs
import re
import traceback
from discord.ui import Button, View
from discord.utils import get
from discord.ext import commands

timer_level = ['4-7', '3-4', '3-5', '3-5', '4-6', '4-7', '5-7', '5-8', '5-9', '6-9', '6-10', '7-11', '7-11', '7-12', '8-13', '8-13', '9-14', '9-15', '9-15', '10-16', '10-17', '11-17', '11-18', '11-19', '12-19', '12-20', '13-21', '13-21', '13-22', '14-23', '14-23', '15-24', '15-25', '15-25', '16-26', '16-27', '17-27', '17-28', '17-29', '18-29', '18-30', '19-31', '19-31', '19-32', '20-33', '20-33', '21-34', '21-35', '21-35', '22-36', '22-37', '23-37', '23-38', '23-39', '24-39', '24-40', '25-41', '25-41', '25-42', '26-43', '26-43', '27-44', '27-45', '27-45', '28-46', '28-47', '29-47', '29-48', '29-49', '30-49', '30-50', '31-51', '31-51', '31-52', '32-53', '32-53', '33-54', '33-55', '33-55', '34-56', '34-57', '35-57', '35-58', '35-59', '36-59', '36-60', '37-61', '37-61', '37-62', '38-63', '38-63', '39-64', '39-65', '39-65', '40-66', '40-67', '41-67', '41-68', '41-69', '42-69', '42-70']

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='?',intents=discord.Intents.all())
messages_to_delete = {}

def connect_data_base(name):
	BASE_DIR = os.path.dirname(os.path.abspath(__file__))
	db_path = os.path.join(BASE_DIR, name+".db")

	if not os.path.exists(name+".db"):
		example = os.path.join(BASE_DIR, "example_to_copy.db")
		shutil.copy(example,db_path)

	return SQLighter(db_path)

def level_exp_cacl(level):
	exp = 0
	for i in range(level+1):
		exp += (5 * i**2 + 50 * i + 100)

	return exp

async def change_exp(user, exp, db=None):
	user[4] = user[4]+exp
	db.update_user(user[2],{'exp':user[4]})
	return await check_level(user, db=db)

async def send_message(text, channel=676122065157488702):
	channel = bot.get_channel(channel)
	message = await channel.send(text)
	messages_to_delete[message] = 60

async def send_embed(embed, channel=676122065157488702, view=None):
	embed = discord.Embed(description=embed, colour = discord.Colour.from_rgb(0, 255, 128))
	channel = bot.get_channel(int(channel))
	message = await channel.send(embed=embed, view=view)
	messages_to_delete[message] = 60

def next_date_create(level):
	if level > 100:
		level = 100
	return datetime.now() + timedelta(seconds=randint(int(timer_level[level].split('-')[1])*60,int(timer_level[level].split('-')[1])*60))

async def check_level(user, db):
	level,exp,exp_for_level = user[3:]
	old_level = level
	if exp < 0:
		exp = 0 
	
	while exp > exp_for_level:
		level += 1
		exp_for_level = level_exp_cacl(level)

	while exp < level_exp_cacl(level-1):
		level -= 1
		exp_for_level = level_exp_cacl(level)

	db.update_user(user[2],{'level':level,'exp_for_next_level':exp_for_level,'next_message_date':next_date_create(level)})

	if level != old_level:
		dis_user = bot.get_user(int(user[2]))
		if level > old_level:
			answer = 'Поздравляю, '+dis_user.mention+', ты повысил уровень эволюции!'+f' Твоя эволюция {level} ранга!'

			channel = db.find_channel('level')

			if channel:
				await send_embed(answer, channel)
			else:
				await send_embed(answer)

		player = db.get_player(user[2])
		player.level = level

		db.update_player(user[2], player)
		#await send_message('Поздравляю, '+dis_user.mention+', ты повысил уровень эволюции!'+f' Твоя эволюция {level} ранга!')
	
	else:
		level = None
	
	return level


def declination(root,num,ending):
	if num >= 100:
		num %= 100
	
	if num > 10 and num <= 20:
		return root+ending[-1]
	
	num %= 10
	
	if num == 1:
		return root+ending[0]

	elif num <= 5 and num > 1:
		return root+ending[1]
	else:
		return root+ending[2]

async def bind(message, db):
	text = message.content

	if len(text.split()) == 3:
		id_ = text.split()[1]
		name = text.split()[2]

		db.add_role(name, id_)

		await send_message('Роль привязана', message.channel.id)
	
	elif len(text.split()) == 2:
		text = text.split(' ')[1]

		db.add_channel(text, message.channel.id)

		await send_message('Канал успешно привязан', message.channel.id)

async def stamina(member, message, db=None):
	arg = message.content.split()[1]
	print(arg)
	player = db.get_player(member.id)
	if arg == 'full':
		player.energy += Energy(100)
	elif arg.replace('+','').replace('-','').isnumeric():
		player.energy += Energy(int(arg))

	db.update_player(player.id, player)

	await send_embed('Выносливоcть изменена', message.channel.id)


async def battle_over(member, message, db=None):
	player = db.get_player(member.id)
	player.in_battle = False
	db.update_player(player.id, player)

	await send_embed('Вне битвы', message.channel.id)

async def change_exp_command(member, message, db=None):
	data = ''.join(message.content.split()[1:]).replace('+','').replace('- ','-')
	data = re.search('[\+\-]*\d+', data).group(0).strip()
	print('exp is', data)
	user = db.get_user(member.id)
	await change_exp(user,int(data), db=db)
	await send_embed('У '+member.mention+' опыт был успешно изменён', channel=message.channel.id)

async def know_exp(member, message, db=None):
	if member.id == message.author.id:
		ds_user = 'У вас '
	else:
		ds_user = 'У '+str(member.mention)+' '
	
	user = db.get_user(member.id)

	await send_embed(ds_user+str(user[4])+' '+declination('опыт',int(user[4]),['','а','а']), channel=message.channel.id)

	return

async def mute():
	pass

async def get_attr(message, db):
	attrs = [Fire,Ice,Wind,Earth,Lightning,Plants,Light,Darkness]
	attr = attrs[int(message.content.split()[1])]()
	user = db.get_user(message.author.id)
	player = db.get_player(message.author.id)
	player.magic_attribute = attr
	player.set_stats()
	db.update_player(message.author.id, player)
	await send_embed('Атрибут {} успешно приобритён'.format(attr.name), message.channel.id)

async def buy(message, db):
	attrs = [Fire,Ice,Wind,Earth,Lightning,Plants,Light,Darkness]
	id_ = message.content.split()[1]
	channel_id = db.find_channel('shop')
	if not channel_id or message.channel.id != int(channel_id):
		return

	user = db.get_user(message.author.id)
	player = db.get_player(message.author.id)
	
	if id_.isnumeric():
		item = get_items()[int(id_)]
		if not 'price' in item.__dict__ or item.price.value == 0:
			return
		
		if int(user[4]) >= item.price.value:
			player.add(item)
			await change_exp(user,item.price.value*-1, db=db)
			db.update_player(message.author.id, player)

			await send_embed(f'Предмет {id_} успешно куплен', message.channel.id)
		else:
			await send_embed(f'Недостаточно средств', message.channel.id)
	
	elif id_ == 'attr':
		if player.magic_attribute.name == 'нет':
			price = 10000
		else:
			price = 100000

		print(int(user[4]) >= price)

		if int(user[4]) >= price:
			await change_exp(user,price*-1, db=db)
			attr = attrs[random.randint(0,len(attrs)-1)]()
			player.magic_attribute = attr
			player.set_stats()
			db.update_player(message.author.id, player)
			await send_embed('Атрибут {} успешно приобритён'.format(attr.name), message.channel.id)
		else:
			await send_embed(f'Недостаточно средств', message.channel.id)

async def sell(message, db):
	id_ = message.content.split()[1]
	channel_id = db.find_channel('shop')
	if not channel_id or message.channel.id != int(channel_id):
		return

	if id_.isnumeric():
		user = db.get_user(message.author.id)
		player = db.get_player(message.author.id)
		item = get_items()[int(id_)]
		if not 'price' in item.__dict__ or item.price.value == 0:
			return
		
		if player.delete(int(id_)):
			await change_exp(user,item.price.value*0.5, db=db)
			db.update_player(message.author.id, player)

			await send_embed(f'Предмет {id_} успешно продан', message.channel.id)
	
async def show(message, attr, db):
	player = db.get_player(message.author.id)
	data = str(getattr(player,attr))
	
	await send_embed(data, message.channel.id)

async def equip(message, db):
	text = message.content.split()[1]
	if text.isnumeric():
		player = db.get_player(message.author.id)
		if player.equip(int(text)):
			db.update_player(message.author.id, player)
			await send_embed(f'Предмет надет', message.channel.id)

async def use(message, db):
	text = message.content.split()[1]
	
	if text.isnumeric():
		player = db.get_player(message.author.id)
		if player.use_consumables(int(text)):
			db.update_player(message.author.id, player)
			await send_embed(f'Израсходовано', message.channel.id)

async def stats(message, member=None, db=None):
	text = ''
	player = db.get_player(member.id)
	
	await send_embed(str(player), message.channel.id)

async def take(member, message, db):
	attrs = [Fire,Ice,Wind,Earth,Lightning,Plants,Light,Darkness]
	player = db.get_player(member.id)
	if 'attr' in message.content:
		name = 'Атрибут'
		id_ = ''
		player.magic_attribute = magic_attribute()
	else:
		id_ = int(message.content.split()[1])
		item = get_items()[id_]
		player.delete(item.id)
		name = 'Предмет'
	
	db.update_player(member.id, player)

	await send_embed(name + f' {id_} успешно забран', message.channel.id)

async def give(member, message, db):
	attrs = [Fire,Ice,Wind,Earth,Lightning,Plants,Light,Darkness]
	player = db.get_player(member.id)
	if 'attr' in message.content:
		id_ = int(message.content.split()[2])
		name = 'Атрибут'
		player.magic_attribute = attrs[id_]()
	else:
		id_ = int(message.content.split()[1])
		item = get_items()[id_]
		player.add(item)
		name = 'Предмет'
	db.update_player(member.id, player)

	await send_embed(name + f' {id_} успешно отдан', message.channel.id)

def last_raid_in_time(last_raid, reverse=False, max_=0):
	if not last_raid:
		return None
	
	if not reverse: 
		last_raid = (datetime.now() - last_raid).seconds
	else:
		last_raid = max_ - (datetime.now() - last_raid).seconds
	
	if last_raid < 60:
		return '{} {}'.format(last_raid,declination('секунд', last_raid, ['а', 'ы', '']))
	elif last_raid < 3600:
		minutes = last_raid//60
		seconds = last_raid%60
		
		return '{} {} {} {}'.format(minutes, declination('минут', minutes, ['а', 'ы', '']), seconds ,declination('секунд', seconds, ['у', 'ы', '']))
	else:
		return None


async def replay(interaction, battle, is_fav=False, db=None):
	async def add_to_fov(interaction):
		player = db.get_player(interaction.user.id)
		if not battle[0].id in player.favorite:
			player.favorite.append(battle[0].id)
			db.update_player(interaction.user.id, player)
			channel = interaction.channel
			message = await send_embed('Добавлено', channel.id)
			await interaction.response.edit_message(embed=interaction.message.embeds[0])

		return

	async def change_str(interaction):
		buttons = []
		view=View(timeout=None)
		data = []
		
		if battle_index[0] > 0:
			data += [['first','<<-', 1, first_callback], ['back', '<-', 1, back_callback]]
		
		if battle_index[0] < len(battle[0].history)-1:
			data += [['next', '->', 1, next_callback], ['last', '->>', 1, last_callback]]	

		if not is_fav:
			data += [['add_fov', 'В избранное⭐', 2, add_to_fov]]

		for element in data:
			button = Button(custom_id=element[0], label=element[1], row=element[2], style=discord.ButtonStyle.green)
			button.callback = element[3]
			view.add_item(button)

		embed = discord.Embed(description=battle[0].history[battle_index[0]], colour = discord.Colour.from_rgb(0, 255, 128))

		if not interaction.response.is_done():
			await interaction.response.edit_message(embed=embed, view=view )
		else:
			await interaction.message.edit(embed=embed, view=view)

		messages_to_delete[interaction.message] = 60*20
		
		return

	async def back_callback(interaction):
		battle_index[0] -= 1
		await change_str(interaction)

	async def next_callback(interaction):
		battle_index[0] += 1
		await change_str(interaction)

	async def first_callback(interaction):
		battle_index[0] = 0
		await change_str(interaction)

	async def last_callback(interaction):
		battle_index[0] = len(battle[0].history) - 1 
		await change_str(interaction)

	battle_index = [len(battle.history)-1]
	battle = [battle]
	await change_str(interaction)

async def menu(message, member, db):
	menu_buttons = [['equipment','Инвентарь'],['stats','Харак-ки'],['replays','Повторы']]

	async def menu_callback(interaction):
		if interaction.user != message.author:
			return
		custom_id = interaction.data['custom_id']
		view = View()

		text = ''
		buttons = []
		print(custom_id)
		if custom_id == 'menu':
			premium = 'да' if player.premium else 'нет'
			text = main_text
			buttons = menu_buttons
		
		elif custom_id == 'equipment':
			text = 'Снаряжение: \n'+str(player.equipment)+'\n'+str(player.consumables)
			buttons = [['menu', 'Назад'], ['different', '<-'], ['bag', '->']]
		elif custom_id == 'bag':
			text = 'Сумка: \n'+str(player.inventory)+'\n'+str(player.bag)
			buttons = [['menu', 'Назад'], ['equipment', '<-'], ['runes', '->']]
		elif custom_id == 'runes':
			text = 'Руны: \n' + str(player.runes)
			buttons = [['menu', 'Назад'], ['bag', '<-'], ['different', '->']]
		
		elif custom_id == 'different':
			text = 'Другое: \n' + str(player.different)
			buttons = [['menu', 'Назад'], ['runes', '<-'], ['equipment', '->']]

		elif custom_id == 'stats':
			text = str(player)
			buttons = [['menu', 'Назад']]
		
		elif custom_id == 'replays':
			battles = db.get_battles()
			text = ''
			buttons = [['menu', 'Назад']]

			for battle_ in battles:
				if battle_[0] in player.favorite:
					text += str(battle_[0])+'. '+str(battle_[-1])+'\n\n'
					buttons.append(['replay'+str(battle_[0]),str(battle_[0])])

		elif 'replay' in custom_id:
			battles = db.get_battles()
			custom_id = custom_id.replace('replay', '')
			for battle_ in battles:
				if battle_[0] == int(custom_id):
					await replay(interaction, battle_[-1], is_fav=True, db=db)
					return
		
		text = text.replace('\nНет предметов','')
		if len(text.splitlines()) == 1:
			text += '\nНет предметов'
		
		for button in buttons:
			button = Button(custom_id=button[0], label=button[1], style=discord.ButtonStyle.green)
			button.callback = menu_callback
			view.add_item(button)
		
		embed = discord.Embed(description=text, colour = discord.Colour.from_rgb(0, 255, 128))
		await interaction.response.edit_message(embed=embed, view=view)
		messages_to_delete[interaction.message] = 60*5

	
	button = Button(custom_id='button1', label='Начать!', style=discord.ButtonStyle.green)

	#await message.channel.send('Битва '+player.name+' с боссом '+boss.name, view=View().add_item(button))
	view = View(timeout=None)
	player = db.get_player(member.id)
	user = db.get_user(player.id)
	premium = 'да' if player.premium else 'нет'
	main_text = '{}\n Уровень — {}\n Опыт — {} / {}\n Выносливоcть — {}\n Премиум — {}\n\n'.format(player.name,player.level,user[4],user[5],player.energy,premium)
	last_raid = last_raid_in_time(player.last_raid)

	if last_raid:
		main_text +=  f"Последний рейд — {last_raid} назад"
	embed = discord.Embed(description=main_text, colour = discord.Colour.from_rgb(0, 255, 128))
	all_stats = None
	buttons = menu_buttons

	for button in buttons:
		button = Button(custom_id=button[0], label=button[1], style=discord.ButtonStyle.green)
		button.callback = menu_callback
		view.add_item(button)
	
	new_message = await message.channel.send(embed=embed, view=view)
	messages_to_delete[new_message] = 60*5


async def raid_limit(member,message,db):
	player = db.get_player(member.id)
	value = int(message.content.split(' ')[1])
	if value == 0:
		player.raid_limit = False
		end = 'выключено'
	else:
		player.raid_limit = True
		end = 'включено'
	db.update_player(player.id, player)
	await send_embed(f'Ограничение {end}')

async def duel(message, mentions=[], db=None):
	await do_battle(message,mentions=mentions, db=db, boss=None)

async def delete_message_on_time(message,time:int):
	time = datetime.now() + timedelta(seconds=time)

	while True:
		if datetime.now() >= time:
			await message.delete()
			return

		await asyncio.sleep(5)


async def raid(message, mentions=[],  db=None):
	if not message.content.split()[1].isnumeric():
		return

	await do_battle(message,mentions=mentions, db=db, boss=message.content.split()[1])

async def trade(member, message, db):
	async def accept_callback(interaction):
		if interaction.user in should_accept and interaction.user not in accepted:
			accepted.append(interaction.user)
			embed = discord.Embed(description=interaction.message.embeds[0].description+'\n {} согласен!'.format(interaction.user.mention), colour = discord.Colour.from_rgb(0, 255, 128))
			await interaction.response.edit_message(embed=embed, view=view)
			messages_to_delete[interaction.message] = 60*3

		for user in should_accept:
			if not user in accepted:
				return

		message = interaction.message
		take_user = db.get_user(member.id)

		if deal == 'give':
			if give_user[4] >= full_exp:
				await change_exp(take_user,exp,db)
				await change_exp(give_user,full_exp*-1,db)
				answer = 'Опыт передан!'
			else:
				answer = 'Недостаточно опыта'
		
		elif deal == 'trade':
			take_player = db.get_player(take_user[2])
			give_player = db.get_player(give_user[2])
			
			if take_user[4] < full_exp:
				answer = 'У пользователя недостаточно опыта для покупки'
			elif int(id_) not in give_player.ids:
				answer = 'У вас нет такого предмета'
			else:
				await change_exp(take_user,full_exp*-1,db)
				give_player.delete(id_)
				take_player.add(get_items()[id_])
				db.update_player(give_player.id, give_player)
				db.update_player(take_player.id, take_player)

				answer = 'Трейд совершен!'

		embed = discord.Embed(description=answer, colour = discord.Colour.from_rgb(0, 255, 128))

		await message.edit(embed=embed, view=None)
		messages_to_delete[message] = 60*2

	
	text = str(message.content)
	accepted = []
	view = View(timeout=None)
	give_user = db.get_user(message.author.id)
	
	for mention in message.mentions:
		text = text.replace(mention.mention,'').strip()
	
	if len(text.split()) == 2:
		full_exp = int(text.split()[1])
		if int(give_user[4]) >= int(full_exp):
			exp = int(full_exp*0.8)
			answer = 'С учётом комисии вы переведёте {} пользователю {}. Вы согласны?'.format(exp, member.mention)
			should_accept = [message.author]
			
			button = Button(custom_id='accept', label='Согласен', row=1, style=discord.ButtonStyle.green)
			button.callback = accept_callback
			view.add_item(button)
			deal = 'give'
		
		else:
			answer = 'Недостаточно средств'

	elif len(text.split()) == 3:
		id_, full_exp = message.content.split()[1:3]
		full_exp, id_ = int(full_exp), int(id_)
		take_user = db.get_user(member.id)
		
		player = db.get_player(message.author.id)

		if int(id_) not in player.ids:
			answer = 'У вас нет такого предмета'
		elif int(take_user[4]) < full_exp:
			answer = 'У пользователя недостаточно опыта для покупки'
		else:
			exp = int(full_exp*0.8)
			answer = 'С учётом комисии вы продадите предмет {} пользователю {} за {}, ваша выручка {}. Вы согласны?'.format(id_,member.mention, full_exp, exp)
			should_accept = [message.author, member]
			
			button = Button(custom_id='accept', label='Согласен', row=1, style=discord.ButtonStyle.green)
			button.callback = accept_callback
			view.add_item(button)
			deal = 'trade'
	
	embed = discord.Embed(description=answer, colour = discord.Colour.from_rgb(0, 255, 128))

	message = await message.channel.send(embed=embed, view=view)
	messages_to_delete[message] = 60*5

	return

async def do_battle(message, mentions=[], db=None, boss=None):
	accepted = []
	buttons = []
	if not message.author in mentions:
		mentions = [message.author] + mentions
	
	if boss:
		if len(mentions) > 4:
			return
		bosses = get_items('bosses')

		if not int(boss) in bosses:
			return

		boss = bosses[int(message.content.split()[1])]
	
	elif len(mentions) != 2:
		return

	async def cancel_battle(edit, player, text):
		embed = discord.Embed(description=text, colour = discord.Colour.from_rgb(0, 255, 128))
		message = await edit(embed=embed,view=View(timeout=None))
		messages_to_delete[message] = 40
		return message


	async def battle_callback(interaction):
		async def end_battle(edit, reward=True):
			text = battle.message+'\n'
			survived_players = battle.players[:]
			battle.sort()
		
			if survived_players != [] and boss.id in drop and reward:
				exp = randint(drop[battle.boss.id]['minExp'], drop[battle.boss.id]['maxExp'])
			else:
				exp = 0

			exp //= len(battle.players)
			
			for player in battle.members:
				if not type(player) == Boss:
					db_player = db.get_player(str(player.id))
					db_player.clear('consumables')
					text += db_player.name
					energy = 10
					
					if player not in survived_players:
						db_player.clear('runes')
						energy += 10
						
					elif survived_players != [] and player == survived_players[0] and battle.boss and reward and int(battle.boss.id) in drop and boss.id in drop and 'rune' in drop[boss.id]:
						if battle.boss and randint(1,100) <= drop[battle.boss.id]['chance']:
							rune = get_items()[drop[battle.boss.id]['rune']]
							db_player.add(rune)
							
							text += ' Получено '+rune.name+'.'

					if not player.last_raid_ready and battle.boss:
						energy = 50

					if exp > 0:
						exp *= player.multiplyer.value/100
						exp = int(exp)
						level = await change_exp(db.get_user(db_player.id), exp, db=db)
						text += f' получено {exp} опыта.'

						if level:
							db_player.level = level
							text += f" Получен новый уровень!"
						
					else:
						text += ' опыт не получен.'
					
					text += f' Потрачено  🔋{energy}.'
					db_player.energy -= energy

					text += '\n'
					
					db_player.in_battle = False
					db_player.last_energy_updated = datetime.now()

					if battle.boss:
						db_player.last_raid = datetime.now()

					db.update_player(player.id, db_player)

			view = None				
			id_ = db.add_battle(battle)
			print(id_)
			battle.id = id_
			battle.history[-1] = text
			
			embed = discord.Embed(description=text, colour = discord.Colour.from_rgb(0, 255, 128))
			await edit(embed=embed,view=view)
			await replay(interaction, battle, db=db)
			return

	
		async def close_on_time(message):
			while True:
				if (datetime.now() >= time_to_exit[0]) and not battle.is_over:
					if battle.move == 0:
						return
					
					count = 0
					while not battle.is_over:
						battle.next()
						count += 1
					
					if count > 10:
						reward = False
					else:
						reward = True
					
					await end_battle(message.edit, reward=reward)
					return

				await asyncio.sleep(3)
		buttons = []

		#Код битвы
		if mentions != []:
			if interaction.user in mentions and interaction.user not in accepted:
				accepted.append(interaction.user)
				text = interaction.message.embeds[0].description

			if not len(accepted) == len(mentions):
				view = View(timeout=None)

				for user in accepted:
					player = db.get_player(user.id)
					
					if player.in_battle:
						text += user.mention+' Не может участовать в бою, так как уже в сражении'
						messages_to_delete[interaction.message] = 30
						break
					else:
						text += ' '+user.mention+' Готов! '
				else:		
					button = Button(custom_id='battle_button', label='Начать!', style=discord.ButtonStyle.green)
					button.callback = battle_callback
					embed = discord.Embed(description=text, colour = discord.Colour.from_rgb(0, 255, 128))
					view = View(timeout=None).add_item(button)
				
				await interaction.response.edit_message(embed=embed, view=view)
				messages_to_delete[interaction.message] = 60*3
				return
		
		if battle.move == 0:
			for player in battle.players:
				player = db.get_player(player.id)
				if player.in_battle:
					text = 'Битва не может быть начата, так как игрок {} уже находится в сражении.'.format(player.name)
					await cancel_battle(interaction.response.edit_message, player, text)
					messages_to_delete[interaction.message] = 30
					return
			
			for player in battle.players:
				player = db.get_player(player.id)
				player.in_battle = True
				player.last_raid = datetime.now()
				db.update_player(player.id,player)	

			battle.history.append(interaction.message.embeds[0].description)
			task = asyncio.create_task(close_on_time(interaction.message))

		buttons = []
		battle.next()
		
		battle_index[0] = len(battle.history)-1
		time_to_exit[0] = datetime.now()+timedelta(seconds=60*20)
		await not_delete(interaction.message)
		view = View(timeout=None)

		if not battle.is_over:
			button = Button(custom_id='battle', label='Дальше!', style=discord.ButtonStyle.green)
			button.callback = battle_callback
			buttons.append(button)
		else:
			await end_battle(interaction.response.edit_message)
			return
	

		for button in buttons:
			view.add_item(button)
		
		#battle.boss.health = Health(0)
				
		embed = discord.Embed(description=battle.message, colour = discord.Colour.from_rgb(0, 255, 128))

		await interaction.response.edit_message(embed=embed, view=view)
		
	battle_index = [-1]
	time_to_exit = [datetime.now()+timedelta(seconds=3*60)]
	battle_button = Button(custom_id='start_button', label='Начать!', style=discord.ButtonStyle.green)
	battle_button.callback = battle_callback
	
	players = []

	added_users = []

	for user in mentions:
		player = db.get_player(user.id)
		cancel = False

		if player.in_battle:
			text = 'Битва не может быть начата, так как игрок {} уже находится в сражении.'.format(player.name)
			cancel = True

		elif player.energy.value <= 49:
			if player.energy.value <= 30:
				text = 'Битва не может быть начата, так как у игрока {} накопилась усталость 😪'.format(player.name)
			elif not player.last_raid_ready and boss:
				text = 'Прошло слишком мало времени с последнего рейда {}'.format(player.name)
			else:
				cancel = False

		if not cancel and boss and user.id == message.author.id and player.raid_limit:
			last_raid_call = last_raid_in_time(player.last_raid_call, reverse=True, max_=60*3)
			if last_raid_call and (datetime.now() - player.last_raid_call).seconds < 60*3:
				text = f'Вы не можете вызывать рейд чаще чем в три минуты, осталось {last_raid_call}'
				cancel = True
			else:
				player.last_raid_call = datetime.now()
				db.update_player(player.id, player)

		if cancel:
			await cancel_battle(message.channel.send, player, text)
			return
	
		if not user in added_users:
			players.append(player)
			added_users.append(user)
	
	if boss:
		if len(mentions) > 1:
			boss.start_health = Health(int(boss.health.value + 0.5*boss.health.value*(len(mentions)-1)))
			boss.health = boss.start_health
		text = 'Рейд!👾\n'
		battle = Battle(boss, *players)
	else:
		text = 'Дуэль⚔️\n'
		battle = Battle(*players)
	
	text = "Место действие: {} / Условие: {}\n\n".format(battle.arena.name,battle.weather.name)

	for player in battle.members:
		text += player.name+': Здоровье - '+str(player.health)+', Урон - '+str(player.damage)
		if type(player) != Boss:
			text += ',  🔋{}/100'.format(str(player.energy))
			
			if battle.boss and not player.last_raid_ready:
				text += '\n\n Предупреждение: с последнего рейда игрока {} прошло слишком мало времени. Вы уверены, что хотите сразиться? Штраф усталости 50.\n\n'.format(player.name)

		text += '\n'	

	#await message.channel.send('Битва '+player.name+' с боссом '+boss.name, view=View().add_item(button))
	embed = discord.Embed(description=text, colour = discord.Colour.from_rgb(0, 255, 128))

	new_message = await message.channel.send(embed=embed, view=View(timeout=None).add_item(battle_button))
	messages_to_delete[new_message] = 60*3

	return

async def do_command(message):
	db = connect_data_base(message.guild.name)
	prefix = bot_data['prefix']
	user = db.get_user(message.author.id)
	await check_level(user, db=db)
	
	show_data = {'runes':'runes', 'eq':'equipment', 'inv':'inventory', 'cons':'consumables', 'diff':'different','bag':'bag'}
	try:
		member_commands = {'exp':know_exp, 'str':stats, 'equip':equip, 'sell':sell, 'raid':raid, 'attr':get_attr,'menu':menu, 'duel':duel,'use':use, 'trade':trade, 'buy':buy}
		admin_commands = {'ban':message.guild.ban, 'mute':mute, 'give':give, 'take':take, 'e':change_exp_command, 'bind':bind, 'stamina':stamina, 'battle_over':battle_over, 'raid_limit':raid_limit}
		self_or_others_command = ['exp','e','str', 'stamina', 'battle_over', 'give', 'take', 'menu','trade', 'raid_limit']
		commands = member_commands
		command = message.content.split()[0]

		mentions = message.mentions

		if message.reference:
			reply_mess = await message.channel.fetch_message(message.reference.message_id)
			reply_user = reply_mess.author
			if not reply_user in mentions:
				mentions.append(reply_user)

		if command[0] == prefix and command[1:] in list(admin_commands.keys())+list(member_commands.keys()):
			command = command[1:]
			if command in admin_commands.keys():
				roles = db.find_roles('admin')
				print(roles)
				if roles:
					for role in message.author.roles:
						if role.id in roles:
							member_commands = member_commands | admin_commands
							break
					else:
						return
				else:
					member_commands = member_commands | admin_commands
			print(command)
			if mentions == []:
				if command in self_or_others_command:
					await member_commands[command](member=message.author, message=message, db=db)
					return
			
			if command == 'raid':
				await raid(message, mentions, db=db)
				return

			if command == 'duel':
				await duel(message, mentions, db=db)
				return
			
			if command in self_or_others_command:
				for user_ in message.mentions:
					try:
						await member_commands[command](member=user_,message=message, db=db)
					except:
						traceback.print_exc()
			else:
				await member_commands[command](message=message, db=db)
				return
		
		elif command in show_data:
			await show(message, show_data[command], db=db)


	except:
		traceback.print_exc()
		return True



@bot.event
async def on_message(message):	
	prefix = bot_data['prefix']
	db = connect_data_base(message.guild.name)
	print(message.author.id, message.content)
	if message.author == bot.user:
		return
	
	
	if not db.user_exists(message.author.id):
		db.add_user(message.author.id,datetime.now()+timedelta(seconds=randint(4*60,7*60)))
		new_player = Player(message.author.id, message.author.mention, 155)
		new_player.add(get_items()[0])
		db.add_player(message.author.id, new_player)
		return


	if message.content[0] == prefix:
		await do_command(message)
		print('hiiiiiiiiiiii')
		return
	
	user = db.get_user(message.author.id)

	if datetime.now() >= user[1]:
		user[4] += randint(15,25)
		db.update_user(user[2],{'exp':user[4]})
		
		if not await check_level(user, db=db):
			db.update_user(user[2],{'next_message_date':next_date_create(user[3])})

@bot.event
async def on_ready():
	await delete_messages()

async def delete_messages():
	sleep = 5
	
	while True:
		try:
			ids = []
			await asyncio.sleep(sleep)

			for i in range(len(messages_to_delete)-1, -1, -1):
				message = list(messages_to_delete.keys())[i]
				messages_to_delete[message] -= sleep
				if message.id not in ids:
					if messages_to_delete[message] <= 0:
						await message.delete()
						del messages_to_delete[message]
						ids.append(message.id)
						break
				else:
					del messages_to_delete[message]
					break
		except:
			traceback.print_exc()
			continue

async def not_delete(message):
	while True:
		for message_ in messages_to_delete:
			if message.id == message_.id:
				del messages_to_delete[message_]
				break
		else:
			break

@bot.event
async def on_member_join(member):
	db = connect_data_base(member.guild.name)
	if not db.user_exists(member.id):
		db.add_user(member.id,datetime.now()+timedelta(seconds=randint(4*60,7*60)))
		new_player = Player(member.id,member.mention, 155)
		new_player.add(get_items()[0])
		db.add_player(member.id, new_player)
		await send_embed('Добро пожаловать, '+member.mention)

if __name__ == '__main__':
	global prefix
	prefix = bot_data['prefix']
	#$task = asyncio.create_task(delete_messages())
	bot.run(bot_data['token'])

#print(level_exp_cacl(20))