import transliterate as tr
from mtarenda import request_url, bs, headers, urljoin
class Product:
    def __init__(self):
        pass
    img_path = ''
    img_downloaded = []
    caracteristics = {}
    category = ''
    url_category = ''

    '''self:
    product_name = ''
    url_product = ''
    img_product_path = def toEngName(product_name)
    price_smena'''
    # price_dostavka = ''
    # caracteristics.keys = param1,...
    # img_src = [] # list of relation url

class Category:
    def translit(self):
        self.translit_name = tr.translit(self.name.replace(' ', '_'), reversed = True).replace('\'','')

    def addition_urls_search(self):
        self.addition_urls = []
        request = request_url(self.category_urls[0], headers)
        if request.status_code == 200:
            soup = bs(request.content, 'lxml')
            div = soup.find('div', class_ = 'modern-page-navigation')
            if div:
                links = div.find_all('a')
                for link in links:
                    if link.text != 'След.':
                        self.category_urls.append(urljoin('https://www.mtarenda.ru', link['href']))

    pass

'''

dict = {
'category': 'Категория',
'price_smena': 'Цена за смену',
'price_dostavks': 'Цена за доставку',
'massa': 'Эксплуатационная масса, кг',
'power': 'Мощность двигателя, л.с.',
'clear_power': 'Полезная мощность двигателя, кВТ',
'max_length_strela': 'Максимальный вылет стрелы, м'
}
'''