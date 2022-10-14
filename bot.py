# -*- coding: utf-8 -*-
import traceback
import requests
import json
import os
import copy
from sql import SQLighter
from threading import Thread
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove,ReplyKeyboardMarkup, KeyboardButton
from time import sleep
from config import token

from parserwb_ozon import start_parse,start_loop,regions,add_competitor_shop

bot = Bot(token=token)
dp = Dispatcher(bot)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "db.db")

db = SQLighter(db_path)

first_button = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Начать'))
shared_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Добавить пользователя')).add(KeyboardButton('Удалить пользователя')).add(KeyboardButton('Главное меню'))
start_buttons = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Отчёт о позициях товаров'),KeyboardButton('Отслеживание цен и и наличия товаров')).add(KeyboardButton('Аккаунт компании'))
start_buttons_goods = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Получить отчёт')).add(KeyboardButton('Редактировать'),KeyboardButton('Добавить товар')).add(KeyboardButton('Главное меню'))
start_buttons_copetitor = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Отслеживание всех товаров магазина')).add(KeyboardButton('Добавить товар на отслеживание'),KeyboardButton('Список отслеживаемых товаров и их удаление')).add(KeyboardButton('Главное меню'))

edit_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Редактировать поисковые запросы')).add(KeyboardButton('Удалить товар')).add(KeyboardButton('Назад'))
edit_search_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Добавить новый')).add(KeyboardButton('Назад'))

admin_chats = ['340549861','618939593']



def get_admin_data():
	with open(f'admin_data.json','r',encoding='utf-8-sig') as file:
		admin_data = json.loads(file.read())

	return admin_data

def save_admin_data(admin_data):
	with open(f'admin_data.json','w',encoding='utf-8-sig') as file:
		file.write(json.dumps(admin_data))

def get_products(chat_id='',name=''):
	print('name is ',name)
	if not 'products' in name:
		name = f'products{name} {chat_id}.json'
	
	with open(f'products/{name}','r',encoding='utf-8-sig') as file:
		products = json.loads(file.read())

	return products

def users_string(amount):
	if amount > 9:
		amount %= 10
	
	if amount == 1:
		return 'пользователь'
	elif amount < 5:
		return 'пользователя'
	else:
		return 'пользователей'

def human_string(amount):
	if amount > 9:
		amount %= 10
	
	if amount > 1 and amount < 5:
		return 'человека'
	else:
		return 'человек'

def get_info():
	registred_users = db.get_users()
	users = []
	users_search = []
	users_products = []
	searches = []
	products = []
	shops_users = 0
	admin_data = get_admin_data()

	for filename in os.listdir("products"):
		with open(os.path.join("products", filename), 'r',encoding='utf-8-sig') as f:
			data = get_products(name=filename)
			if data == [] or data == {}:
				continue

			if 'shop' in filename:
				shops_users += 1
				continue
			if not filename.split()[1] in users:
				users.append(filename.split()[1])

			print(filename)
			if not '_competive' in filename:
				print(data)
				for product in data:
					print(product)
					if 'search' in product:
						for search in product['search']:
							if not search in searches:
								searches.append(search)
					else:
						searches.append(product['url'])
				
				if not filename.split()[1] in users_search:
					users_search.append(filename.split()[1])
			else:
				for product in data:
					if not product in products:
						products.append(product)
				if not filename.split()[1] in users_products:
					users_products.append(filename.split()[1])

	strings = ['1. В боте зарегистрировано пользователей - ','2. Активных пользователей - ','3.Пользователей,которые имеют запросы на отслеживании - ','4.Пользователей,которые имеют товары на отслеживании - ','5. Всего запросов отслеживается - ','6. Всего товаров отслеживается - ','7. Людей отслежиают магазины - ']
	data = [registred_users,users,users_search,users_products,searches,products,shops_users]
	admin_keys = list(admin_data.keys())
	info = ''
	
	for i in range(len(strings)):
		if isinstance(data[i], list):
			amount = len(data[i])
		else:
			amount = data[i]
		diff = amount - int(admin_data[admin_keys[i]])
		end = '🟢' if diff >= 0 else '🔴'
		sybmol = '+' if int(diff) >= 0 else ''

		end = f'({sybmol}{diff}) {end}'

		info += strings[i]+str(amount)+end+'\n'
		admin_data[admin_keys[i]] = amount

	save_admin_data(admin_data)
	
	return info

