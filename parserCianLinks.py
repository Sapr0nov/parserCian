# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen
import csv
import os
import base64
import re 
import math
import configparser
import sys

flats = []
config = configparser.ConfigParser()
config_file = config.read('config.ini')

if os.path.isfile('config.ini') == False: 
    print('установка значений по умолчанию')
    COOKIES = input('Введите COOKIES и нажмите Enter для продолжения')
    config['DEFAULT'] = {
        'COOKIES': COOKIES,
        'FILE': 'output.csv',
        'LINKS_FILE': 'links-list',
        'HOST': '',
        }
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    config_file = config.read('config.ini')

HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36',
	'Cache-Control': 'max-age=0',
	'Connection': 'keep-alive',
	'Keep-Alive': '300',
	'Accept-Language': 'en-us,en;q=0.5',
	'dnt': '1',
    'cookie': config['DEFAULT']['COOKIES'],
    'upgrade-insecure-requests': '1',
    'sec-fetch-user': '?1',
    'sec-fetch-site': 'none',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-dest': 'document'
    }

def get_html (url, params=None):
    r = requests.get(url, headers=HEADERS,params=params)
    return r
#//get_html

def get_pages_count(html):
    soup = BeautifulSoup(html, 'html.parser')
    flatsAll = soup.find('div', {'data-name' : 'SummaryHeader'})
    if flatsAll:
        numbers = flatsAll.get_text()
    else:
        numbers = 1
    print ('объявлений:',numbers)
    pages = math.ceil(int(re.sub('[^0-9]+', '', numbers)) / 28)
    if pages > 54:
        return 54
    else:
        return pages
#//get_pages_count

def get_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    captcha = soup.find('form', {'id' : 'form_captcha'})
    error404 = soup.find('h5', class_='error-code')
    if error404:
        return '404'
    
    if captcha:
        return 'captcha'
    
    data = []
    items = soup.find_all('div', {'data-name' : 'LinkArea'})

    for item in items:
        data.append({
            'link':  config['DEFAULT']['HOST'] + item.find('a').get('href'),
        })
    return data
# //get_content

def save_file(items, path):
    with open(path, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['ссылка'])
        for item in items:
            link  = item['link'].encode('ansi', errors='ignore').decode('cp1251')
            writer.writerow([link])
# //save_file

def parse():
    URL = input('Введите URL: ')
    if URL == '':
        URL = config['DEFAULT']['URL']
        print('default: ',URL)

    params = {
        'p': 1
    }
    URL = URL.strip();
    html = get_html(URL, params = params)
    if html.status_code == 200:
        addInfo = get_content(html.text)
        successful = False
        while not successful:  
            if addInfo == 'captcha':
                COOKIES = input('Введите COOKIES и нажмите Enter для продолжения (пустой ввод - выход из программы)')
                if COOKIES == '':
                    sys.exit("Вы завершили работу")
                config['DEFAULT']['COOKIES'] = COOKIES
                with open('config.ini', 'w') as configfile:
                    config.write(configfile)
                HEADERS['cookie'] = COOKIES;
            else:
                successful = True
                
        pages_count = get_pages_count(html.text)
        # запускаем цикл парсинга на каждую страницу пагинации
        for page in range(1, pages_count + 1):
            print(f'Парсинг страницы {page} из {pages_count}...')
            params['p'] = page
            successful = False
            while not successful:    
                html = get_html(URL, params = params)
                addInfo = get_content(html.text)
                if addInfo == 'captcha':
                    COOKIES = input('Введите COOKIES и нажмите Enter для продолжения')
                    config['DEFAULT']['COOKIES'] = COOKIES
                    with open('config.ini', 'w') as configfile:
                        config.write(configfile)
                    HEADERS['cookie'] = COOKIES;
                    if COOKIES == '':
                        save_file(flats, config['DEFAULT']['LINKS_FILE'])
                        os.startfile(config['DEFAULT']['LINKS_FILE'])
                        break
                else:
                    successful = True
            else:
                flats.extend(addInfo)
    else:
        print('Site unavailable')

    save_file(flats, config['DEFAULT']['LINKS_FILE'])
    os.startfile(config['DEFAULT']['LINKS_FILE'])
#//parse

# starting programm

parse()