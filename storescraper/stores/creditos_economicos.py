import json
import urllib
import re

from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy
from storescraper.categories import STOVE, WASHING_MACHINE, REFRIGERATOR, \
    OVEN, STEREO_SYSTEM, CELL, TELEVISION, AIR_CONDITIONER


class CreditosEconomicos(Store):
    @classmethod
    def categories(cls):
        return [
            STOVE,
            WASHING_MACHINE,
            REFRIGERATOR,
            OVEN,
            STEREO_SYSTEM,
            CELL,
            TELEVISION,
            AIR_CONDITIONER
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['C:/1/96/97/', TELEVISION],
            ['C:/1/2/', STEREO_SYSTEM],
            ['C:/105/109/', CELL],
            ['C:/8/17/', REFRIGERATOR],
            ['C:/8/18/', AIR_CONDITIONER],
            ['C:/8/15/', OVEN],
            # Hornos y microondas
            ['C:/8/11/32/', OVEN],
            ['C:/8/16/', WASHING_MACHINE],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1

            while True:
                if page > 30:
                    raise Exception('Page overflow')

                url = 'https://www.creditoseconomicos.com/buscapagina?' \
                      'fq={}&PS=40&sl=cc521686-accb-412a-a2eb-16f6beb3ca11&' \
                      'cc=4&sm=0&PageNumber={}'.format(
                       urllib.parse.quote_plus(category_path), page)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                products = soup.findAll('a')

                if not products:
                    if page == 1:
                        raise Exception('Empty url {}'.format(url))
                    else:
                        break

                for product in products:
                    product_url = product['href']
                    if product_url == '#':
                        continue
                    if product.find('div', 'brand-name').text != 'LG':
                        continue

                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        scripts = soup.findAll('script')
        product_data = [s for s in scripts if 'var skuJson' in s.text]

        if product_data:
            product_data = product_data[0].text
        else:
            raise Exception('No Data')

        product_json = json.loads(re.search(
            r'var skuJson_0 = ([\S\s]+?);', product_data).groups()[0])

        name = product_json['name']
        sku = str(product_json['skus'][0]['sku'])
        stock = 0
        if product_json['available']:
            stock = -1

        tax = Decimal('1.12')
        price = Decimal(product_json['skus'][0]['bestPrice']/100)*tax

        picture_urls = [
            a['zoom'] for a in soup.findAll('a', {'id': 'botaoZoom'})]

        description = html_to_markdown(
            str(soup.find('div', 'product-description')))

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'USD',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]
