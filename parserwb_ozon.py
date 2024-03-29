# -*- coding: utf-8 -*-
import requests
import json
import traceback
import urllib.parse
import os
import copy
import pickle

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver
from selenium.webdriver.common.by import By 

from bs4 import BeautifulSoup as bs
from sql import SQLighter
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, executor, types
from time import sleep

from config import token


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "db.db")

db = SQLighter(db_path)

regions = {
			'Москва':'&couponsGeo=12,3,18,15,21&curr=rub&dest=-1029256,-102269,-162903,-446078&emp=0&lang=ru&locale=ru&reg=0&regions=68,64,83,4,38,80,33,70,82,86,75,30,69,22,66,31,40,1,48,71&',
			'Казань':'&regions=68,64,83,4,38,80,33,70,82,86,30,69,22,66,31,40,1,48&reg=0&emp=0&locale=ru&lang=ru&curr=rub&couponsGeo=12,7,3,6,18,22,21&dest=-1075831,-79374,-367666,-2133466&',
			'Краснодар':'&couponsGeo=2,7,3,6,19,21,8&curr=rub&dest=-1059500,-108082,-269701,12358060&emp=0&lang=ru&locale=ru&regions=68,64,83,4,38,80,33,70,82,86,30,69,22,66,31,40,1,48&',
			'Санкт-Петербург':'&couponsGeo=12,7,3,6,5,18,21&curr=rub&dest=-1216601,-337422,-1114252,-1124719&emp=0&lang=ru&locale=ru&regions=68,64,83,4,38,80,33,70,82,86,30,69,22,66,31,40,1,48&',
			'Екатеринбург':'&couponsGeo=2,12,7,3,6,13,21&curr=rub&dest=-1113276,-79379,-1104258,-5818948&emp=0&lang=ru&locale=ru&regions=64,58,83,4,38,80,33,70,82,86,30,69,22,66,31,40,1,48&',
			'Новосибирск':'&couponsGeo=2,12,7,3,6,21,16&curr=rub&dest=-1221148,-140294,-1751445,-364763&emp=0&lang=ru&locale=ru&regions=64,58,83,4,38,80,33,70,82,86,30,69,22,66,31,40,1,48&',
			'Хабаровск':'&couponsGeo=2,12,7,6,9,21,11&curr=rub&dest=-1221185,-151223,-1782064,-1785056&emp=0&lang=ru&locale=ru&regions=64,4,38,80,70,82,86,30,69,22,66,40,1,48&'
}

def create_driver(headless=True):
	print('create_driver()')
	chrome_options = webdriver.ChromeOptions()
	if headless:
		chrome_options.add_argument("--headless")
	chrome_options.add_argument("--log-level=3")
	chrome_options.add_argument("--start-maximized")
	chrome_options.add_argument('--no-sandbox')
	chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36')
	chrome_options.add_argument('--disable-blink-features=AutomationControlled')
	#chrome_options.add_argument('--proxy-server='+proxy)

	chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
	chrome_options.add_experimental_option('useAutomationExtension', False)
	chrome_options.add_argument("--disable-blink-features")
	chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36")
	chrome_options.add_experimental_option("prefs", { 
	"profile.default_content_setting_values.media_stream_mic": 1, 
	"profile.default_content_setting_values.media_stream_camera": 1,
	"profile.default_content_setting_values.geolocation": 1, 
	"profile.default_content_setting_values.notifications": 1,
	"profile.default_content_settings.geolocation": 1,
	"profile.default_content_settings.popups": 0
  })
	
	caps = DesiredCapabilities().CHROME

	caps["pageLoadStrategy"] = "none"	
	
	driver = webdriver.Chrome(desired_capabilities=caps,chrome_options=chrome_options)	

	driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
 "source": """
	  const newProto = navigator.__proto__
	  delete newProto.webdriver
	  navigator.__proto__ = newProto		
	  """
})
	driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
	
	caps["pageLoadStrategy"] = "none"
	driver.implicitly_wait(30)

	#params = {
	#"latitude": 55.5815245,
	#"longitude": 36.825144,
	#"accuracy": 100
	#}
	#driver.execute_cdp_cmd("Emulation.setGeolocationOverride", params)
	#driver.refresh()
	
	return driver

#driver = create_driver()