def save_products(products,chat_id,name=''):
	print('saving')
	with open(f'products/products{name} {chat_id}.json','w',encoding='utf-8-sig') as file:
		file.write(json.dumps(products))

async def post(message):
	users = db.get_users()

	for user in users:
		user = user[0]
		if not os.path.exists('photo.png'):
			await bot.send_message(chat_id=user,text=message)
		else:
			with open('photo.png', 'rb') as photo:
				await bot.send_photo(chat_id=user,caption=message,photo=photo)
			

@dp.message_handler(content_types=['text','document','photo'])
async def answer_message(message,text='',chat_id=''):
	start_message = 'Выберите действие'
	first_message = "Привет! Этот бот будет тебе очень полезен, вот что он умеет:\n\n\n1. Может взять ваш магазин на отслеживание и уведомлять когда цена товара изменилась, либо он выпал из наличия. Это застрахует вас от ошибок в выставлении цен и поможет контролировать правильность действий ваших сотрудников, а также поможет вовремя среагировать на неожиданное выпадение товара из наличия по какой-либо причине\n\n2. Поможет отслеживать движения ваших товаров в поисковой выдаче WildBerries. Полезно знать как растёт ваш товар при его продвижении и иметь возможность быстро среагировать, если позиции вашего товара начали падать. Бот также поможет в SEO оптимизации, благодаря ему вы будете знать появился ли товар в поиске по нужным вам запросам или неожиданно пропал из поиска\n\n3. Покажет выдачу с различных регионов. Ваш товар может быть в топе, например, в Москве, но в Екатеринбурге в самом низу выдачи. Бот поможет вам выстроить вашу стратегию распределения товара по региональным складам\n\n4. Бот-помощник позволяет следить за действиями ваших конкурентов, сообщая когда они меняют цену или их товар выпадает из наличия. Просто добавьте товар конкурента на отслеживание и мгновенно реагируйте на любые его действия, повышайте цену когда он выпадает из наличия и вовремя замечайте изменения среднерыночной цены на ваш товар"
	start_buttons = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Отчёт о позициях товаров'),KeyboardButton('Отслеживание цен и и наличия товаров')).add(KeyboardButton('Аккаунт компании'),KeyboardButton('Настройки'))
	
	if chat_id == '':
		chat_id = message.chat.id 
		twice_chat_id = ''
	else:
		twice_chat_id = chat_id

	markets = ['Ozon','WildBerries']
	files = ['_wb','_wb_competive','_ozon','_shop']
	chat_id_products = chat_id

	if db.get_shared(chat_id) and 'shared' in db.get_shared(chat_id):
		chat_id_products =  db.get_shared(chat_id).split('_')[1]

	twice_answer = False
	twice_answer_text = ''


	if not db.user_exists(str(chat_id)):
		if message.from_user.username:
			db.add_user(str(chat_id),message.from_user.username)
		else:
			db.add_user(str(chat_id),message.from_user.first_name)

		db.update_status(chat_id,'first')

		await message.answer(first_message,reply_markup=first_button)
		return

	else:
		for file in files:
			print('products'+file+' '+str(chat_id)+'.json')
			if not os.path.exists('products/products'+file+' '+str(chat_id)+'.json'):
				blank = {} if ('competive' in file or 'shop' in file) else []
				save_products(blank,chat_id,file)

		if twice_chat_id == '':
			if message.from_user.username:
				if db.get_nick(chat_id) != message.from_user.username:
					db.add_nick_name(chat_id,message.from_user.username)
			else:
				if db.get_nick(chat_id) != message.from_user.first_name:
					db.add_nick_name(chat_id,message.from_user.first_name)
	
	status = db.get_status(chat_id)
	if text == '':
		text = message.text
	keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add('Главное меню')
	answer = ''
	
	save = False
	parse = False

	save_name = '_wb'
	products = get_products(chat_id_products,save_name)

	admin_rights = False

	if str(chat_id) in admin_chats:
		admin_rights = True
		start_buttons = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Отчёт о позициях товаров'),KeyboardButton('Отслеживание цен и и наличия товаров')).add(KeyboardButton('Аккаунт компании'),KeyboardButton('Настройки')).add(KeyboardButton('/info'),KeyboardButton('/post'))
	
	if text == 'Главное меню':
		if status != 'main':
			start_message = 'Выбор отменён,выберите действие'
		db.update_status(chat_id,'start')
		await message.answer(start_message,reply_markup=start_buttons)
		return

	elif text == '/start':
		db.update_status(chat_id,'first')
		await message.answer(first_message,reply_markup=first_button)
		return

	if admin_rights:
		if message.text == '/info' and admin_rights:
			info = get_info()
			await message.answer(info,reply_markup=start_buttons)
			return

		elif message.text == '/post' and admin_rights:
			db.update_status(chat_id,'post')
			await message.answer('Введите сообщение для рассылки',reply_markup=keyboard)
			return
	
	if 'post' in status:
		if not 'start' in status:
			db.update_status(chat_id,'post start')
	
			if message.photo != []:
				await message.photo[-1].download('photo.png')
				text = message.caption
			elif os.path.exists('photo.png'):
				os.remove('photo.png')
			
			db.update_temp(chat_id,text)
			keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add('Да').add('Главное меню')
			await message.answer('Вы уверены,что хотите сделать рассыку этого сообщения?',reply_markup=keyboard)
		else:
			if text == 'Да':
				print('post')
				text = db.get_temp(chat_id)
				await post(text)
				await message.answer(start_message,reply_markup=start_buttons)
		return

	if status == 'first':
		keyboard = start_buttons
		answer = start_message
		db.update_status(chat_id,'start')
	elif status == 'start':
		if text == 'Отчёт о позициях товаров':
			keyboard = start_buttons_goods
			answer = 'После того как вы добавили товар, бот будет регулярно отчитываться о том как меняются его позиции\n\nОтчёт приходит после 10:00 по Мск с заданной периодичностью\n\nВы можете в любой момент изменить периодичность отчётов или запросить немедленное формирование отчёта'
			db.update_status(chat_id,'goods_main')
		elif text == 'Отслеживание цен и и наличия товаров':
			keyboard = start_buttons_copetitor
			answer = 'Бот предупредит вас когда конкурент сменит цену или его товар выпадет из наличия\n\n\nЭто важно, если ваш товар находится на первых местах в топе. Тогда действия конкурентов будут влиять на ваши продажи, а благодаря боту вы будете в курсе и быстро узнаете если ваш конкурент начнёт демпинговать или наоборот завысит цену, и сможете изменить свою цену, привлечь таким образом больше покупателей и продаж\n\n\nЭто же касается и моментов когда важный конкурент выпадает из наличия, в это время выгодно поднимать цены, ведь вам достанется больше покупателей\n\n\nТакже данный функционал можно использовать для отслеживания собственных цен. Чтобы убедиться в том что установлена правильная цена (помогает контролировать сотрудников и проверять себя), а также убедиться в том что скидка применилась и товар добавился в акцию'
			db.update_status(chat_id,'competitor_main')
		elif text == 'Аккаунт компании':
			keyboard = shared_keyboard
			answer = 'Вы можете добавить своего сотрудника в бот, чтобы вместе получать уведомления и работать с общим списком товаров. Для этого ваш сотрудник должен активировать бот, после чего вам нужно добавить его к своему аккаунту, указав ник в телеграм'
			db.update_status(chat_id,'shared_main')
		elif text == 'Настройки':
			keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Доавить регион/регионы'),KeyboardButton('Удалить регион/регионы')).add(KeyboardButton('Периодичность отчёта')).add(KeyboardButton('Главное меню'))
			answer = 'Выберите действие'
			db.update_status(chat_id,'settings choose')

	elif status == 'period':
		periods = [1,3,7,31]
		days_past = 0

		if not text.isnumeric() or int(text) > len(periods):
			answer = 'Не возможный вариант'
		else:
			days_max = periods[int(text)-1]
			db.update_user(days_max,days_past,chat_id)
			answer = 'Периодичность выставлена'
		db.update_status(chat_id,'start')
		keyboard = start_buttons

	if 'shared' in status:
		if 'main' in status:
			shared = db.get_shared(chat_id)

			if text == 'Добавить пользователя':
				if not shared or shared == '':
					answer = 'Введите username пользователя,которого хотите добавить'
					db.update_status(chat_id,'shared_add')
				else:
					answer = 'У вас уже есть аккаунт компании'
					db.update_status(chat_id,'start')

			elif text == 'Удалить пользователя':
				if shared and shared != '':
					if not 'shared' in shared:
						shared = shared.split()
						
						answer = 'Выберите пользователя,которго хотите удалить:\n\n'
					
						for i in range(len(shared)):
							answer += str(i+1)+'. '+db.get_nick(shared[i])+'\n'

						db.update_status(chat_id,'shared_delete')
					else:
						orgin_chat_id = shared.split('_')[1]
						db.add_shared(chat_id,'')
						shared_origin = db.get_shared(orgin_chat_id).split()
						print(shared_origin)
						db.update_status(orgin_chat_id,'shared_delete')
						twice_answer_text = str(shared_origin.index(str(chat_id))+1)
						twice_answer = True
						twice_chat_id = orgin_chat_id
						answer = 'Вы вышли из аккаунта компании'
						keyboard = start_buttons
						db.update_status(chat_id,'start')

				else:
					answer = 'У вас нет добавленых пользователей'
					db.update_status(chat_id,'start')

		elif 'add' in status:
			shared_chat_id = db.get_chat_from_nick(text)
			keyboard = start_buttons
			db.update_status(chat_id,'start')
			
			if shared_chat_id == []:
				answer = 'Этот пользователь не зарегистрирован или не активен'
			else:
				shared_chat_id = shared_chat_id[0]
				shared_origin = db.get_shared(chat_id)

				if not db.get_shared(shared_chat_id) or db.get_shared(shared_chat_id) == '':
					if not shared_origin:
						shared_origin = ''
					else:
						shared_origin += ' '

					shared_origin += str(shared_chat_id)
					shared_sec = 'shared_'+str(chat_id)

					db.add_shared(chat_id,shared_origin)
					db.add_shared(shared_chat_id,shared_sec)

					answer = f'Акканут {text} добавлен'

				else:
					answer = 'У этого пользователя уже есть аккаунт компании'

		elif 'delete' in status:
			keyboard = start_buttons
			db.update_status(chat_id,'start')	
			shared_origin = db.get_shared(chat_id)
			shared_origin = shared_origin.split()

			if text.isnumeric() and int(text)-1 < len(shared_origin):
				shared_chat_id = shared_origin[int(text)-1]
				nick = db.get_nick(shared_origin[int(text)-1])
				del shared_origin[int(text)-1]
				db.add_shared(chat_id,' '.join(shared_origin).strip())
				db.add_shared(shared_chat_id,'')
				answer = f'Аккаунт {nick} удалён'
			else:
				answer = 'Невозможный выбор'

	elif 'settings' in status:
		if 'choose' in status:
			user_regions = db.get_user(chat_id)[6].split(',')
			if text == 'Доавить регион/регионы':
				answer = "Введите регионы которые хотите добавить через запятую: \n\n"
				new_regions = []
				for region in regions:
					if not region in user_regions:
						new_regions.append(region)

				answer += ','.join(new_regions)
				
				db.update_status(chat_id,'settings region add')
			elif text == 'Удалить регион/регионы':
				answer = "Введите регионы которые хотите удалить через запятую: \n\n"
				answer += ','.join(user_regions)
				db.update_status(chat_id,'settings region delete')

			elif text == 'Удалить регион/регионы':
				answer = "Введите регионы которые хотите удалить через запятую: \n\n"
				answer += ','.join(user_regions)
				db.update_status(chat_id,'settings region delete')

			elif text == 'Периодичность отчёта':
				answer = 'Выберите, как часто бот должен присылать отчёт об изменении позиций ваших товаров: :\n\n1.Каждый день\n2.Каждые три дня\n3.Каждую неделю\n4.Каждый месяц\n\nПришлите номер нужного варианта'
				db.update_status(chat_id,'period')

		elif 'region' in status:
			if 'add' in status:
				user_regions = db.get_user(chat_id)[6].split(',')
				choosed_regions = text.split(',')
				answer = ''
				
				for choosed_region in choosed_regions:
					for region in regions:
						if region.lower() == choosed_region.lower() and region not in user_regions:
							user_regions.append(region)
							answer += choosed_region+' добавлен(а)'+'\n'
							break
					else:
						answer += choosed_region+' отсуствует'+'\n'

				db.update_regions(chat_id,','.join(user_regions))
				db.update_status(chat_id,'start')
				keyboard = start_buttons

			elif 'delete' in status:
				user_regions = db.get_user(chat_id)[6].split(',')
				choosed_regions = text.split(',')
				delete_regions = []
				answer = ''

				for choosed_region in choosed_regions:
					for region in user_regions:
						if region.lower() == choosed_region.lower():
							delete_regions.append(region)
							answer += choosed_region+' удалён(а)'+'\n'
							break
					else:
						answer += choosed_region+' отсуствует'+'\n'
				new_regions = []

				for region in user_regions:
					if not region in delete_regions:
						new_regions.append(region)

				db.update_regions(chat_id,','.join(new_regions))
				db.update_status(chat_id,'start')
				keyboard = start_buttons


	elif 'goods' in status:
		if 'main' in status:
			if text == 'Получить отчёт':
				answer = 'Подготовка отчёта запущена, ожидайте'
				db.update_status(chat_id,'start')
				keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
				parse = True
			elif text == 'Добавить товар':
				db.update_status(chat_id,'goods_add_product_url')
				answer = 'Пришлите ссылку на товар'
			elif text == 'Редактировать':
				new_status = 'change_wb_goods_change_choose'
				keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Редактировать ключевые слова'),KeyboardButton('Убрать товар из отслеживания')).add(KeyboardButton('Удалить всё'),KeyboardButton('Главное меню'))
				answer = 'Выберите действие'
				if len(products) == 0:
					answer = 'Товары отсуствуют'
					keyboard = start_buttons
					new_status = 'start'
				
				db.update_status(chat_id,new_status)

	if 'add_product' in status:
		if 'url' in status:
			try:
				if 'ozon' in text:
					if '/?' in text:
						id_ = text.split('/?')[0].split('-')[-1]
					else:
						id_ = text.split('/')[-2].split('-')[-1]
				elif 'wildberries' in text:	
					id_ = text.split('/')[4].split('/')[0]
				else:
					id_ = ''
			except:
				traceback.print_exc()
				id_ = ''

			if id_.isnumeric():
				db.update_status(chat_id,'goods_add_product_name')
				answer = 'Введите название товара'
				db.update_temp(chat_id,text)
			else:
				db.update_status(chat_id,'start')
				answer = 'Ошибка добавления товара,неверный url'
				keyboard = start_buttons
		
		elif 'name' in status:
			temp = db.get_temp(chat_id)
			if 'wildberries' in temp:
				db.update_temp(chat_id,temp+';;;;;'+text)
				db.update_status(chat_id,'goods_add_product_search')
				answer = 'Введите запросы по которым данный товар будет отслеживаться , через запятую'
			elif 'ozon' in temp:
				save_name = '_ozon'
				products = get_products(chat_id_products,save_name)
				name = text
				db.update_status(chat_id,'start')
				answer = f'Товар "{name}" добавлен'
				product = {'url':temp,'name':name,'place':{'москва':None,'казань':None}}
				products.append(product)
				keyboard = start_buttons
			
				save = True

				if len(products) == 1:
					print('here')
					twice_answer = True
					twice_answer_text = 'Периодичность отчёта'
					db.update_status(chat_id,'goods_main')

		elif 'search' in status:
			db.update_status(chat_id,'start')
			url,name = db.get_temp(chat_id).split(';;;;;')
			id_ = int(url.split('/')[4].split('/')[0])
			
			product = {'url':url,'name':name,'search':[]}

			for search in text.split(','):
				plases = {}
				
				for region in regions:
					plases[region] = None
				
				product['search'].append([search,plases]) 

			products.append(product)
			save = True
			answer = f'Товар "{name}" добавлен'
			keyboard = start_buttons

			if len(products) == 1:
				print('here')
				twice_answer = True
				twice_answer_text = 'Периодичность отчёта'
				db.update_status(chat_id,'goods_main')
	
	elif 'change' in status:
		if 'wb' in status:
			if 'choose' in status:
				if text == 'Удалить всё':
					answer = 'Список очищен'
					keyboard = start_buttons
					db.update_status(chat_id,'start')
					products = []
					save = True

				elif text in ['Редактировать ключевые слова','Убрать товар из отслеживания']:
					if 'слова' in text:
						end_word = 'отредактировать'
						status_str = '_search'
						suf = '()'
					else:
						end_word = 'удалить'
						status_str = '_delete'
						suf = '(а)'

					new_status = 'wb_change_product_do'+status_str
					list_text = ''

					if len(products) > 0:
						for i in range(len(products)):
							list_text += str(i+1)+') '+products[i]['name']+'\n\n' 
						answer = f'Список товаров на отслеживание: \n\n{list_text}\n\n '+f'Отправьте порядоквые номер{suf} товара,который нужно '+end_word
						db.update_status(chat_id,new_status)
					else:
						answer = 'Товары отсуствуют'
						db.update_status(chat_id,'start')
						keyboard = start_buttons
			
			elif 'product' in status:
				if 'do' in status:
					print('here')
					if 'search' in status:
						if text.isnumeric() and int(text)-1 < len(products):
							db.update_status(chat_id,'wb_goods_change_search')

							#temp = db.get_temp(chat_id)
							num = int(text)-1
							db.update_temp(chat_id,text)
							
							name = products[num]['name']
							search_list = ''
							search = products[num]['search']
							count = 1
							
							for i in range(len(search)):
								search_list += str(i+1)+') '+search[i][0]+'\n'
							
							answer = f'Список запросов по которым отслеживается `{name}`:\n\n {search_list} \nОтправте порядковые номера запросов которые нужно удалить через запятую'
							keyboard = edit_search_keyboard
						else:
							answer = 'Такой товар отсуствует'
							db.update_status(chat_id,'wb_change_choose')
							twice_answer = True
							twice_answer_text = 'Редактировать ключевые слова'
					
					elif 'delete' in status:
						text = text.split(',')
						old_products = copy.deepcopy(products)
						answer = ''
						
						for el in text:
							if el.isnumeric() and int(el)-1 < len(old_products):
								num = int(el) - 1
								index = products.index(old_products[num])
								del products[index]
								answer += f'Товар {el} удалён\n'
							else:
								answer += f'Товар {el} отсуствует\n'
						
						save = True
						twice_answer = True
						db.update_status(chat_id,'wb_change_choose')
						twice_answer_text = 'Убрать товар из отслеживания'
			
			elif 'search' in status:
				temp = db.get_temp(chat_id)
				if 'add' in status:
					answer = 'Запрос добавлен,ожидайте отчёт'
					keyboard = start_buttons

					plases = {}
					for region in regions:
						plases[region] = None
				
					products[int(temp)-1]['search'].append([text,plases]) 
					save = True

					db.update_status(chat_id,'wb_change_choose')
					twice_answer = True
					twice_answer_text = 'Редактировать ключевые слова'
				
				elif text == 'Добавить новый':
					db.update_status(chat_id,'wb_goods_change_search_add')
					answer = 'Введите запрос для добавления к товару '+products[int(temp)-1]['name']

				elif text == 'Назад':
					answer = ''
					db.update_status(chat_id,'wb_change_choose')
					twice_answer = True
					twice_answer_text = 'Редактировать ключевые слова'
				else:
					db.update_status(chat_id,'wb_goods_change_product')
					keyboard = start_buttons
					old_products = copy.deepcopy(products)

					for num in text.split(','):
						num = num.strip()
						if num.isnumeric() and not int(num)-1 >= len(old_products[int(temp)-1]['search']):
							name = products[int(temp)-1]['name']

							if len(name) > 15:
								name = name[:15]+'...'

							index = products[int(temp)-1]['search'].index(old_products[int(temp)-1]['search'][int(num)-1])
							search = products[int(temp)-1]['search'][index][0]
							answer_mess = f'Запрос {search} для товара {name} - удалён'
							
							del products[int(temp)-1]['search'][index]
							save = True
						else:
							answer_mess = f'{num} такой номер отсуствует'

						await message.answer(answer_mess)

					answer = 'Выберите действие'
					db.update_status(chat_id,'wb_change_choose')
					twice_answer = True
					twice_answer_text = 'Редактировать ключевые слова'
			

		elif 'ozon' in status:
			save_name = '_ozon'
			products = get_products(chat_id_products,save_name)
			old_products = products[:]
			if 'delete' in status:
				for num in text.split(','):
					num = num.strip()
					keyboard = start_buttons
					db.update_status(chat_id,'change_market')
					
					if num.isnumeric() and int(num) <= len(old_products):
						index = products.index(old_products[int(num)-1])
						del products[index]
						answer_mess = f'Товар {num} удалён'
						save = True
					else:
						answer_mess = f'{num} невозможный выбор'

					await message.answer(answer_mess)
				
				answer = 'Выберите действие'
				twice_answer = True
				twice_answer_text = 'Ozon'
	
	elif 'competitor' in status:
		if 'main' in status:
			if text == 'Добавить товар на отслеживание':
				answer = 'Введите ссылку на товар для отслеживания'
				db.update_status(chat_id,'competitor_add_url')
			elif text == 'Список отслеживаемых товаров и их удаление':
				db.update_status(chat_id,'competitor_delete')
				answer = 'У вас нет товаров конкурентов'
				print('products/products_wb_competive '+str(chat_id))
				if os.path.exists('products/products_wb_competive '+str(chat_id)+'.json'):
					products = get_products(chat_id_products,'_wb_competive')
					
					if products != {}:
						keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Удалить всё')).add(KeyboardButton('Главное меню'))
						answer = ''
						count = 1
						for product in products:
							answer += str(count)+'. '+products[product]['name']+'\n'
							count += 1
						answer += '\nВведите номер товара, который хотите удалить'

			elif text == 'Отслеживание всех товаров магазина':
				db.update_status(chat_id,'competitor_shop_choice')
				answer = 'У вас нет магазинов конкурентов'
				print('products/products_shop '+str(chat_id))
				keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Добавить магазин')).add(KeyboardButton('Главное меню'))
				
				if os.path.exists('products/products_shop '+str(chat_id)+'.json'):
					products = get_products(chat_id_products,'_shop')
					
					if products != {}:
						keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Добавить магазин')).add(KeyboardButton('Удалить всё')).add(KeyboardButton('Главное меню'))
						answer = ''
						count = 1
						for product in products:
							answer += str(count)+'. '+products[product]['name']+'\n'
							count += 1
						answer += '\nВведите номер магазина, который хотите удалить'
		
		elif 'shop' in status:
			print('here--------------------')
			if 'choice' in status:
				products = get_products(chat_id_products,'_shop')
				if text == 'Удалить всё':
					answer = 'Список очищен'
					products = {}
					save = True
					save_name = '_shop'
				elif text == 'Добавить магазин':
					answer = 'Введите ссылку на магазин,который хотите добавить'
					db.update_status(chat_id,'competitor_shop_add')
				elif text.isnumeric() and len(products) >= int(text)-1:
					answer = 'Магазин успешно удалён'
					products_keys = list(products.keys())
					del products[products_keys[int(text)-1]]
					save = True
					save_name = '_shop'
					twice_answer = True
					twice_answer_text = 'Отслеживание всех товаров магазина'
					db.update_status(chat_id,'competitor_main')
			
			elif 'add' in status:
				answer = add_competitor_shop(text,chat_id_products)
				twice_answer = True
				twice_answer_text = 'Отслеживание всех товаров магазина'
				db.update_status(chat_id,'competitor_main')

		elif 'delete' in status:
			if os.path.exists('products/products_wb_competive '+str(chat_id)+'.json'):
				products = get_products(chat_id_products,'_wb_competive')				
				old_products = list(products.keys())
				db.update_status(chat_id,'start')
				keyboard = start_buttons
				if text == 'Удалить всё':
					products = {}
					save = True
					save_name = '_wb_competive'
					answer = 'Список очищен'
				else:
					for num in text.split(','):
						num = num.strip()
						if num.isnumeric():
							if not int(num)-1 >= len(old_products):
								count = 0
								for product in old_products:
									print(count)
									if count == int(num)-1:
										name = products[product]['name']
										del products[product]
										break
									count += 1
								answer_mess = f'Товар {name} успешно удалён и более не отслеживается'
								save = True
								save_name = '_wb_competive'

							else:
								answer_mess = 'Такой товар отсуствует'
						else:
							db.update_status(chat_id,'start')
							answer_mess = 'Невозможный выбор'
							keyboard = start_buttons

						await message.answer(answer_mess)

		elif 'add' in status:
			if 'url' in status:
				try:
					id_ = text.split('/')[4].split('/')[0]
				except:
					id_ = ''
				
				if not id_ == '':
					answer = 'Введите название отслеживаемного товара\n\n\nНапример, "Товар подушка Конкурент ИП Пупкин"'
					db.update_status(chat_id,'competitor_add_name')
					db.update_temp(chat_id,id_)
				else:
					db.update_status(chat_id,'start')
					answer = 'Неправильный url'
					keyboard = start_buttons
			
			elif 'name' in status:
				db.update_status(chat_id,'start')
				answer = 'Товар успешно добавлен, бот пришлёт уведомление когда зафиксирует изменения'
				keyboard = start_buttons
				id_ = db.get_temp(chat_id)

				if os.path.exists('products/products_wb_competive '+str(chat_id)+'.json'):
					products = get_products(chat_id_products,'_wb_competive')
				else:
					products = {}

				price = {}
				for region in regions:
					price[region] = '0'
				
				products[id_] = {'name':text,'price':price}
				save = True
				save_name = '_wb_competive'
	elif answer == '':
		if status != 'main':
			start_message = 'Выбор отменён,выберите действие'
		db.update_status(chat_id,'start')
		await message.answer(start_message,reply_markup=start_buttons)
		return
	

	if save:
		save_products(products,chat_id_products,save_name)

	if answer != '':
		await message.answer(answer,reply_markup=keyboard)
	
	if twice_answer:
		await answer_message(message,twice_answer_text,twice_chat_id)

	if parse:
		start_parse(str(chat_id),True,False)


if __name__ == '__main__':
	Thread(target=start_loop,args=[]).start()
	executor.start_polling(dp,skip_updates=True)