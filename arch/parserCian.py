import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen
import csv
import os
import base64
import re 
import math

URL = 'https://krym.cian.ru/cat.php?currency=2&deal_type=sale&engine_version=2&maxprice=3299999&offer_type=flat&region=184739'
ANTI_BOT = '"2|1:0|10:1612387073|8:anti_bot|40:eyJyZW1vdGVfaXAiOiAiNjIuMTgxLjUxLjUifQ==|94849fdff4f9be072468679b5ae925ce345e45c891909a4d2e8d2c780400591a"'
HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36',
	'Cache-Control': 'max-age=0',
	'Connection': 'keep-alive',
	'Keep-Alive': '300',
	'Accept-Language': 'en-us,en;q=0.5',
	'dnt': '1',
    'cookie': 'afUserId=f3f8f60c-56c1-46d4-9984-ae7e99dedbe0-p; __cfduid=dfb75d98003286be5284e70d2f98ee1041612371671; _CIAN_GK=d51a93dd-d444-4cb7-bbd9-f9da7768d2fb; _gcl_au=1.1.1379731776.1612371672; login_mro_popup=meow; sopr_utm=%7B%22utm_source%22%3A+%22direct%22%2C+%22utm_medium%22%3A+%22None%22%7D; first_visit_time=1612371696219; uxfb_usertype=searcher; uxs_uid=79b36740-6641-11eb-90c7-839a8faa80af; uxs_mig=1; tmr_lvidTS=1593435826451; tmr_lvid=facb536fba54871935496034bf60538a; _ga=GA1.2.828095930.1612371697; _gid=GA1.2.37862445.1612371697; _fbp=fb.1.1612371697021.1127807772; fingerprint=33f12b8a4f15aeb5fb3853d9c11d288e; serp_registration_trigger_popup=1; cookie_agreement_accepted=true; serp_stalker_banner=1; __cf_bm=2ad773bae72c0b4233a47c554e31e93e6f8a5dc4-1612421683-1800-AaojHood212jrAMpr4W1RTe11fERwJzqBPlns+PATgmDYzy/ofJtTcU2x8Bp8r7G9CyO8BsvO+lHmc93OaHu9hA=; sopr_session=4bf086f0e4954bef; session_region_id=184739; session_main_town_region_id=184739; _gat_UA-30374201-1=1; _dc_gtm_UA-30374201-1=1; tmr_detect=0%7C1612422278456; tmr_reqNum=1392',
    'upgrade-insecure-requests': '1',
    'sec-fetch-user': '?1',
    'sec-fetch-site': 'none',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-dest': 'document'
    }
COOKIES = {
    'anti_bot': ANTI_BOT,
    'session_main_town_region_id' : '184734',
    'login_mro_popup' : '',
    'serp_registration_trigger_popup' : '1',
    '_CIAN_GK' : 'd51a93dd-d444-4cb7-bbd9-f9da7768d2fb',
    'sopr_utm' : '%7B%22utm_source%22%3A+%22direct%22%2C+%22utm_medium%22%3A+%22None%22%7D',
    'uxfb_usertype' : 'searcher',
    'tmr_lvid' : 'facb536fba54871935496034bf60538a',
    'tmr_reqNum' : '1384',
    'serp_stalker_banner' : '1',
    'cookie_agreement_accepted' : 'true',
    '__cf_bm' : '2ad773bae72c0b4233a47c554e31e93e6f8a5dc4-1612421683-1800-AaojHood212jrAMpr4W1RTe11fERwJzqBPlns+PATgmDYzy/ofJtTcU2x8Bp8r7G9CyO8BsvO+lHmc93OaHu9hA=',
    '_fbp' : 'fb.1.1612371697021.1127807772',
    '_gid':'GA1.2.37862445.1612371697',
    '_ga':'GA1.2.828095930.1612371697',
    'tmr_lvidTS':'1593435826451',
    'uxs_mig':'1',
    '__cfduid':'dfb75d98003286be5284e70d2f98ee1041612371671',
    'fingerprint':'33f12b8a4f15aeb5fb3853d9c11d288e',
    'first_visit_time':'1612371696219',
    '_gcl_au':'1.1.1379731776.1612371672',
    'uxs_uid':'79b36740-6641-11eb-90c7-839a8faa80af',
    'sopr_session':'4bf086f0e4954bef',
    'session_region_id':'184739',
    'session_main_town_region_id':'184739',
    'afUserId':'f3f8f60c-56c1-46d4-9984-ae7e99dedbe0-p',
    
    
}
HOST = '' #'https://cian.ru'
FILE = 'output.csv'
flats = []

def get_html (url, params=None):
    r = requests.get(url, headers=HEADERS, cookies=COOKIES, params=params)
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
    if captcha:
        return 'captcha'
    else:
        items = soup.find_all('div', {'data-name' : 'LinkArea'})
        data = []

        for item in items:
            title = item.find('span', {'data-mark' : 'OfferTitle'})
            if title:
                title = title.get_text()
            else:
                title = 'не найдено'
            
            addresses = item.find_all('a',{'data-name':'GeoLabel'})
            address = ''
            if addresses:
                for part in addresses:
                    address = address + part.get_text()
            else:
                address = 'не найдено'

            priceSpan = item.find('span', {'data-mark' : 'MainPrice'})
            if priceSpan:
                price = priceSpan.get_text()
            else:
                price = 'не найдено'

            pBlocks = item.find_all('p')
            if pBlocks:
                desc = pBlocks[-1] 
                if desc:
                    description = desc.get_text()
                else:
                    description = 'не найдено'
            else:
                description = 'не найдено'


            data.append({
                'link':  HOST + item.find('a').get('href'),
                'price': price,
                'address':  address,
                'title':  title,
                'description':description,
            })
        return data
# //get_content

def save_file(items, path):
    with open(path, 'w', newline='') as file: #,encoding='cp1251'
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['название','ссылка','цена','адрес','описание'])
        for item in items:
            title = item['title'].encode('ansi', errors='ignore').decode('cp1251').replace('•',' ')
            link  = item['link'].encode('ansi', errors='ignore').decode('cp1251')
            price = item['price'].encode('ansi', errors='ignore').decode('cp1251')
            address = item['address'].encode('ansi', errors='ignore').decode('cp1251')
            description = item['description'].encode('ansi', errors='ignore').decode('cp1251')
            
            writer.writerow([title,link,price,address,description])
# //save_file

def parse():
    URL = input('Введите URL: ')
    if URL == '':
        URL = 'https://krym.cian.ru/cat.php?currency=2&deal_type=sale&engine_version=2&maxprice=3299999&offer_type=flat&region=184739'

    params = {
        'p': 1
    }
    print('default: ',URL)
    URL = URL.strip();
    html = get_html(URL, params = params)
    if html.status_code == 200:
        pages_count = get_pages_count(html.text)
        # запускаем цикл парсинга на каждую страницу пагинации
        for page in range(1, pages_count + 1):
            print(f'Парсинг страницы {page} из {pages_count}...')
            successful = False
            params['p'] = page
            while not successful:    
                html = get_html(URL, params = params)
                addInfo = get_content(html.text)
                if addInfo == 'captcha':
                    ANTI_BOT = input('Введите ANTI_BOT и нажмите Enter для продолжения')
                else:
                    successful = True
            else:
                flats.extend(addInfo)
    else:
        print('Site unavailable')
    
    save_file(flats, FILE)
    os.startfile(FILE)
#//parse

# starting programm

parse()