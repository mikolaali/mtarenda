from bs4 import BeautifulSoup as bs
import time
import requests, pickle, shelve
from urllib.parse import urljoin
from product import *
import transliterate as tr
import transliterate as tr

content_live = 86400
headers = {'accept': '*/*', 'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
base_url = 'https://mtarenda.ru/catalog/'
root = 'https://mtarenda.ru'
tractor_url = 'https://mtarenda.ru/catalog/arenda-traktora/'
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
cat_list = []

def request_url(base_url, headers):
    session = requests.Session()
    session.cookies.clear()
    return session.get(base_url, headers = headers)

def mt_parse_categories(base_url, headers) -> None:
    '''Парсит сайт на предмент urls категорий, имени категории ,  и транслит категории
    Все помещается в список cat_list'''
    request = request_url(base_url, headers)
    if request.status_code == 200:
        soup = bs(request.content, 'lxml')
        lis = soup.find_all('li', class_ = 'catalog-left-menu-item')
        for li in lis:
            # print(urljoin('https://www.mtarenda',li.a['href']), li.a.text.strip(), tr.translit(li.a.text.strip().replace(' ','_'), reversed = True))
            if li.a.text.strip() in categories:
                cat = Category()
                cat.category_urls = [ urljoin('https://www.mtarenda.ru', li.a['href']) ]
                cat.addition_urls_search()
                print(cat.category_urls)
                cat.name = li.a.text.strip()
                cat.translit()
                cat_list.append(cat)
                print(cat.name, cat.translit_name, cat.category_urls)
        cat = Category()
        cat.category_urls = [ 'https://mtarenda.ru/catalog/arenda-traktora/' ]
        cat.addition_urls_search()
        cat.name = 'Аренда трактора'
        cat.translit()
        cat_list.append(cat)
    else:
        print('ERROR')

def mt_parse_product(url, headers):
    session = requests.Session()
    request = session.get(url, headers = headers)
    if request.status_codej == 200:
        soup = bs(request.content, 'lxml')

def update_db_cat():
    mt_parse_categories(base_url, headers)
    d = {}
    for cat in cat_list:
        # if cat.translit_name not in list(db.keys()):
        print(cat.name, 'from db')
        d[cat.translit_name] = cat
    db['catsep'] = d

def category_content_download():
    cat_dict = db['catsep']
    for key in cat_dict.keys():
        cat = cat_dict[key]
        if round(time.time() - getattr(cat, 'time', 0)) < content_live: print('Cach already up to date'); continue
        count = 0
        cat.content = []
        for url in cat.category_urls:
            content = request_url(url, headers)
            if content.status_code == 200:
                print(count, key, url)
                cat.content.append(content.content)
        cat.time = time.time()
        print(len(cat.content))
        cat_dict[key] = cat
    db['catsep'] = cat_dict

if __name__ == '__main__':
    db = shelve.open('mydb','w')
    # db.clear()
    # db.
    if not db.get('categories'):
        print('no data')
        mt_parse_categories(base_url, headers)
        db['categories'] = cat_list
        for cat in cat_list:
            print(cat.category_urls)
    else:
        cat_list = db['categories']
        cat_sep = db['catsep']
        print(list(cat_sep.keys()))
        print('have data')

    # update_db_cat()
    category_content_download()
    print(list(db.keys()))

    for key in cat_sep.keys():
        for content in cat_sep[key].content:
            soup = bs(content, 'lxml')
            divs = soup.find_all('div', class_ = 'row catalog-item')
            print(len(divs))
            for div in divs:
                print(urljoin(root, div.a['href']), div.img['src'], key)
                print(div.a['href'].split('/')[-2], div.img['src'].split('/')[-1],\
                      tr.translit(div.find_all('a')[1].text, reversed=True).replace(' ','_'))
                # print((div))
            break
        break

    db.close()

# 1. открыть категорию -> сохранить в обьект категории контент в список , если несколько страниц
# 2. Добавить в список visited + timestamp