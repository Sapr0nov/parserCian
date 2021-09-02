import requests
from bs4 import BeautifulSoup
from cefpython3 import cefpython as cef
from urllib.request import urlopen
import csv
import os
import base64
import re 
import math
import configparser

flats = []
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) + "/"
CONFIG_FILE = "cian_config.ini"
config = configparser.ConfigParser()

if os.path.isfile(BASE_DIR + 'cian_config.ini') == False: 
    print('установка значений по умолчанию')
    config['DEFAULT'] = {
        'COOKIES': '',
        'FILE': 'output',
        'LINKS_FILE': 'links-list',
        'HOST': '',
        'PRICES': '',
        'DELTA_PRICE': '1000000',
        'URL': 'https://nn.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&region=4885',
        }
    print('запись значений по умолчанию в файл cian_config.ini')
    with open(BASE_DIR + CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
        configfile.close()

print('чтение значений по умолчанию в файл cian_config.ini')
config_file = config.read(BASE_DIR + CONFIG_FILE)

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
    r = requests.get(url, headers=HEADERS, params=params, allow_redirects=False)
    return r
#//get_html

def get_pages_count(url, html):
    soup = BeautifulSoup(html, 'html.parser')
    captcha = soup.find('form', {'id' : 'form_captcha'})

    if captcha:
        return 'captcha'

    flatsAll = soup.find('div', {'data-name' : 'SummaryHeader'})
    if flatsAll:
        numbers = flatsAll.get_text()
    else:
        numbers = 1

    print ('объявлений:',numbers)
    numbers = math.ceil(int(re.sub('[^0-9]+', '', numbers)))
    pages = math.ceil(numbers / 28)

    if pages <= 54:
        return pages

    print ('Единоразово Cian отдает 1512 объявлений. Производится попытка разбить на несколько запросов- от ' + str( math.ceil(numbers / 1512)) )

    prices = []
    prices.append(0)
    delta = int( config['DEFAULT']['DELTA_PRICE']) # стартовый прирост к цене при поиске диапазона 1000000
    foundOrders = 0
    new_numbers = 0

    while foundOrders + new_numbers < numbers:
        params = {
            'minprice' : prices[len(prices)-1],
            'maxprice' : prices[len(prices)-1] + delta
        }

        html = get_html(url, params = params)

        if html.status_code == 302:
            return 'captcha'

        if html.status_code == 200:
            soup = BeautifulSoup(html.text, 'html.parser')
            flatsAll = soup.find('div', {'data-name' : 'SummaryHeader'})
            if flatsAll:
                new_numbers = int(re.sub('[^0-9]+', '', flatsAll.get_text() ))
                print ('подбор... от ' + str( prices[len(prices)-1] ) + ' до ' + str( prices[len(prices)-1] + delta ) + " найдено " + str(new_numbers))

                if new_numbers >= 1000 and new_numbers < 1500:
                    foundOrders = foundOrders + new_numbers
                    prices.append(prices[len(prices)-1] + delta)
                    delta = int( config['DEFAULT']['DELTA_PRICE'])
                else:
                    if new_numbers < 1000:
                        delta = math.ceil(delta * 1.2)
                    else:
                        delta = math.ceil(delta / 1.2)
                # контрольный выход при поиске более 1 000 000 000 руб
                if delta > 1000000000:
                    prices.append(prices[len(prices)-1] + delta)
                    new_numbers = 1000000

    return prices

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
                'link':   config['DEFAULT']['host'] + item.find('a').get('href'),
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
    file.close()
# //save_file

def parse():
    URL = input('Введите URL: ')
    if URL == '':
        URL = config['DEFAULT']['URL']

    params = {
        'p': 1
    }

    print('default: ',URL)
    URL = URL.strip()
    html = get_html(URL, params = params)

    if html.status_code == 302:
        captcha(URL)
        config_file = config.read(BASE_DIR + CONFIG_FILE)
        HEADERS['cookie'] = config['DEFAULT']['COOKIES']
        html = get_html(URL, params = params)

    if html.status_code == 301:
        print('Старница не найдена, перенаправление 301')
        print(f'url = {URL}&minprice={prices[i-1]}&maxprice={prices[i]-1}&p={page}' )
        
    if html.status_code == 200:
        pages_count = get_pages_count(URL, html.text)
        # если вернулось число - обычный перебор, если массив (есть __len__) то перебираем по ценам
        if hasattr(pages_count, "__len__"):

            prices = pages_count
            pages_count = 0

            for i in range(1, len(prices) ):
            
                params = {
                    'p': 1,
                    'minprice' : prices[i-1],
                    'maxprice' : prices[i]-1
                }

                print(f'url = {URL}&minprice={prices[i-1]}&maxprice={prices[i]-1}&p=1' )
                # запускаем цикл парсинга на каждую страницу пагинации для интервалов
                # определяем количество страниц в текущем диапазоне
                html = get_html(URL, params = params)
                
                if html.status_code == 302:
                    while html.status_code == 302:
                        html = checkCaptha(URL, params)

                pages_count = get_pages_count(URL, html.text)

                for page in range(1, pages_count + 1):
                    
                    params['p'] = page
                    html = get_html(URL, params = params)
                    print(f'Парсинг страницы {page} из {pages_count} Статус страницы {html.status_code}...')

                    # если ответ 301 вероятно страницы нет..
                    if html.status_code == 301:
                        print('Старница не найдена, перенаправление 301')
                        print(f'url = {URL}&minprice={prices[i-1]}&maxprice={prices[i]-1}&p={page}' )
                        continue

                    # если ответ 302 вероятно капча...
                    if html.status_code == 302:
                        while html.status_code == 302:
                            html = checkCaptha(URL, params)
                            print(html.status_code)

                    if html.status_code == 200:
                        addInfo = get_content(html.text)
                        flats.extend(addInfo)

        # запускаем цикл парсинга на каждую страницу пагинации
        else:
            for page in range(1, pages_count + 1):
                
                params['p'] = page
                html = get_html(URL, params = params)
                print(f'Парсинг страницы {page} из {pages_count} Статус страницы {html.status_code}...')

                # если ответ 301 вероятно страницы нет..
                if html.status_code == 301:
                    print('Старница не найдена, перенаправление 301')
                    print(f'url = {URL}&minprice={prices[i-1]}&maxprice={prices[i]-1}&p={page}' )
                    continue

                # если ответ 302 вероятно капча...
                if html.status_code == 302:
                    while html.status_code == 302:
                        html = checkCaptha(URL, params)

                addInfo = get_content(html.text)
                flats.extend(addInfo)

    
    save_file(flats, BASE_DIR + config['DEFAULT']['LINKS_FILE'] + ".csv")
    os.startfile(BASE_DIR + config['DEFAULT']['LINKS_FILE'] + ".csv")
    print ('Парсинг закончен результаты сохранены в файл')
#//parse

def checkCaptha(URL, params):

    save_file(flats, BASE_DIR + config['DEFAULT']['LINKS_FILE'] + "_tmp" + ".csv")
    captcha(URL)
    config_file = config.read(BASE_DIR + CONFIG_FILE)
    HEADERS['cookie'] = config['DEFAULT']['COOKIES']
    html = get_html(URL, params = params)

    return html

def captcha(URL):
    check_versions()
    cef.Initialize()
    currentURL = URL
    browser = cef.CreateBrowserSync(url=currentURL, window_title="Captcha!")
    browser.SetClientHandler(LoadHandler())

    cef.MessageLoop()
    return True

class LoadHandler(object):
    def OnLoadingStateChange(self, browser, is_loading, **_):

        if is_loading:
            manager = cef.CookieManager.GetGlobalManager()
            self.cookie_visitor = CookieVisitor()
             
            result = manager.VisitAllCookies(self.cookie_visitor)
            
            i = 0
            successful = False

            print ('looking for cookies... ')
            while not successful:
                COOKIES = self.cookie_visitor.cookie_str
                i=i+1
                if COOKIES.find('anti_bot') > 0:
                    successful = True
                if i > 300:
                    successful = True
                

            if COOKIES.find('anti_bot') > 0:
                print("COOKIE anti-bot найдена, сохраняю новое значение... ")
                COOKIES = COOKIES.replace('%', '%%')
                config['DEFAULT']['COOKIES'] = COOKIES
                with open(BASE_DIR + CONFIG_FILE, 'w') as configfile:
                    config.write(configfile)
                    configfile.close()
                browser.CloseBrowser(True)

            if not result:
                print("Error: не удалось получить COOKIE")

class CookieVisitor(object):
    cookie_str = '' 
    def Visit(self, cookie, count, total, delete_cookie_out):
        self.cookie_str +=  cookie.GetName() + '=' + cookie.GetValue() + '; '
        return True

    def get_cookie(self):
        return self.cookie_str

def check_versions():
    ver = cef.GetVersion()
    assert cef.__version__ >= "57.0", "CEF Python v57.0+ required to run this"

# starting programm

parse()