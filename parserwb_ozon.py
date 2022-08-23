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

regions = {
			'Москва':'&couponsGeo=12,3,18,15,21&curr=rub&dest=-1029256,-102269,-162903,-446078&emp=0&lang=ru&locale=ru&reg=0&regions=68,64,83,4,38,80,33,70,82,86,75,30,69,22,66,31,40,1,48,71&',
			'Казань':'&regions=68,64,83,4,38,80,33,70,82,86,30,69,22,66,31,40,1,48&reg=0&emp=0&locale=ru&lang=ru&curr=rub&couponsGeo=12,7,3,6,18,22,21&dest=-1075831,-79374,-367666,-2133466&'
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

driver = create_driver()

def get_page_driver(url,region):
	while True:
		try:
			print(url)
			driver.get(url)
			sleep(0.1)
			load_cookie(region)
			sleep(0.4)

			data = driver.find_element(By.XPATH,"/html/body").text
			#test(data,'test.html')
			driver.delete_all_cookies()
			
			return json.loads(data)
		except:
			traceback.print_exc()
			continue

def get_category(id_):
	search_url = 'https://www.ozon.ru/product/'+str(id_)
	driver.get(search_url)
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
	id_ = id_.split('/?')[0].split('-')[-1]

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
	input()
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

def start_loop():
	print('Петля запущена')
	BASE_DIR = os.path.dirname(os.path.abspath(__file__))
	db_path = os.path.join(BASE_DIR, "db.db")

	db = SQLighter(db_path)
	
	while  True:
		sended_message = False
		while True:
			try:
				users = db.get_users()

				for user in users:
					if os.path.exists('products/products_wb_competive '+user[1]+'.json'):
						check_competitor(user[1])
			except:
				traceback.print_exc()

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
							traceback.print_exc()
						days_past = 0

					db.update_user(days_max,days_past,user[1])
				sended_message = True
			if hour == '11':
				break
			
			sleep(3)

def check_if_product_in_fileselling(id_,exctra):
	search_url = f'https://card.wb.ru/cards/detail?spp=0&{exctra}pricemarginCoeff=1.0&appType=1&nm='+str(id_)
	data = get_page(search_url)['data']['products'][0]

	if 'wh' in data:
		return True

	return False


def check_competitor_products(ids,exctra):
	search_url = f'https://card.wb.ru/cards/detail?spp=0&{exctra}pricemarginCoeff=1.0&appType=1&nm='+';'.join(ids)
	data = get_page(search_url)

	return data['data']['products']

def check_competitor(chat_id):
	products = get_products(chat_id,'_wb_competive')
	old_products = copy.deepcopy(products)
	update_products = check_competitor_products(products.keys(),regions['Москва'])
	text = ''
	count = 0
	keyboard = []

	for product in update_products:
		product_in_file = products[str(product['id'])]
		price = str(product['salePriceU']//100)
		name = product_in_file['name']
		region = 'Москва'
		
		if not 'wh' in product:
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
					text += str(count)+'. '+f'Цена на товар {name} изменилась: {price} ({symbol}{change}){emoji}'+'\n'
					keyboard.append({'url':'https://www.wildberries.ru/catalog/'+str(product['id']),'text':'https://www.wildberries.ru/catalog/'+str(product['id'])})
				else:
					text += str(count)+'. '+f'Товар {name}, больше не в продаже🔴'
			
			product_in_file['price'][region] = price
		

	if products != old_products:
		keyboard = {'inline_keyboard':[keyboard]}
		send_message(text,chat_id,keyboard=keyboard)
		save_products(products,chat_id,'_wb_competive')

#@dp.message_handler()
def start_parse(chat_id):
	warining_sent = False
	market_places = ['wb','ozon']
	for market in market_places:
		products = get_products(chat_id,'_'+market)
		
		if not warining_sent and not products == []:
			now = datetime.now().strftime("%d.%m")
			send_message(f'Отчёт по позициям товаров за {now} готовится, ожидайте',chat_id)
			warining_sent = True
		
		for product in products:
			print(product)
			name = product['name']
			url = product['url']
			if market == 'wb':
				id_ = int(url.split('/')[4].split('/')[0])
			text = f'<b>{market} -> {name}</b>:\n\n'

			for region in regions:
				text += region+':\n\n'
				if market == 'wb':
					search = []
					for reg_search in product['search']:
						if reg_search[1] is None or not 'Москва' in reg_search[1]:
							search.append([reg_search[0],{'Москва':reg_search[1],'Казань':None}])
						else:
							search.append(reg_search)
					
					product['search'] = search

				if market == 'ozon' or check_if_product_in_fileselling(id_,regions[region]):
					count = 0
					if market == 'wb':		
						for search in product['search']:
							try:
								count += 1
								name_search = search[0].strip()
								print(name_search)
								answer_message = get_answer_message(market,url,name_search,search[1],region)
								save_products(products,chat_id,'_wb')
							except:
								traceback.print_exc()
								answer_message = name_search+' - произошла ошибка⚠️'

							text += str(count)+'. '+answer_message+'\n'

					elif market == 'ozon':
						count += 1
						answer_message = get_answer_message(market,url,product['name'],product['place'],region.lower())
						save_products(products,chat_id,'_ozon')
						text += str(count)+'. '+answer_message+'\n'
					text += '\n'
				else:
					text += f'-Нет в наличии\n\n'
		
			send_message(text,chat_id)
	
	send_message(f'Отчёт по позициям товаров за {now} закончен',chat_id)

def get_answer_message(market,url,name,data,region):
	if market == 'wb':
		number = check_position(name,url,regions[region])
	elif market == 'ozon':
		number = check_product_ozon(url,region=region)

	if number is None:
		answer_message = name+' - товар в выдаче, на 25+ странице🔴'
	elif 'реклама' in str(number):
		num = str(number).split()[1]
		if data[region] is None or not 'реклама' in data[region]:
			answer_message = name+' - Товар рекламируется©,место '+num+' 🟢'
		else:
			diff = str(int(data[region].split()[1])-int(num))
			end = '🟢' if int(diff) >= 0 else '🔴'
			diff = '+'+diff if int(diff) >= 0 else diff

			answer_message = name+' - Товар рекламируется©,место '+str(number)+'('+diff+') '+end

	elif 'нет' in str(number):
		answer_message = '<del>'+name+'</del>'+' - товар отсутствует в выдаче 🔴'

	else:
		if not data[region] or not data[region].isnumeric():
			answer_message = name+' - место '+str(number)+' 🟢'
		else:
			diff = str(int(data[region])-int(number))
			end = '🟢' if int(diff) >= 0 else '🔴'
			diff = '+'+diff if int(diff) >= 0 else diff

			answer_message = name+' - место '+str(number)+'('+diff+') '+end

	data[region] = str(number)

	return answer_message


def send_message(message,chat_id,keyboard=None):
	admin_chats = ['340549861','618939593']
	telegram_api = 'https://api.telegram.org/bot5490688808:AAE9EVs8TSxndZt7FDAo7JyjwVIftI6DkH4/'
	chat_id = chat_id
	message = urllib.parse.quote_plus(message)
	
	if not keyboard:
		keyboard = [['Отчёт о позициях товаров'],['Отчёт по действиям конкурентов']] if not str(chat_id) in admin_chats else [['Отчёт о позициях товаров'],['Отчёт по действиям конкурентов'],['/info'],['/post']]
		keyboard = {'keyboard':keyboard,'resize_keyboard':False}
	
	url = telegram_api + 'sendMessage?chat_id='+chat_id+'&text='+message+'&parse_mode=html&reply_markup='+json.dumps(keyboard)
	print(url)
	requests.get(url)

def get_page(url):
	headers = get_headers()
	r = requests.get(url,headers=headers)
	test(r.text,'test.html')
	json_ = json.loads(r.text)
	
	return json_

def test(content,name):
	with open(name,'w',encoding='utf-8') as f:
		f.write(content)

def get_headers():
	with open('headers.txt','r',encoding='utf-8') as file:
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
		print(int(adv['id']))
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
		print('page is ',page)
		search_url = f'https://search.wb.ru/exactmatch/ru/common/v4/search?appType=1&page={page}&pricemarginCoeff=1.0&query={query}&resultset=catalog&sort=popular&spp=0{region}'+extra_params
		data = get_page(search_url)['data']

		for product in data['products']:
			if int(product['id']) == int(id_):
				print(id_)
				return str(number)

			number += 1
		
		if len(data['products']) < 100:
			return None
	else:
		return None

def check_brand(query,id_,region):
	search_url = f'https://wbx-content-v2.wbstatic.net/ru/{id_}.json'
	brand_id = get_page(search_url)['data']['brand_id']
	extra = f'&fbrand={brand_id}'

	return check_product(query,id_,10000,region,extra)
	
def check_position(query,url,region):
	id_ = int(url.split('/')[4].split('/')[0])
	adv = check_adv(query,id_)
	if  adv:
		print('Товар найден среди рекламы')
		return 'реклама '+str(adv)
	
	print('Товар не рекламный')
	
	if not check_brand(query,id_,region):
		print('Товар отсутствует')
		return 'нет'

	print('Товар найден в сортировки по бренду')

	return check_product(query,id_,region=region)

if __name__ == '__main__':
	#start_parse('618939593')
	#start_loop()
	#send_message('~Товар~','618939593')
	#print(get_name('43475901'))
	check_competitor('618939593')