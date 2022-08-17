# -*- coding: utf-8 -*-
from sql import SQLighter
import requests
import json
import os
from threading import Thread
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove,ReplyKeyboardMarkup, KeyboardButton
from time import sleep

from parserwb import start_parse,start_loop,regions

bot = Bot(token='5490688808:AAE9EVs8TSxndZt7FDAo7JyjwVIftI6DkH4')
dp = Dispatcher(bot)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "db.db")

db = SQLighter(db_path)

first_button = ReplyKeyboardMarkup().add(KeyboardButton('Начать'))

start_buttons = ReplyKeyboardMarkup().add(KeyboardButton('Отчёт о позициях товаров')).add(KeyboardButton('Отчёт по действиям конкурентов'))
start_buttons_goods = ReplyKeyboardMarkup().add(KeyboardButton('Получить отчёт')).add(KeyboardButton('Добавить товар')).add(KeyboardButton('Редактировать')).add(KeyboardButton('Главное меню'))
start_buttons_copetitor = ReplyKeyboardMarkup().add(KeyboardButton('Добавить товар на отслеживание')).add(KeyboardButton('Список отслеживаемых товаров и их удаление')).add(KeyboardButton('Главное меню'))

edit_keyboard = ReplyKeyboardMarkup().add(KeyboardButton('Редактировать поисковые запросы')).add(KeyboardButton('Удалить товар')).add(KeyboardButton('Главное меню'))
edit_search_keyboard = ReplyKeyboardMarkup().add(KeyboardButton('Добавить новый')).add(KeyboardButton('Главное меню'))

