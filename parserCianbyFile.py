# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from cefpython3 import cefpython as cef
import os
import re 
import csv
import sys
import configparser

flats = []
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
        'URL': 'https://nn.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&region=4885',
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

def get_content(html, link):
    soup = BeautifulSoup(html, 'html.parser')
    captcha = soup.find('form', {'id' : 'form_captcha'})
    error404 = soup.find('h5', class_='error-code')
    if error404:
        return '404'

    if captcha:
        return 'captcha'

    data = []
    btiVariables = {
        'Тип дома': 'home',
        'Год постройки': 'year',
        'Построен': 'year',
        'Срок сдачи': 'year_pass',
        'Строительная Серия': 'homeSeries',
        'Строительная серия': 'homeSeries',
        'Тип перекрытий': 'perekritiya',
        'Лифты': 'lift',
        'Подъезды':'podezdi',
        'Мусоропровод': 'garbage',            
        'Отопление':'heat',
        'Аварийность':'avariya',
        'Газоснабжение':'gas',
        'Парковка': 'parking',

        'Тип жилья':'flatType',
        'Санузел':'toilet',
        'Балкон/лоджия':'balkon',
        'Планировка':'plan',
        'Ремонт':'repair',
        'Вид из окон':'window',
        'Высота потолков':'Hceiling',
        'Отделка': 'otdelka',

        'Общая':'area',
        'Жилая':'livingArea',
        'Кухня':'kitchen',
        'Этаж':'floor',
    }
     
    params = {
        'flatId' : '',
        'address' : '',
        'price': '',
        'priceMarket': '',
        'home' : '',
        'parking' : '',
        'description': '',
        'homeSeries' : '',
        'lift' : '',
        'garbage' : '',
        'flatType' : '',
        'repair' : '',
        'balkon' : '',
        'window' : '',
        'toilet' : '',
        'Hceiling' : '',
        'avariya': '',
        'podezdi': '',
        'heat': '',
        'gas': '',
        'perekritiya': '',
        'otdelka': '',
        'livingArea': '',
        'kitchen': '',
        'year': '',
        'year_pass': '',
        'area' : '',
        'floor' : '',
        'plan': '',

        'numberRooms' : '',
        'phone' : '',
        'areaRooms' : '',
        'cityPhone' : '',
        'nameZHK' : '',

        'link': link,
    }
        
    item = soup.find('div', {'data-name' : 'renderOfferCard'})

    addresses = item.find_all('div',{'data-name':'Geo'})
    address = ''
    if addresses:
        for part in addresses:
            params['address'] = params['address'] + part.get_text()
        params['address'] = params['address'].replace('на карте','')
    else:
        params['address'] = 'не найдено'

    priceSpan = item.find('span', {'itemprop' : 'price'})
    if priceSpan:
        params['price'] = priceSpan.get_text()
    else:
        params['price'] = 'не найдено'

    priceDiv = item.find('div', {'data-name' : 'MarketPrice'})
    if priceDiv:
        params['priceMarket'] = priceDiv.get_text()
    else:
        params['priceMarket'] = ' '

    pBlock = item.find('p', {'itemprop':'description'})
    if pBlock:
        params['description'] = pBlock.get_text()
    else:
        params['description'] = ' '

    params['flatId'] = re.sub('[^0-9]+', '', link)

    phoneDiv = item.find(class_=re.compile("--phone--"))
    if phoneDiv:
        params['phone'] = phoneDiv.get_text() 

    divInfo = item.find('div', {'data-name':'GeneralInformation'})
    if divInfo:
        infoArr = divInfo.find_all('li', {'data-name':'AdditionalFeatureItem'})
        for infoItem in infoArr:
            name = infoItem.find(class_=re.compile("--name--")).get_text()
            value = infoItem.find(class_=re.compile("--value--")).get_text()
            try:
                params[btiVariables[name]] = value
            except:
                print('Параметр не найден',name)

    divInfo2 = item.find('div', {'data-name':'Description'})
    if divInfo2:
        info2Arr = divInfo2.find_all(class_=re.compile("--info--"))
        for info2Item in info2Arr:
            name = info2Item.find(class_=re.compile("--info-title--")).get_text()
            value = info2Item.find(class_=re.compile("--info-value--")).get_text()
            try:
                params[btiVariables[name]] = value
            except:
                print('Параметр не найден',name)

    divBtiInfo = item.find('div', {'data-name':'BtiHouseData'})
    if divBtiInfo:
        btiArr = divBtiInfo.find_all('div', {'data-name':'Item'})
        for btiItem in btiArr:
            name = btiItem.find(class_=re.compile("--name--")).get_text()
            value = btiItem.find(class_=re.compile("--value--")).get_text()
            try:
                params[btiVariables[name]] = value
            except:
                print('Параметр не найден',name)