def get_page_driver(url,region):
	while True:
		try:
			#print(url)
			driver.get(url)
			sleep(0.1)
			load_cookie(region)
			sleep(0.4)
			data = driver.find_element(By.XPATH,"/html/body").text
			driver.delete_all_cookies()
			
			return json.loads(data)
		except:
			log_exc()
			continue

def get_category(id_):
	search_url = 'https://www.ozon.ru/product/'+str(id_)
	driver.get(search_url)
	sleep(3)
	test(driver.page_source,'ozon_test.html')
	print('saved')
	driver.find_elements(By.XPATH,'//ol')[-1]
	soup = bs(driver.page_source,'html.parser')

	category = soup.findAll('ol')[-1].findAll('li')

	full_category = category
	category = category[-2].find('a')

	if not category:
		category = full_category[-1].find('a')

	return category.get('href')

def check_product_ozon(id_,last_page=26,region='',extra_params=''):
	number = 0
	add_number = 0
	if '/?' in id_:
		id_ = id_.split('/?')[0].split('-')[-1]
	else:
		id_ = id_.split('/')[-2].split('-')[-1]

	category = get_category(id_)
	
	next_page_str = ''
	
	for page in range(1,last_page):
		search_url = 'https://www.ozon.ru/api/composer-api.bx/page/json/v2?url='
		
		search_param = category+'?page='+str(page) if page == 1 else next_page_str.replace('layout_container=searchMegapagination&','')
		
		json_ = get_page_driver(search_url+search_param,region)
		widget = json_['widgetStates']
		
		if page == 1:
			for key in widget:
				if 'searchResultsV2' in key and 'default-' in key:
					searchresult = key
			
				elif 'megaPaginator-' in key and 'default-' in key:
					next_page_param = json.loads(json_['widgetStates'][key])
		else:
			for key in widget:
				if 'searchResultsV2' in key and 'categorySearchMegapagination-' in key:
					searchresult = key
					break
			next_page_param = json_

		widget = json.loads(json_['widgetStates'][searchresult])
		
		if not 'items' in widget or len(widget['items']) == 0:
			return None

		items = widget['items']
		
		for item in items:
			item_id = item['action']['link'].split('/?')[0].split('-')[-1]
			if not 'backgroundColor' in item:
				number += 1
				result = number
			else:
				add_number += 1
				result = 'реклама '+str(add_number)

			if item_id == id_:
				return result

		next_page_str = next_page_param['nextPage']
	else:
		return None

def load_cookie(cookie='москва'):
	with open(cookie, 'rb') as cookiesfile:
		cookies = pickle.load(cookiesfile)
		for cookie in cookies:
			driver.add_cookie(cookie)

	driver.refresh()
	return False


def save_cookie(name='москва'):
	driver.get('https://www.ozon.ru/')
	with open(name, 'wb') as filehandler:
		pickle.dump(driver.get_cookies(), filehandler)


def get_products(chat_id,name=''):
	with open(f'products/products{name} {chat_id}.json','r',encoding='utf-8-sig') as file:
		products = json.loads(file.read())

	return products

def save_products(products,chat_id,name=''):
	print('saving')
	with open(f'products/products{name} {chat_id}.json','w',encoding='utf-8-sig') as file:
		file.write(json.dumps(products))

def log_exc():
	traceback.print_exc()
	with open('log.txt','a+') as file:
		file.write(str(datetime.now())+'\n'+str(traceback.format_exc())+'\n\n\n')

def start_loop():
	print('Петля запущена')
	sended_message = False
	while True:
		try:
			users = db.get_users()

			for user in users:
				if os.path.exists('products/products_wb_competive '+user[1]+'.json'):
					check_competitor(user[1])
				if os.path.exists('products/products_shop '+user[1]+'.json'):
					check_competitor_shop(user[1])
		except:
			log_exc()

		try:
			hour,minute = datetime.now().strftime("%H:%M").split(':')
			print(hour,'hour')
			if hour == '10' and not sended_message:
				for user in users:		
					days_max,days_past = user[-2:]
				
					if days_max == -1:
						continue

					days_past += 1

					if days_past >= days_max:
						try:
							start_parse(user[1])
						except:
							log_exc()
						days_past = 0

					db.update_user(days_max,days_past,user[1])
				sended_message = True
			elif hour == '11':
				sended_message = False
		except:
			log_exc()
			continue

		sleep(60)