admin_chats = ['340549861','618939593']


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
	amount_of_users = len(db.get_users())
	users = []
	users_search = 0
	users_products = 0
	searches = []
	products = []

	for filename in os.listdir("products"):
		with open(os.path.join("products", filename), 'r') as f:
			data = f.read()
			if data == '[]' or data == '{}':
				continue	

			data = get_products(name=filename)
			
			if not filename.split()[1] in users:
				users.append(filename.split()[1])

			print(filename)
			if not '_competive' in filename:
				print(data)
				for product in data:
					print(product)
					for search in product['search']:
						if not search in searches:
							searches.append(search)

				users_search += 1
			else:
				for product in data:
					if not product in products:
						products.append(product)
				users_products += 1

	info = f'1. В боте зарегистрировано {amount_of_users} '+users_string(amount_of_users)+'\n2. Активных пользователей - '+str(len(users))+'\n3. '+str(users_search) + ' ' + human_string(users_search)+' имеют(ет) запросы на отслеживании'+'\n4. '+str(users_products) + ' ' + human_string(users_products)+' имеют(ет) товары на отслеживании'+'\n5. '+'Всего поисковых запросов '+str(len(searches))+'\n6. '+str(len(products))+' товаров отслеживается'

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
async def answer(message):
	start_message = 'Выберите действие'
	first_message = "Привет! Этот бот будет тебе очень полезен, вот что он умеет:\n\n\n1.Отслеживать движения товаров в поисковой выдаче WildBerries в разных городах. Полезно знать как растёт ваш товар при его продвижении и иметь возможность быстро среагировать, если позиции вашего товара начали падать. Бот также поможет в SEO оптимизации, благодаря ему вы будете знать появился ли товар в поиске по нужным вам запросам или неожиданно пропал из поиска\n\n\n2.Следить за действиями ваших главных конкурентов, сообщая когда они меняют цену или их товар выпадает из наличия"
	chat_id = message.chat.id
	
	if not db.user_exists(str(chat_id)):
		db.add_user(str(chat_id))
		save_products([],chat_id)
		await message.answer(first_message,reply_markup=first_button)
	
	status = db.get_status(chat_id)
	text = message.text
	keyboard = ReplyKeyboardMarkup().add('Главное меню')
	answer = ''
	
	save = False
	parse = False

	save_name = ''
	admin_rights = False

	if str(chat_id) in admin_chats:
		admin_rights = True
		start_buttons = ReplyKeyboardMarkup().add(KeyboardButton('Отчёт о позициях товаров')).add(KeyboardButton('Отчёт по действиям конкурентов')).add(KeyboardButton('/info')).add(KeyboardButton('/post'))
	
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
		if message.text == '/info':
			info = get_info()
			await message.answer(info,reply_markup=start_buttons)
			return

		elif message.text == '/post':
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
			keyboard = ReplyKeyboardMarkup().add('Да').add('Главное меню')
			await message.answer('Вы уверены,что хотите сделать рассыку этого сообщения?',reply_markup=keyboard)
		else:
			if text == 'Да':
				print('post')
				text = db.get_temp(chat_id)
				await post(text)
				await message.answer(start_message,reply_markup=start_buttons)
		return

	products = get_products(chat_id)

	if status == 'first':
		keyboard = start_buttons
		answer = start_message
		db.update_status(chat_id,'start')
	elif status == 'start':
		if text == 'Отчёт о позициях товаров':
			keyboard = start_buttons_goods
			answer = 'После того как вы добавили товар, бот ежедневно будет отчитываться о том как меняются его позиции\n\n\nЕжедневный отчёт приходит после 10:00 по Мск\n\n\nТакже вы можете запросить формирование отчёта в любой момент, если нужны свежие данные о его позициях'
			db.update_status(chat_id,'goods_main')
		elif text == 'Отчёт по действиям конкурентов':
			keyboard = start_buttons_copetitor
			answer = 'Бот предупредит вас когда конкурент сменит цену или его товар выпадет из наличия\n\n\nЭто важно, если ваш товар находится на первых местах в топе. Тогда действия конкурентов будут влиять на ваши продажи, а благодаря боту вы будете в курсе и быстро узнаете если ваш конкурент начнёт демпинговать или наоборот завысит цену, и сможете изменить свою цену, привлечь таким образом больше покупателей и продаж\n\n\nЭто же касается и моментов когда важный конкурент выпадает из наличия, в это время выгодно поднимать цены, ведь вам достанется больше покупателей\n\n\nТакже данный функционал можно использовать для отслеживания собственных цен. Чтобы убедиться в том что установлена правильная цена (помогает контролировать сотрудников и проверять себя), а также убедиться в том что скидка применилась и товар добавился в акцию'
			db.update_status(chat_id,'competitor_main')
	
	if 'goods' in status:
		if 'main' in status:
			if text == 'Получить отчёт':
				answer = ''
				keyboard = ReplyKeyboardMarkup()
				parse = True
			elif text == 'Добавить товар':
				db.update_status(chat_id,'goods_add_product_url')
				answer = 'Пришлите ссылку на товар'
			elif text == 'Редактировать':
				if len(products) > 0:
					list_text = ''
					for i in range(len(products)):
						list_text += str(i+1)+') '+products[i]['name']+'\n\n' 
					answer = f'Список товаров на отслеживание: \n\n{list_text}\n\n Отправьте порядоквый номер товара,который нужно отредактировать'
					db.update_status(chat_id,'goods_change_choose')
				else:
					answer = f'Товары отсуствуют'
					keyboard = start_buttons

		elif 'add_product' in status:
			if 'url' in status:
				try:
					id_ = text.split('/')[4].split('/')[0]
				except:
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
				db.update_temp(chat_id,temp+','+text)
				db.update_status(chat_id,'goods_add_product_search')
				answer = 'Введите запросы по который данный товар будет отслеживаться,через запятую'

			elif 'search' in status:
				db.update_status(chat_id,'start')
				url,name = db.get_temp(chat_id).split(',')
				id_ = int(url.split('/')[4].split('/')[0])
				
				product = {'url':url,'name':name,'search':[]}

				for search in text.split(','):
					plases = {}
					
					for region in regions:
						plases[region] = None
					
					product['search'].append([search,plases]) 

				products.append(product)
				save = True
				answer = f'Товар `{name}` добавлен,ожидайте отчёт'
				keyboard = start_buttons
		
		elif 'change' in status:
			if 'choose' in status:
				if not text.isnumeric() or int(text) > len(products):
					answer = 'Такой номер отсуствует'
					keyboard = start_buttons
					db.update_status(chat_id,'start')
				else:	
					db.update_status(chat_id,'goods_change_product')
					db.update_temp(chat_id,text)
					name = products[int(text)-1]['name']
					
					answer = f'Что желаете сделать с {text} товаром,{name}'
					keyboard = edit_keyboard
			elif 'product' in status:
				if text == 'Редактировать поисковые запросы':
					db.update_status(chat_id,'goods_change_search')

					temp = db.get_temp(chat_id)
					num = int(temp)-1
					name = products[num]['name']
					search_list = ''
					search = products[num]['search']
					count = 1
					
					for i in range(len(search)):
						search_list += str(i+1)+') '+search[i][0]+'\n'
					
					answer = f'Список запросов по которым отслеживается `{name}`:\n\n {search_list} \nОтправте порядковый номер запроса который нужно удалить'
					keyboard = edit_search_keyboard
				elif text == 'Удалить товар':
					db.update_status(chat_id,'start')
					temp = db.get_temp(chat_id)
					del products[int(temp)-1]
					answer = f'Товар {temp} удалён'
					keyboard = start_buttons
					save = True
			elif 'search' in status:
				temp = db.get_temp(chat_id)
				if 'add' in status:
					db.update_status(chat_id,'start')
					answer = 'Запрос добавлен,ожидайте отчёт'
					keyboard = start_buttons

					products[int(temp)-1]['search'].append([text,None])
					save = True
				
				elif text == 'Добавить новый':
					db.update_status(chat_id,'goods_change_search_add')
					answer = 'Введите запрос для добавления к товару '+products[int(temp)-1]['name']
				else:
					db.update_status(chat_id,'start')
					keyboard = start_buttons
					
					if text.isnumeric():
						name = products[int(temp)-1]['name']

						if len(name) > 15:
							name = name[:15]+'...'
						
						search = products[int(temp)-1]['search'][int(text)-1][0]
						answer = f'Запрос {search} для товара {name} - удалён'
						del products[int(temp)-1]['search'][int(text)-1]
						save = True
					else:
						answer = 'Такой номер отсуствует'
	
	elif 'competitor' in status:
		if 'main' in status:
			if text == 'Добавить товар на отслеживание':
				answer = 'Введите ссылку на товар для отслеживания'
				db.update_status(chat_id,'competitor_add_url')
			elif text == 'Список отслеживаемых товаров и их удаление':
				db.update_status(chat_id,'competitor_delete')
				answer = 'У вас нет товаров конкурентов'
				print('products/products_competive '+str(chat_id))
				if os.path.exists('products/products_competive '+str(chat_id)+'.json'):
					products = get_products(chat_id,'_competive')
					
					if products != {}:
						answer = ''
						count = 1
						for product in products:
							answer += str(count)+'. '+products[product]['name']+'\n'
							count += 1
						answer += '\nВведите номер товара, который хотите удалить'
		
		elif 'delete' in status:
			if text.isnumeric() and os.path.exists('products/products_competive '+str(chat_id)+'.json'):
				products = get_products(chat_id,'_competive')
				db.update_status(chat_id,'start')
				keyboard = start_buttons

				if not int(text)-1 >= len(products):
					count = 0
					for product in products:
						if count == int(text)-1:
							name = products[product]['name']
							del products[product]
							break
						count += 1
					answer = f'Товар {name} успешно удалён и более не отслеживается'
					save = True
					save_name = '_competive'

				else:
					answer = 'Такой товар отсуствует'
			else:
				db.update_status(chat_id,'start')
				answer = 'Невозможный выбор'
				keyboard = start_buttons

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

				if os.path.exists('products/products_competive '+str(chat_id)+'.json'):
					products = get_products(chat_id,'_competive')
				else:
					products = {}

				price = {}
				for region in regions:
					price[region] = '0'
				
				products[id_] = {'name':text,'price':price}
				save = True
				save_name = '_competive'

	if save:
		save_products(products,chat_id,save_name)

	if answer != '':
		await message.answer(answer,reply_markup=keyboard)

	if parse:
		start_parse(str(chat_id))

if __name__ == '__main__':
	Thread(target=start_loop,args=[]).start()
	executor.start_polling(dp,skip_updates=True)