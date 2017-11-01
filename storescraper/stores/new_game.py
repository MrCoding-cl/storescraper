import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class NewGame(Store):
    @classmethod
    def categories(cls):
        return [
            'Mouse',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['accion=hijo&plt=pc&cat=14', 'Mouse'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = 'http://www.newgame.cl/index.php?' + category_path
            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            product_cells = soup.findAll('a', 'juego')

            for product_cell in product_cells:
                product_url = 'http://www.newgame.cl/' + product_cell['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('div', 'detalle-nombre').text.strip()

        sku = urllib.parse.parse_qs(
            urllib.parse.urlparse(url).query)['type'][0]

        stock_url = 'http://www.newgame.cl/agregarcarro.php?value=' + sku
        stock_text = session.get(stock_url).text.split('|')[0]

        if stock_text in ['STOCK', 'STOCKTEMP']:
            stock = 0
        else:
            stock = int(stock_text)

        offer_price = soup.findAll('div', 'preciobig')[1].find('span')
        offer_price = Decimal(remove_words(offer_price.text))

        normal_price = soup.findAll('div', 'preciobig')[0].find('span')
        normal_price = Decimal(remove_words(normal_price.text))

        description = html_to_markdown(
            str(soup.find('div', 'contenido-juego')))

        picture_urls = [tag['src'] for tag in
                        soup.find('div', 'nivoSlider').findAll('img')]

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]