import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import POWER_SUPPLY, COMPUTER_CASE, MOTHERBOARD, \
    CPU_COOLER, HEADPHONES, MOUSE, STEREO_SYSTEM
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class JeanfigPc(Store):
    @classmethod
    def categories(cls):
        return [
            POWER_SUPPLY,
            COMPUTER_CASE,
            MOTHERBOARD,
            CPU_COOLER,
            HEADPHONES,
            MOUSE,
            STEREO_SYSTEM
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['componentes/fuentes-de-poder', POWER_SUPPLY],
            ['componentes/gabinetes', COMPUTER_CASE],
            ['componentes/placas-madres', MOTHERBOARD],
            ['componentes/ventiladores', CPU_COOLER],
            ['perifericos/audifonos', HEADPHONES],
            ['perifericos/mouse', MOUSE],
            ['perifericos/parlantes-pc', STEREO_SYSTEM]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://jeanfigpc.cl/categoria-producto/{}/' \
                              'page/{}/'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.find('div', 'row list-product-row')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers. \
                        findAll('div', 'product-container'):
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_title').text
        sku = soup.find('link', {'rel': 'shortlink'})['href'].split('p=')[-1]
        if soup.find('p', 'stock out-of-stock'):
            stock = 0
        else:
            stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        if soup.find('p', 'price').find('ins'):
            normal_price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            normal_price = Decimal(remove_words(soup.find('p', 'price').text))
        offer_price = Decimal(
            remove_words(soup.find('span', 'woocommerce-Price-amount').text))
        picture_urls = [tag['src'] for tag in soup.find(
            'div', 'woocommerce-product-gallery').findAll('img')]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