#//if item

    data.append({
        'id': params['flatId'],
        'numberRooms': params['numberRooms'],       #
        'address': params['address'],               
        'phone': params['phone'],                   
        'areaRooms': params['areaRooms'],           #
        'cityPhone': params['cityPhone'],           #
        'nameZHK': params['nameZHK'],               #
        'plan': params['plan'],
        'type': params['flatType'],
        'area': params['area'],
        'livingArea': params['livingArea'],
        'kitchen': params['kitchen'],
        'home': params['home'],
        'year': params['year'],
        'year_pass': params['year_pass'],
        'avariya': params['avariya'],
        'podezdi': params['podezdi'],
        'heat': params['heat'],
        'gas': params['gas'],
        'perekritiya': params['perekritiya'],
        'floor': params['floor'],
        'parking': params['parking'],
        'price': params['price'],
        'priceMarket': params['priceMarket'],
        'description': params['description'],
        'repair': params['repair'],
        'balkon': params['balkon'],
        'window': params['window'],
        'toilet': params['toilet'],
        'homeSeries': params['homeSeries'],
        'Hceiling' : params['Hceiling'],
        'lift':  params['lift'],
        'garbage': params['garbage'],
        'otdelka': params['otdelka'],
        'link':  params['link'],
    })
    return data
# //get_content
 
def save_file(items, path):
    with open(path, 'w', newline='') as file: #,encoding='cp1251'
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['ИД','Количество комнат','Тип','Адрес','Площадь, м2','Жилая площадь, м2','Площадь кухни, м2','Планировка','Этаж','Дом','Год постройки','Год сдачи','Аварийность','Подъезды','Отопление','Газ','Перекрытия','Отделка','Парковка','Цена','Рыночная цена','Телефоны','Описание','Ремонт','Площадь комнат, м2','Балкон','Окна','Санузел','Есть телефон','Название ЖК','Серия дома','Высота потолков, м','Лифт','Мусоропровод','Ссылка на объявление'])
        for item in items:
            flatId = item['id'].encode('ansi', errors='ignore').decode('cp1251')
            numberRooms = item['numberRooms'].encode('ansi', errors='ignore').decode('cp1251')
            address = item['address'].encode('ansi', errors='ignore').decode('cp1251')
            phone = item['phone'].encode('ansi', errors='ignore').decode('cp1251')
            areaRooms = item['areaRooms'].encode('ansi', errors='ignore').decode('cp1251')
            cityPhone = item['cityPhone'].encode('ansi', errors='ignore').decode('cp1251')
            nameZHK = item['nameZHK'].encode('ansi', errors='ignore').decode('cp1251')
            plan = item['plan'].encode('ansi', errors='ignore').decode('cp1251')
            flatType = item['type'].encode('ansi', errors='ignore').decode('cp1251')
            area = item['area'].encode('ansi', errors='ignore').decode('cp1251')
            livingArea = item['livingArea'].encode('ansi', errors='ignore').decode('cp1251')
            kitchen = item['kitchen'].encode('ansi', errors='ignore').decode('cp1251')
            home = item['home'].encode('ansi', errors='ignore').decode('cp1251')
            year = item['year'].encode('ansi', errors='ignore').decode('cp1251')
            year_pass = item['year_pass'].encode('ansi', errors='ignore').decode('cp1251')
            avariya = item['avariya'].encode('ansi', errors='ignore').decode('cp1251')
            podezdi = item['podezdi'].encode('ansi', errors='ignore').decode('cp1251')
            heat = item['heat'].encode('ansi', errors='ignore').decode('cp1251')
            gas = item['gas'].encode('ansi', errors='ignore').decode('cp1251')
            perekritiya = item['perekritiya'].encode('ansi', errors='ignore').decode('cp1251')
            floor = item['floor'].encode('ansi', errors='ignore').decode('cp1251')
            parking = item['parking'].encode('ansi', errors='ignore').decode('cp1251')
            price = item['price'].encode('ansi', errors='ignore').decode('cp1251')
            priceMarket = item['priceMarket'].encode('ansi', errors='ignore').decode('cp1251')
            description = item['description'].encode('ansi', errors='ignore').decode('cp1251')
            repair = item['repair'].encode('ansi', errors='ignore').decode('cp1251')
            balkon = item['balkon'].encode('ansi', errors='ignore').decode('cp1251')
            window = item['window'].encode('ansi', errors='ignore').decode('cp1251')
            toilet = item['toilet'].encode('ansi', errors='ignore').decode('cp1251')
            homeSeries = item['homeSeries'].encode('ansi', errors='ignore').decode('cp1251')
            Hceiling = item['Hceiling'].encode('ansi', errors='ignore').decode('cp1251')
            lift = item['lift'].encode('ansi', errors='ignore').decode('cp1251')
            garbage = item['garbage'].encode('ansi', errors='ignore').decode('cp1251')
            otdelka = item['otdelka'].encode('ansi', errors='ignore').decode('cp1251')
            link  = item['link'].encode('ansi', errors='ignore').decode('cp1251')

            writer.writerow([flatId,numberRooms,flatType,address,area,livingArea,kitchen,plan,floor,home,year,year_pass,avariya,podezdi,heat,gas,perekritiya,otdelka,parking,price,priceMarket,phone,description,repair,areaRooms,balkon,window,toilet,cityPhone,nameZHK,homeSeries,Hceiling,lift,garbage,link])

