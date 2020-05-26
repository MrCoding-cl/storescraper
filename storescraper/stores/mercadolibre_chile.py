import html
import json
import demjson
import re
from decimal import Decimal

import requests
from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown


class MercadolibreChile(Store):
    store_extension = ''

    @classmethod
    def categories(cls):
        category_paths = cls._category_paths()
        return list(set(e[1] for e in category_paths))

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_sections = cls._category_paths()

        session = requests.Session()
        product_urls = []

        for category_path, local_category in category_sections:
            if local_category != category:
                continue

            category_url = 'https://listado.mercadolibre.cl/{}/' \
                           '{}'.format(category_path, cls.store_extension)
            print(category_url)
            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            if soup.find('div', 'zrp-offical-message'):
                raise Exception('Invalid category: ' + category_url)

            containers = soup.findAll('li', 'results-item')

            if not containers:
                raise Exception('Empty category: ' + category_url)

            for container in containers:
                product_url = container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = requests.Session()
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        products = []

        name = soup.find('meta', {'name': 'twitter:title'})['content'].strip()
        description = html_to_markdown(
            str(soup.find('section', 'item-description')))

        variations = re.search(r'meli.Variations\(\{([\S\s]+?)}\);',
                               page_source)

        if not variations:
            pictures_data = json.loads(html.unescape(
                soup.find('div', 'gallery-content')['data-full-images']))
            picture_urls = [e['src'] for e in pictures_data]
            pricing_str = re.search(
                r'dataLayer = ([\S\s]+?);', page_source).groups()[0]
            pricing_data = json.loads(pricing_str)[0]
            sku = pricing_data['itemId']
            price = Decimal(pricing_data['localItemPrice'])
            stock = pricing_data['availableStock']

            products.append(Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                sku,
                stock,
                price,
                price,
                'CLP',
                sku=sku,
                description=description,
                picture_urls=picture_urls
            ))

        else:
            variations_str = variations.groups()[0]
            variations_data = demjson.decode("{"+variations_str+"}")['model']

            for variation in variations_data:
                key = str(variation['id'])
                sku = soup.find('input', {'name': 'itemId'})['value']
                v_suffix = variation[
                    'attribute_combinations'][0]['value_name']
                v_name = name + "({})".format(v_suffix)
                v_url = url.split('?')[0] + "?variation={}".format(key)
                price = Decimal(variation['price'])
                stock = variation['available_quantity']
                picture_url_base = 'https://mlc-s2-p.mlstatic.com/{}-F.jpg'
                picture_urls = [picture_url_base.format(p_id)
                                for p_id in variation['picture_ids']]

                products.append(Product(
                    v_name,
                    cls.__name__,
                    category,
                    v_url,
                    url,
                    key,
                    stock,
                    price,
                    price,
                    'CLP',
                    sku=sku,
                    description=description,
                    picture_urls=picture_urls
                ))

        return products

    @classmethod
    def _category_paths(cls):
        raise NotImplementedError('Subclasses must implement this')