def check_if_product_in_fileselling(id_,exctra):
	search_url = f'https://card.wb.ru/cards/detail?spp=0&{exctra}pricemarginCoeff=1.0&appType=1&nm='+str(id_)
	data = get_page(search_url)['data']['products'][0]

	if data['sizes'][0]['stocks'] != []:
		return True

	return False


def check_competitor_products(ids,exctra):
	products = []
	for id_ in ids:
		search_url = f'https://card.wb.ru/cards/detail?spp=0&{exctra}pricemarginCoeff=1.0&appType=1&nm='+str(id_)
		data = get_page(search_url)
		products += data['data']['products']

	return products

def check_photo(id_):
	count_photo = 0
	is_photo = False
	headers = get_headers('photo_headers')
	while not is_photo:
		photo = f'https://basket-0{count_photo}.wb.ru/vol'+str(id_[:len(id_)-5])+'/part'+str(id_[:len(str(id_))-3])+'/'+str(id_)+'/images/c516x688/1.jpg'
		try:
			r = requests.get(photo,headers=headers)
			status = r.status_code
		except:
			status = 404
		
		if status != 404:
			is_photo = True
		
		count_photo += 1
		if count_photo == 10 and not is_photo:
			photo = None
			break
	
	return r.content

def check_competitor_shop(chat_id):
	shared = db.get_shared(chat_id)
	extra_chat_ids = []
	
	if shared and shared != '':
		if 'shared' in shared:
			return
		else:
			extra_chat_ids = shared.split()
	print('test',shared,extra_chat_ids)
	if not os.path.exists(f'products/products_shop {chat_id}.json'):
		return
	
	shops = get_products(chat_id,'_shop')
	old_shops = copy.deepcopy(shops)
	for sup_id in shops:
		ids = []
		page = 1

		while True:
			search_url = 'https://catalog.wb.ru/sellers/catalog?appType=1&couponsGeo=12,3,18,15,21&curr=rub&dest=-1029256,-102269,-1252558,-1252424&emp=0&lang=ru&locale=ru&pricemarginCoeff=1.0&reg=0&regions=68,64,83,4,38,80,33,70,82,86,75,30,69,1,48,22,66,31,40,71&spp=0&supplier='+sup_id+'&page='+str(page)
			products = get_page(search_url)['data']['products']
			if len(products) == 0:
				break
			
			for product in products:
				keyboard = []
				text = ''
				#print(product['id'],product['name'])
				ids.append(str(product['id']))

				if not str(str(product['id'])) in shops[sup_id]['products']:
					text = 'Появился новый товар у '+shops[sup_id]['name']+'\n'+product['name']
					price = {}
					for region in regions:
						price[region] = product['salePriceU']//100
					
					shops[sup_id]['products'][str(str(product['id']))] = {'name':product['name'],'price':price}
				else:
					shop_product = shops[sup_id]['products'][str(str(product['id']))]
					name = shop_product['name']
					price = product['salePriceU']//100

					if shop_product['price']['Москва'] == None:
						text = f'Товар {name} снова в продаже🟢'
					elif product['salePriceU']//100 != shop_product['price']['Москва']:
						change =  price - shop_product['price']['Москва']
						
						if change > 0:
							symbol = '+'
							emoji = '🟢'
						else:
							symbol = ''
							emoji = '🔴'

						text = f'Цена на товар {name} изменилась: {price} ({symbol}{change}){emoji}'+'\n'

					shop_product['price']['Москва'] = price

					keyboard.append({'url':'https://www.wildberries.ru/catalog/'+str(str(product['id']))+'/detail.aspx?targetUrl=XS','text':'Ссылка'})
					keyboard = {'inline_keyboard':[keyboard]}
					
					if text != '':
						photo = check_photo(str(product['id']))

						send_message(text,chat_id,keyboard=keyboard,extra_chat_ids=extra_chat_ids,photo=photo)
			
			page+=1


		for id_ in shops[sup_id]['products']:
			if not str(id_) in str(ids):
				product = shops[sup_id]['products'][id_]
				name = product['name']
				if product['price']['Москва'] != None:
					text = f'Товар {name}, больше не в продаже🔴'
					product['price']['Москва'] = None
					photo = check_photo(str(id_))
					keyboard = []
					keyboard.append({'url':'https://www.wildberries.ru/catalog/'+id_+'/detail.aspx?targetUrl=XS','text':'Ссылка'})
					keyboard = {'inline_keyboard':[keyboard]}

					send_message(text,chat_id,keyboard=keyboard,extra_chat_ids=extra_chat_ids,photo=photo)

	if shops != old_shops:
		save_products(shops,chat_id,'_shop')



