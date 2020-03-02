# coding=utf-8
from bs4 import BeautifulSoup as bs
import bs4
import time
import requests, pickle, shelve, re
from urllib.parse import urljoin
from product import *
import transliterate as tr
import os, sys, resource
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.webdriver import FirefoxProfile
import platform
import subprocess

# google_search = 'https://images.google.com/?q=%s'
# MacOS
# chrome_path = 'open -a /Applications/Google\ Chrome.app %s'
# Windows
# chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'
# Linux
# chrome_path = '/usr/bin/google-chrome --no-sandbox %s'
sys.setrecursionlimit(15000)

content_live = 86400
headers = {
    'accept': '*/*',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
base_url = 'https://mtarenda.ru/catalog/'
root = 'https://mtarenda.ru'
tractor_url = 'https://mtarenda.ru/catalog/arenda-traktora/'
path_img = 'images'

categories = [
    'Аренда трактора',
    'Гусеничные экскаваторы',
    'Колесные экскаваторы',
    'Экскаваторы погрузчики',
    'Экскаваторы планировщики',
    'Экскаваторы-разрушители',
    'Фронтальные погрузчики',
    'Погрузчики вилочные',
    'Погрузчики телескопические',
    'Автовышки',
    'Автокраны',
    'Самосвалы',
    'Манипуляторы',
    'Длинномеры',
    'Катки',
    'Низкорамные тралы',
    ]

cat_dict = {}
prod_list = {}
# prod_urls = []
img_urls = []
imgs_path = {}
prod_id = ''
full_comments = {}

#for dir open
def open_file(path):    # for dir open
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

# get content, return content.bs4
def request_url(base_url, headers):
    session = requests.Session()
    session.cookies.clear()
    return session.get(base_url, headers=headers)

# cat_dict - описание категории + url's
def categories_parse(base_url, headers):
    '''Парсит сайт на предмент urls категорий, имени категории ,  и транслит категории
    Все помещается в список cat_list
    initiates dictionary cat_list and shelve it in db['catset']
    '''
    request = request_url(base_url, headers)
    if request.status_code == 200:
        soup = bs(request.content, 'lxml')
        lis = soup.find_all('li', class_='catalog-left-menu-item')
        for li in lis:
            # print(urljoin('https://www.mtarenda',li.a['href']), li.a.text.strip(), tr.translit(li.a.text.strip().replace(' ','_'), reversed = True))
            if li.a.text.strip() in categories:
                cat = Category()
                cat.category_urls = [urljoin('https://www.mtarenda.ru', li.a['href'])]
                cat.addition_urls_search()
                # print(cat.category_urls)
                cat.name = li.a.text.strip()
                cat.translit()
                cat_dict[cat.translit_name] = cat
                print(cat.name, cat.translit_name, cat.category_urls)
        cat = Category()
        cat.category_urls = ['https://mtarenda.ru/catalog/arenda-traktora/']
        cat.addition_urls_search()
        cat.name = 'Аренда трактора'
        cat.translit()
        cat_dict[cat.translit_name] = cat
        print('End categories_parse()')
        db['catsep'] = {}
        db['catsep'] = cat_dict
    else:
        print('ERROR')

# загрузить содержимое в обьект Category(), может быть несколько страниц
def category_content_download():
    # cat_dict = db['catsep']
    for key in cat_dict.keys():
        cat = cat_dict[key]
        if round(time.time() - getattr(cat, 'time', 0)) < content_live: continue  #print('Cash already up to date'); continue
        count = 0
        cat.content = []
        for url in cat.category_urls:
            content = request_url(url, headers)
            if content.status_code == 200:
                print(count, key, url)
                cat.content.append(content.content)
                # print('content_context', cat.content[0])
            else:
                print('error getting content', content.status_code, url)
        cat.time = time.time()
        print(len(cat.content))
        cat_dict[key] = cat
    db['catsep'] = {}
    db['catsep'] = cat_dict

# Зарактеристики продукта , добавить в prod_list = {}
def product_parse(content, cat):
    soup = bs(content, 'lxml')
    divs = soup.find_all('div', class_='row catalog-item')
    # print(len(divs))
    for div in divs:
        name = div.find_all('a')[1].text
        translit_name = tr.translit(name, reversed=True).replace(' ', '_').replace('\'', '')
        # if translit_name in prod_list.keys():
        #     if round(time.time() - prod_list[translit_name].time) < content_live:
        #         continue
        prod = Product()
        prod.url = urljoin(root, div.a['href'])
        prod.img_url = urljoin(root, div.img['src'])
        prod.category_name = cat.name
        prod.category_translitname = cat.translit_name
        prod.name = name
        prod.translit_name = translit_name
        # characteristics of product
        spans = div.find_all('span', class_='amount')
        prod.comment = prod_comment(prod.url, prod.translit_name)
        prod.shift = spans[0].text
        prod.shipping = spans[1].text
        lis = div.find_all('li', class_='specifications-item')
        characteristics = {}
        cnt = 0
        for li in lis:
            spans = li.find_all('span')
            characteristics[cnt] = [spans[0].text, spans[1].text]
            cnt += 1
        prod.characteristics = characteristics
        # prod.time = time.time()
        prod.img = save_img(prod.img_url, cat, prod)
        prod_list[prod.translit_name] = prod
        imgs_path[prod.translit_name] = prod.img
        # for k in prod.__dict__.keys():
        #     print(k, getattr(prod, k))
        # print(list(prod.__dict__.keys()))
        # db['prod'] = prod
        # for prod in prod_list:
        #     repr(prod)
        # print(prod_list)
        db['imgs_path'] = {}
        db['imgs_path'] = imgs_path
        db['prod_list'] = {}
        db['prod_list'] = prod_list

# Описание к продукту, костыль , т.к. из начально парсил со страницы категории , а не со страницы
def prod_comment(url, translit_name):
    content = request_url(url, headers)
    if content.status_code == 200:
        soup = bs(content.content, 'lxml')
        div = soup.find('div', class_ = ['row element-description-row preview-descr', 'row element-description-row'])
        # print(dir(div))
        full_comment = ''
        if div:
            for i in range(1, len(div.contents[1])):
                # print(div.next)
                elem = div.contents[1].contents[i]
                if isinstance(elem, bs4.element.NavigableString): continue
                # print(type(elem), str(elem).replace('МосТрансАренда', 'А Строй').strip(), 'type --- elem')
                if isinstance(elem, (bs4.element.Tag,)):
                    elem_str = str(elem).strip().replace(' \n','')
                    if  elem_str == '<h2>Контакты</h2>' or elem_str == '<h2>Контактные данные</h2>': break
                    else:
                        full_comment += elem_str.replace('МосТрансАренда', 'А Строй')
            print(full_comment, '---- full_comment')
            full_comments[translit_name] = full_comment
            db['full_comments'] = {}
            db['full_comments'] = full_comments
        else:
            print('if div- NoneObj', type(div))
            # print(type(elem.find_all_next()),elem.find_next())
            # print(type(elem.find_next()), elem.find_next(),'----elem', div.find_next(), '---- div')
            # comment = elem.find(text='Контакты')
            # if str(comment) == 'Контакты':
            #     print(str(comment), '---- founds contacts')
            #     break

            # print(elem, '--- i perebor')
            # print(elem.name, '------ name')
            # break
        # div = soup.find('div', class_ = 'row element-description-row preview-descr')
        # if div:
        #     p = div.find('p')
        #     comment = p.text.strip()
        #     print(comment.replace('МосТрансАренда', 'А Строй'))
        #     return comment.replace('МосТрансАренда', 'А Строй')
        # else:
        #     return ''

def save_img(url, cat, prod):
    relative_path = '..' + '/' + path_img + '/' + cat.translit_name + '/' + prod.translit_name
    path = '/home/aloha/mtarenda/' + path_img + '/' + cat.translit_name + '/' + prod.translit_name
    img_file = path + '/' + prod.translit_name + '.' + url.split('.')[-1]
    prod.relative_path = relative_path
    if not os.path.exists(path):
        print(path, 'not exists FUCK')
        os.makedirs(path, exist_ok=True)

    if url not in img_urls:
        r = requests.get(url)
    else:
        # print('already downloaded')
        return img_file

    if r.status_code == 200:
        # print('new download')
        img = r.content
        img_urls.append(url)
        with open(img_file, 'wb') as f:
            f.write(img)
        db['img_urls'] = img_urls
        return img_file

def set_id():
    cnt = 0
    for prod in prod_list:
        prod.id = cnt
        cnt += 1

def update_db_cat():
    categories_parse(base_url, headers)
    d = {}
    for cat in cat_list:
        # if cat.translit_name not in list(db.keys()):
        print(cat.name, 'from db')
        d[cat.translit_name] = cat
    db['catsep'] = d

# csv segment
def csv_row_build(cat,prod):
    '''
    :param cat: Object of type Category()
    :param prod:  Object of type Product()
    :return: csv string for inserting in csv file
    :prod_id: id - uniq , autoincrement
    prod_id&1&prod.name&cat.name;Аренда спецтехники&prod.shift.replace(' ','')&&&0&&0&&&prod.shipping&&&&&&&&&&&100&&both&&&&&full_comments[prod.translit_name]&&&&&&&&
    '''
    img_string = ''
    characteristic = ''
    characteristics_string = ''
    img_path = '/home/s/ss992mhb/back/public_html/import/'

    result_string = ''

    list_images = os.listdir(prod.relative_path)
    print(list_images)
    for img in list_images:
        if os.path.isfile(img):
            img_string = img_path + cat.translit_name + '/' + prod.translit_name + '/' + img + ';'
            result_string += img_string
    print(result_string)
    for c in prod.characteristics:
        characteristics_string += c[0] + ':' + c[1]
    print(characteristics_string)



if __name__ == '__main__':
    db = shelve.open('mydb', 'w')
    # db.clear()
    # db.
    if not db.get('catsep') or not db.get('img_urls') or not db.get('imgs_path') or not db.get('prod_list') or not db.get('full_comments'):
        print(list(db.keys()))
        print(len(db.get('catsep')), len(db.get('img_urls')), len(db.get('imgs_path')), len(db.get('prod_list')))
        print('no data')
        categories_parse(base_url, headers)
        category_content_download()
        # for key in cat_dict.keys():
        #     print(cat_dict[key].category_urls)
        print('End if not db.get()')
    else:
        cat_dict = db['catsep']
        img_urls = db['img_urls']
        imgs_path = db['imgs_path']
        prod_list = db['prod_list']
        full_comments = db['full_comments']
        print(list(cat_dict.keys()))
        print('have data')
        print('End else section')




    # update_db_cat()

    # category_content_download()

    #
    for key in cat_dict.keys():
        cat = cat_dict[key]
        for content in cat_dict[key].content:
            product_parse(content, cat_dict[key])

    set_id()

    for key in prod_list.keys():
        prod = prod_list[key]
        csv_row_build(cat_dict[prod.category_translitname],prod)
    # print(prod_list,'\n', imgs_path,'\n', img_urls)
    #---------------- FULL COMMENTS
    # cnt = 0
    # for k in prod_list.keys():
    #     prod = prod_list[k]
    #     print(prod.name, prod.comment)
    #     print(len(prod_list))
    #     print('/'.join(imgs_path[prod.translit_name].split('/')[:-1]))
    #     # open_file('/'.join(imgs_path[prod.translit_name].split('/')[:-1]))
    #     # open_file(prod.relative_path)
    #     print(prod.relative_path, '-----begin comment')
    #     print(cnt , '------------- product NUMBER')
    #     cnt += 1
    #     prod_comment(prod.url, prod.translit_name)
        #--------------------------   FIREFOX START SEARCH GOOGLE IMAGE
        # ffp = FirefoxProfile('/home/aloha/.mozilla/firefox')
        # driver = webdriver.Firefox()
        # search = prod.name.replace(' ','+')
        # driver.get("https://www.google.com.sg/search?q=%s" % search + "&espv=2&biw=1920&bih=989&site=webhp&source=lnms&tbm=isch&sa=X&ei=ApZZVdrQJcqWuATcz4K4Cw&sqi=2&ved=0CAcQ_AUoAg")
        # break
    # ------------- CHECK FULL COMMENTS  ----------- ALL OK
    # cnt = 0
    # for k in full_comments.keys():
    #     print(len(full_comments[k]), '--------', cnt)
    #     cnt += 1
    # -------------------------------------------

    db.close()

# 1. открыть категорию -> сохранить в обьект категории контент в список , если несколько страниц
# 2. Добавить в список visited + timestamp