# //save_file

def parse():
    LINKS_FILE = input(f"Введите названия CSV файла ({ config['DEFAULT']['LINKS_FILE'] }): ")

    if LINKS_FILE == '':
        LINKS_FILE = config['DEFAULT']['LINKS_FILE']

    LINKS_FILE += '.csv'
    
    LINKS_FILE = LINKS_FILE.strip();
    print('open: ',LINKS_FILE)

    if os.path.isfile(LINKS_FILE): 
        with open(LINKS_FILE, encoding='cp1251') as r_file:
            file_reader = csv.reader(r_file, delimiter = ";")
            cnt = 0
        
            for row in file_reader:
                cnt += 1
        
            print (f'Найдено {cnt} записей')
    else:
        input(f"Файл не найден. Нажмите Enter для завершения программы.")
        sys.exit("Файл не найден. Работа программы прекращена.")

    with open(LINKS_FILE, encoding='cp1251') as r_file:
        file_reader = csv.reader(r_file, delimiter = ";")
        count = 0

        for row in file_reader:
            count += 1 

            if count == 1:
                print(f'Найден столбец - {", ".join(row)}')
                continue

            # автосохранение каждые 100 записей
            if count % 100 == 0:  
                save_file(flats, 'list-tmp.csv')

            print(f'{row[0]} {count} / {cnt}')
            URL = row[0]
            # запускаем цикл парсинга на каждую страницу пагинации
            successful = False
            while not successful:    
                html = get_html(URL)
                addInfo = get_content(html.text,URL)
                if addInfo == 'captcha':
                    captcha(URL)
                    config_file = config.read('cian_config.ini')
                    HEADERS['cookie'] = config['DEFAULT']['COOKIES'];
                else:
                    successful = True
            else:
                if addInfo == '404':
                    print ('404')
                    count += 1  
                    continue
            flats.extend(addInfo)
               
        print(f'Всего Обработано {count} строк.')
        save_file(flats, config['DEFAULT']['FILE']+'.csv')
        os.startfile(config['DEFAULT']['FILE']+'.csv')
        cef.Shutdown()
    #//parse

def captcha(URL):
    check_versions()
    #sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    cef.Initialize()
    browser = cef.CreateBrowserSync(url=URL, window_title="Капча!")
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
                COOKIES = self.cookie_visitor.show_cookie()
                if COOKIES.find('anti_bot') > 0:
                    COOKIES = COOKIES.replace('%', '%%')
                    config['DEFAULT']['COOKIES'] = COOKIES
                    with open('cian_config.ini', 'w') as configfile:
                        config.write(configfile)
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