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

start_buttons = ReplyKeyboardMarkup().add(KeyboardButton('Получить отчёт')).add(KeyboardButton('Добавить товар')).add(KeyboardButton('Редактировать')).add(KeyboardButton('Товары конкурентов'))
edit_keyboard = ReplyKeyboardMarkup().add(KeyboardButton('Редактировать поисковые запросы')).add(KeyboardButton('Удалить товар')).add(KeyboardButton('Главное меню'))

edit_keyboard_comp = ReplyKeyboardMarkup().add(KeyboardButton('Добавить товар')).add(KeyboardButton('Главное меню'))

edit_search_keyboard = ReplyKeyboardMarkup().add(KeyboardButton('Добавить новый')).add(KeyboardButton('Главное меню'))

def get_products(chat_id,name=''):
	with open(f'products/products{name} {chat_id}.json','r',encoding='utf-8-sig') as file:
		products = json.loads(file.read())

	return products

def save_products(products,chat_id,name=''):
	print('saving')
	with open(f'products/products{name} {chat_id}.json','w',encoding='utf-8-sig') as file:
		file.write(json.dumps(products))

@dp.message_handler()
async def answer(message):
	start_message = 'Приветствую,выберите действие ниже'
	chat_id = message.chat.id
	
	if not db.user_exists(str(chat_id)):
		db.add_user(str(chat_id))
		save_products([],chat_id)
		await message.answer(start_message,reply_markup=start_buttons)
	
	status = db.get_status(chat_id)
	text = message.text
	keyboard = ReplyKeyboardMarkup().add('Главное меню')
	answer = ''
	save = False
	parse = False
	save_name = ''

	if text == 'Главное меню' or text == '/start':
		if status != 'main':
			start_message = 'Выбор отменён,выберите действие'
		db.update_status(chat_id,'main')
		await message.answer(start_message,reply_markup=start_buttons)
		return
	
	products = get_products(chat_id)
	
	if status == 'main':
		if text == 'Получить отчёт':
			answer = ''
			keyboard = ReplyKeyboardMarkup()
			parse = True
		elif text == 'Добавить товар':
			db.update_status(chat_id,'add_product_url')
			answer = 'Пришлите ссылку на товар'
		elif text == 'Редактировать':
			if len(products) > 0:
				list_text = ''
				for i in range(len(products)):
					list_text += str(i+1)+') '+products[i]['name']+'\n\n' 
				answer = f'Список товаров на отслеживание: \n\n{list_text}\n\n Отправьте порядоквый номер товара,который нужно отредактировать'
				db.update_status(chat_id,'change_choose')
			else:
				answer = f'Товары отсуствуют'
				keyboard = start_buttons
		elif text == 'Товары конкурентов':
			db.update_status(chat_id,'competitor_choose')
			answer = 'У вас нет товаров конкурентов'
			keyboard = edit_keyboard_comp
			print('products/products_competive '+str(chat_id))
			if os.path.exists('products/products_competive '+str(chat_id)+'.json'):
				products = get_products(chat_id,'_competive')
				
				if products != {}:
					answer = 'Выберите товар для удаления:\n\n'
					count = 1
					for product in products:
						answer += str(count)+'. '+products[product]['name']+'\n'
						count += 1

	
	elif 'competitor' in status:
		if 'choose' in status:
			if text == 'Добавить товар':
				db.update_status(chat_id,'competitor_add_name')
				answer = 'Введите название товара'
			elif text.isnumeric() and os.path.exists('products/products_competive '+str(chat_id)+'.json'):
				products = get_products(chat_id,'_competive')
				db.update_status(chat_id,'main')
				keyboard = start_buttons

				if not int(text)-1 >= len(products):
					count = 0
					for product in products:
						if count == int(text)-1:
							name = products[product]['name']
							del products[product]
							break
						count += 1
					answer = f'Товар {name} успешно удалён'
					save = True
					save_name = '_competive'

				else:
					answer = 'Такой товар отсуствует'
			else:
				db.update_status(chat_id,'main')
				answer = 'Невозможный выбор'
				keyboard = start_buttons

		if 'add' in status:
			if 'name' in status:
				db.update_status(chat_id,'competitor_add_url')
				db.update_temp(chat_id,text)
				answer = 'Введите ссылку на товар'
			elif 'url' in status:
				db.update_status(chat_id,'main')
				answer = 'Товар успешно добавлен'
				keyboard = start_buttons
				try:
					id_ = text.split('/')[4].split('/')[0]
				except:
					id_ = ''
					db.update_status(chat_id,'main')
					answer = 'Неправильный url'
					keyboard = start_buttons

				if not id_ == '':
					temp = db.get_temp(chat_id)

					if os.path.exists('products/products_competive '+str(chat_id)+'.json'):
						products = get_products(chat_id,'_competive')
					else:
						products = {}

					price = {}
					for region in regions:
						price[region] = '0'
					
					products[id_] = {'name':temp,'price':price}
					save = True
					save_name = '_competive'


	elif 'add_product' in status:
		if 'url' in status:
			try:
				id_ = text.split('/')[4].split('/')[0]
			except:
				id_ = ''

			if id_.isnumeric():
				db.update_status(chat_id,'add_product_name')
				answer = 'Введите название товара'
				db.update_temp(chat_id,text)
			else:
				db.update_status(chat_id,'main')
				answer = 'Ошибка добавления товара,неверный url'
				keyboard = start_buttons
		
		elif 'name' in status:
			temp = db.get_temp(chat_id)
			db.update_temp(chat_id,temp+','+text)
			db.update_status(chat_id,'add_product_search')
			answer = 'Введите запросы по который данный товар будет отслеживаться,через запятую'

		elif 'search' in status:
			db.update_status(chat_id,'main')
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
				db.update_status(chat_id,'main')
			else:	
				db.update_status(chat_id,'change_product')
				db.update_temp(chat_id,text)
				name = products[int(text)-1]['name']
				
				answer = f'Что желаете сделать с {text} товаром,{name}'
				keyboard = edit_keyboard
		elif 'product' in status:
			if text == 'Редактировать поисковые запросы':
				db.update_status(chat_id,'change_search')

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
				db.update_status(chat_id,'main')
				temp = db.get_temp(chat_id)
				del products[int(temp)-1]
				answer = f'Товар {temp} удалён'
				keyboard = start_buttons
				save = True
		elif 'search' in status:
			temp = db.get_temp(chat_id)
			if 'add' in status:
				db.update_status(chat_id,'main')
				answer = 'Запрос добавлен,ожидайте отчёт'
				keyboard = start_buttons

				products[int(temp)-1]['search'].append([text,None])
				save = True
			
			elif text == 'Добавить новый':
				db.update_status(chat_id,'change_search_add')
				answer = 'Введите запрос для добавления к товару '+products[int(temp)-1]['name']
			else:
				db.update_status(chat_id,'main')
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
	if save:
		save_products(products,chat_id,save_name)

	if answer != '':
		await message.answer(answer,reply_markup=keyboard)

	if parse:
		start_parse(str(chat_id))

if __name__ == '__main__':
	Thread(target=start_loop,args=[]).start()
	executor.start_polling(dp,skip_updates=True)