def check_competitor(chat_id):
	shared = db.get_shared(chat_id)
	extra_chat_ids = []
	
	if shared and shared != '':
		if 'shared' in shared:
			return
		else:
			extra_chat_ids = shared.split()
	
	products = get_products(chat_id,'_wb_competive')
	old_products = copy.deepcopy(products)
	update_products = check_competitor_products(products.keys(),regions['Москва'])
	text = ''
	count = 0

	for product in update_products:
		try:
			keyboard = []
			product_in_file = products[str(str(product['id']))]
			price = str(product['salePriceU']//100)
			name = product_in_file['name']
			region = 'Москва'
			
			if product['sizes'][0]['stocks'] == []:
				price = None

			if product_in_file['price'][region] != price:
				if not product_in_file['price'][region] is None:
					if not price is None:
						change = int(price) - int(product_in_file['price'][region])
						if change > 0:
							symbol = '+'
							emoji = '🟢'
						else:
							symbol = ''
							emoji = '🔴'
				else:
					symbol = ''
					emoji = '🟢'
					change = 'Снова в продаже'

				count += 1
				if product_in_file['price'][region] != '0':
					if price:
						text = f'Цена на товар {name} изменилась: {price} ({symbol}{change}){emoji}'+'\n'
					else:
						text = f'Товар {name}, больше не в продаже🔴'

				keyboard.append({'url':'https://www.wildberries.ru/catalog/'+str(product['id'])+'/detail.aspx?targetUrl=XS','text':'Ссылка'})
				
				product_in_file['price'][region] = price
				keyboard = {'inline_keyboard':[keyboard]}
				is_photo = False
				count_photo = 0
				photo = check_photo(str(product['id']))
				send_message(text,chat_id,keyboard=keyboard,extra_chat_ids=extra_chat_ids,photo=photo)
		except:
			log_exc()
			continue

	if products != old_products:
		save_products(products,chat_id,'_wb_competive')

#@dp.message_handler()
def start_parse(chat_id,solo=False,warn=True):
	warining_sent = False
	market_places = ['wb']
	full_name_market = {'wb':'WildBerries','ozon':'Ozon'}
	now = datetime.now().strftime("%d.%m")
	blank = 0
	products_chat_id = chat_id
	extra_chat_ids = []
	shared = db.get_shared(chat_id)
	messages = []

	if warn:
		send_message('Подготовка отчёта запущена, ожидайте',chat_id)

	if shared and shared != '':
		if 'shared' in shared:
			if not solo:
				return
			else:
				products_chat_id = shared.split('_')[1]
		elif not solo:
			extra_chat_ids= shared.split()

	user_regions = db.get_user(products_chat_id)[6].split(',')
	product_history = get_products(products_chat_id,'_history')

	for market in market_places:
		count_of_product = 0
		products = get_products(products_chat_id,'_'+market)
		if len(products) == 0:
			blank += 1
			if blank == len(products) - 1:
				send_message(f'Товары не добавлены, для формирования отчёта добавьте товары',chat_id)
			continue
		
		if not warining_sent and not products == []:
			send_message(f'Отчёт по позициям товаров за {now} готовится, ожидайте',chat_id,extra_chat_ids=extra_chat_ids)
			warining_sent = True
		
		for product in products:
			try:
				count_of_product += 1
				#print(count_of_product,'____________________',len(products))

				name = product['name']
				url = product['url']
				if market == 'wb':
					id_ = int(url.split('/')[4].split('/')[0])
				
				full_name = full_name_market[market]
				text = f'<b>{count_of_product}. {name}</b>:\n\n'

				for region in regions:
					if not region in user_regions:
						continue

					text += region+':\n\n'
					if market == 'wb':
						search = []
						for reg_search in product['search']:
							if not region in reg_search[1]:
								reg_search[1][region] = None

					if market == 'ozon' or check_if_product_in_fileselling(id_,regions[region]):
						count = 0
						if market == 'wb':		
							for search in product['search']:
								for i in range(3):
									try:
										count += 1
										name_search = search[0].strip()
										answer_message = get_answer_message(market,url,name_search,search[1],region)
										save_products(products,products_chat_id,'_wb')
										break
									except:
										log_exc()
										answer_message = name_search+' - произошла ошибка⚠️'

								text += answer_message+'\n'

						elif market == 'ozon':
							count += 1
							answer_message = get_answer_message(market,url,product['name'],product['place'],region.lower())
							save_products(products,products_chat_id,'_ozon')
							text += answer_message+'\n'
						text += '\n'
					else:
						text += f'-Нет в наличии\n\n'
			
				messages.append(text)
				
				product_history = get_products(products_chat_id,'_history')
				if not str(id_) in product_history:
					product_history[str(id_)] = []

				elif product_history[str(id_)][-1][0] == datetime.now().strftime("%m.%d.%Y"):
					product_history[str(id_)][-1] = [datetime.now().strftime("%m.%d.%Y"),text]
				
				else:
					product_history[str(id_)].append([datetime.now().strftime("%m.%d.%Y"),text])
				
				save_products(product_history,products_chat_id,'_history')
			except:
				log_exc()
				text += f'{count_of_product}. - {name} произошла ошибка⚠️,попробуйте удалить и снова добавить продукт\n\n'
				messages.append(text)

	j = 0
	do_while = True
	print('messages is ',len(messages))

	while (len(messages) != 0) and (j < len(messages)-1 or do_while):
	 	do_while = False
	 	print(i,j)
	 	for i in range(len(messages)-1,-1,-1):
	 		if len(''.join(messages[j:i+1])) <= 4000:
	 			text = ''.join(messages[j:i+1])
	 			send_message(text,chat_id,extra_chat_ids=extra_chat_ids)
	 			j = i+1
	 			break
	
	send_message(f'Отчёт по позициям товаров за {now} закончен',chat_id,extra_chat_ids=extra_chat_ids,keyboard=True)

def get_answer_message(market,url,name,data,region):
	if market == 'wb':
		number = check_position(name,url,regions[region])
	elif market == 'ozon':
		number = check_product_ozon(url,region=region)

	if number is None:
		answer_message = '<i>'+name+'</i>'+' - товар в выдаче, на 25+ странице🔴'
	elif 'реклама' in str(number):
		num = str(number).split()[1]
		if data[region] is None or not 'реклама' in data[region]:
			answer_message = name+' - Товар рекламируется©,место '+num+' 🟢'
		else:
			diff = str(int(data[region].split()[1])-int(num))
			end = '🟢' if int(diff) >= 0 else '🔴'
			diff = '+'+diff if int(diff) >= 0 else diff

			answer_message = '<i>'+name+'</i>'+' - Товар рекламируется©,место '+str(number)+'('+diff+') '+end

	elif 'нет' in str(number):
		answer_message = '<del>'+name+'</del>'+' - товар отсутствует в выдаче 🔴'

	else:
		if not data[region] or not data[region].isnumeric():
			answer_message = '<i>'+name+'</i>'+' - место '+str(number)+' 🟢'
		else:
			diff = str(int(data[region])-int(number))
			end = '🟢' if int(diff) >= 0 else '🔴'
			diff = '+'+diff if int(diff) >= 0 else diff

			answer_message = '<i>'+name+'</i>'+' - место '+str(number)+'('+diff+') '+end

	data[region] = str(number)

	return answer_message


def send_message(message,chat_id,keyboard=None,extra_chat_ids=[],photo=None):
	extra_chat_ids = [chat_id]+extra_chat_ids
	print('test',extra_chat_ids)
	for chat_id in extra_chat_ids:
		admin_chats = ['340549861','618939593']
		text = urllib.parse.quote_plus(message)
		telegram_api = 'https://api.telegram.org/bot'+token+'/'
		if keyboard == True:
			keyboard = [['Отчёт о позициях товаров','Отслеживание цен и и наличия товаров'],['Аккаунт компании','Настройки']] if not str(chat_id) in admin_chats else [['Отчёт о позициях товаров','Отслеживание цен и и наличия товаров'],['Аккаунт компании','Настройки'],['/info','/post']]
			keyboard = {'keyboard':keyboard,'resize_keyboard':True}
		elif keyboard == None:
			keyboard = [['Ожидайте']]
			keyboard = {'keyboard':keyboard,'resize_keyboard':True}
		
		if not isinstance(keyboard,str):
			keyboard = json.dumps(keyboard)


		if photo:
			url = telegram_api + 'sendPhoto?chat_id='+chat_id+'&caption='+text+'&parse_mode=html&reply_markup='+keyboard
			requests.post(url,files={'photo':photo})
		else:
			url = telegram_api + 'sendMessage?chat_id='+chat_id+'&text='+text+'&parse_mode=html&reply_markup='+keyboard
			requests.get(url)


def get_page(url,name='headers'):
	headers = get_headers(name)
	print(url)
	r = requests.get(url,headers=headers)
	#print(url)
	test(r.text,'test.html')
	json_ = json.loads(r.text)
	
	return json_

def test(content,name):
	with open(name,'w',encoding='utf-8') as f:
		f.write(content)

def get_headers(name='headers'):
	with open(name+'.txt','r',encoding='utf-8') as file:
		headers = file.read()
		headers = headers.splitlines()
		py_headers = {}
		for header in headers:
			key,value = header.split(': ')
			py_headers[key] = value

		return py_headers

def check_adv(query,id_):
	search_url = f'https://catalog-ads.wildberries.ru/api/v5/search?keyword={query}'
	data = get_page(search_url)['adverts']
	number = 1
	if data is None:
		return None
	
	for adv in data:
		if int(adv['id']) == int(id_):
			return number
		number += 1
	return None

def get_name(id_):
	search_url = f'https://wbx-content-v2.wbstatic.net/ru/{id_}.json'
	result = get_page(search_url)
	return result

def check_product(query,id_,last_page=26,region='',extra_params=''):
	number = 1
	for page in range(1,last_page):
		search_url = f'https://search.wb.ru/exactmatch/ru/common/v4/search?appType=1&page={page}&pricemarginCoeff=1.0&query={query}&resultset=catalog&sort=popular&spp=0{region}'+extra_params
		
		try:
			data = get_page(search_url)['data']
		except KeyError:
			return None

		for product in data['products']:
			if int(product['id']) == int(id_):
				return str(number)

			number += 1
		
		if len(data['products']) < 100:
			return None
	else:
		return None

def check_brand(query,id_,region):
	search_url = f'https://wbx-content-v2.wbstatic.net/ru/{id_}.json'
	data = get_page(search_url)['data']

	if not 'brand_id' in data:
		return True

	brand_id = data['brand_id']
	extra = f'&fbrand={brand_id}'

	return check_product(query,id_,10000,region,extra)
	
def check_position(query,url,region):
	id_ = int(url.split('/')[4].split('/')[0])
	adv = check_adv(query,id_)
	if  adv:
		#print('Товар найден среди рекламы')
		return 'реклама '+str(adv)
	
	#print('Товар не рекламный')
	
	if not check_brand(query,id_,region):
		print('Товар отсутствует')
		return 'нет'

	#print('Товар найден в сортировки по бренду')

	return check_product(query,id_,region=region)

def add_competitor_shop(url,chat_id):
	sup_id = url.split('/')[-1]
	try:
		search_url = 'https://www.wildberries.ru/webapi/seller/data/short/'+sup_id
		name = get_page(search_url,'shop')['name']
		user_products = get_products(chat_id,'_shop')

		if sup_id in user_products:
			return 'Такой магазин уже добавлен'

		user_products[sup_id] = {'name':name,'products':{}}
		page = 1

		while True:
			search_url = 'https://catalog.wb.ru/sellers/catalog?appType=1&couponsGeo=12,3,18,15,21&curr=rub&dest=-1029256,-102269,-1252558,-1252424&emp=0&lang=ru&locale=ru&pricemarginCoeff=1.0&reg=0&regions=68,64,83,4,38,80,33,70,82,86,75,30,69,1,48,22,66,31,40,71&spp=0&supplier='+sup_id+'&page='+str(page)
			products = get_page(search_url)['data']['products']
			if len(products) == 0:
				break
			
			for product in products:
				if not str(str(product['id'])) in user_products:
					price = {}
					for region in regions:
						price[region] = product['salePriceU']//100
					
					user_products[sup_id]['products'][str(str(product['id']))] = {'name':product['name'],'price':price}
			page+=1
		
		if len(user_products) > 0:
			save_products(user_products,chat_id,'_shop')
			return f'Магазин {name} успешно добавлен'
	except:
		log_exc()

	return 'Магазин пуст или неправильный url'



if __name__ == '__main__':
	#start_parse('618939593')
	#start_loop()
	#send_message('~Товар~','618939593')
	#print(get_name('43475901'))
	#check_competitor('618939593')
	#add_competitor_shop('https://www.wildberries.ru/seller/70619','618939593')
	check_competitor_shop('340549861')