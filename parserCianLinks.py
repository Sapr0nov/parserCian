# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen
from cefpython3 import cefpython as cef
import os
import re 
import csv
import sys
import math
import configparser

flats = []
prices = []
config = configparser.ConfigParser()

if os.path.isfile('cian_config.ini') == False: 
    print('установка значений по умолчанию')
    COOKIEinput = input('Введите COOKIES и нажмите Enter для продолжения')
    config['DEFAULT'] = {
        'COOKIES': COOKIEinput,
        'FILE': 'output',
        'LINKS_FILE': 'links-list',
        'HOST': '',
        'PRICES': '',
        'URL': 'https://nn.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&region=4885&p=2',
        }
    with open('cian_config.ini', 'w') as configfile:
        config.write(configfile)

config_file = config.read('cian_config.ini')

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

def get_pages_count(html, URL, first=True):
    soup = BeautifulSoup(html, 'html.parser')
    captcha = soup.find('form', {'id' : 'form_captcha'})
    error404 = soup.find('h5', class_='error-code')
    if error404:
        return '404'
    
    if captcha:
        return 'captcha'

    flatsAll = soup.find('div', {'data-name' : 'SummaryHeader'})
    if flatsAll:
        numbers = flatsAll.get_text()
        pages = math.ceil(int(re.sub('[^0-9]+', '', numbers)) / 28)
    else:
        numbers = 1
        pages = 1
 
    if pages > 54:
        if first:
            prices = get_links_pages(URL)
        return 54
    else:
        return pages
#//get_pages_count

def get_links_pages(URL):
    prices.append(0)
    prices_success = True

    while prices_success:
        pages = 1
        delta = 1000000
        direction = 'more' # more - увеличиваем цену / less уменьшаем 
        maxprice = prices[-1]

        while pages < 40 or pages > 50:
            
            print('price ' + str(prices[-1]) + ' подбор...')
            if pages > 50:
                if direction == 'less': # слишком мало убавили 
                    delta = math.ceil(delta * 1.5)
                else:
                    delta = math.ceil(delta * 0.7) # слишком сильно добавили
                maxprice -= delta
                direction = 'less'
                if maxprice < prices[-1]:
                    delta = math.ceil(delta * 0.5)
                    maxprice = math.ceil(prices[-1] + delta / 2)
            else:  # page < 40
                if direction == 'more': # слишком мало добавили
                    delta = math.ceil(delta * 1.5)
                else:
                    delta = math.ceil(delta * 0.7) # слишком сильно убавили
                maxprice += delta
                direction = 'more'

            if maxprice > 9899999999:
                break

            URLmodified = URL + '&maxprice='+ str(maxprice) + '&minprice='+ str(prices[-1] + 1)
            
            successful = False
            while not successful:   
                html = get_html(URLmodified)
                pages = get_pages_count(html.text, URLmodified, False)
                if pages == 'captcha':
                    captcha(URLmodified)
                    config_file = config.read('cian_config.ini')
                    HEADERS['cookie'] = config['DEFAULT']['COOKIES'];
                else:
                    successful = True

        prices.append(maxprice)
        if maxprice > 9899999999:
            prices_success = False
    return prices

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
    URL = input('Введите URL (https://spb.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&p=2&region=2): ')
    if URL == '':
        URL = config['DEFAULT']['URL']
        prices = config['DEFAULT']['PRICES'].strip('][').split(', ')
        print('default: '+URL)
    else:
        config['DEFAULT']['URL'] = URL
        config['DEFAULT']['PRICES'] = ''
        with open('cian_config.ini', 'w') as configfile:
            config.write(configfile)
        
    params = {
        'p': 1
    }
    URL = URL.strip();
    html = get_html(URL, params = params)
    if html.status_code == 200:
        addInfo = get_content(html.text)
        successful = False
        while not successful:    
            html = get_html(URL)
            addInfo = get_content(html.text)
            if addInfo == 'captcha':
                captcha(URL)
                config_file = config.read('cian_config.ini')
                HEADERS['cookie'] = config['DEFAULT']['COOKIES'];
            else:
                successful = True

        if config['DEFAULT']['PRICES'] == '':
            pages_count = get_pages_count(html.text, URL)
        else:
            prices = config['DEFAULT']['PRICES'].strip('][').split(', ')
            print('Найден список ценовых диапазонов: '+str(prices))

        # цикл на каждый диапазон цен
        pre_price = 0
        for price in prices:
            if int(price) == 0:
                pre_price = price
            else:
                URLmodified = URL + '&maxprice='+ str(price) + '&minprice='+ str(pre_price)
                print(URLmodified)
                pages_count = get_pages_count(html.text, URLmodified, False)

                # запускаем цикл парсинга на каждую страницу пагинации
                for page in range(1, pages_count + 1):
                    print(f'Парсинг страницы {page} из {pages_count} диапазон цен {pre_price} - {price}...')
                    params['p'] = page
                    params['minprice'] = pre_price
                    params['maxprice'] = price

                    successful = False
                    while not successful:    
                        html = get_html(URL, params = params)
                        addInfo = get_content(html.text)
                        if addInfo == 'captcha':
                            captcha(URL)
                            config_file = config.read('cian_config.ini')
                            HEADERS['cookie'] = config['DEFAULT']['COOKIES'];
                        else:
                            successful = True
                    else:
                        flats.extend(addInfo)

                    pre_price = int(price) + 1
    else:
        print('Site unavailable')

    save_file(flats, config['DEFAULT']['LINKS_FILE']+'.csv')
    os.startfile(config['DEFAULT']['LINKS_FILE']+'.csv')
#//parse

def captcha(URL):
    check_versions()
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    cef.Initialize()
    browser = cef.CreateBrowserSync(url=URL, window_title="Капча! "+URL)
    browser.SetClientHandler(LoadHandler())
    cef.MessageLoop()
    return True

class LoadHandler(object):
    def OnLoadingStateChange(self, browser, is_loading, **_):
        if is_loading:
            manager = cef.CookieManager.GetGlobalManager()
            self.cookie_visitor = CookieVisitor()
            result = manager.VisitAllCookies(self.cookie_visitor)
            if not result:
                print("Error: could not access cookies")
            else:
                while self.cookie_visitor.show_cookie() == '':
                    self.cookie_visitor.show_cookie()
                    print('...'+self.cookie_visitor.show_cookie())
                COOKIES = self.cookie_visitor.show_cookie()
                print(COOKIES)
                if COOKIES.find('anti_bot') > 0:
                    COOKIES = COOKIES.replace('%', '%%')
                    if COOKIES.find('GRECAPTCHA') > 0:
                        COOKIES = COOKIES.replace('_GRECAPTCHA', 'GC')
                        letter = input('COOKIES содержат _GRECAPTCHA, хотите ввести COOKIES вручную? y/n:')
                        if letter=='y' or letter=='Y':
                            COOKIES = input('Введите новые COOKIES:')
                    config['DEFAULT']['COOKIES'] = COOKIES
                    with open('cian_config.ini', 'w') as configfile:
                        config.write(configfile)
                    print('update Cookies')
                    browser.CloseBrowser(True)
                    return True        

class CookieVisitor(object):
    cookie_str = ''    
    def Visit(self, cookie, count, total, delete_cookie_out):
        self.cookie_str +=  cookie.GetName() + '=' + cookie.GetValue() + '; '
        return True

    def show_cookie(self):
        return self.cookie_str

def check_versions():
    ver = cef.GetVersion()
    assert cef.__version__ >= "57.0", "CEF Python v57.0+ required to run this"

# starting programm

parse()