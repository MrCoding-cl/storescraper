import json
import re
from collections import defaultdict

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.flixmedia import flixmedia_video_urls
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, get_cf_session

from .ripley_chile_base_lg_assistant_keywords import keywords


class RipleyChileBase(Store):
    preferred_products_for_url_concurrency = 3

    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Television',
            'Tablet',
            'Refrigerator',
            'Printer',
            'Oven',
            'Stove',
            'DishWasher'
            'VacuumCleaner',
            'WashingMachine',
            'Cell',
            'Camera',
            'StereoSystem',
            'OpticalDiskPlayer',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'Projector',
            'VideoGameConsole',
            'Monitor',
            'AllInOne',
            'AirConditioner',
            'WaterHeater',
            'SolidStateDrive',
            'SpaceHeater',
            'Wearable',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        url_base = 'https://simple.ripley.cl/{}?page={}'

        category_paths = [
            ['tecno/computacion/notebooks', ['Notebook'],
             'Tecno > Computación > Notebooks', 1],
            # ['tecno/computacion/2-en-1convertibles', ['Notebook'],
            #  'Tecno > Cmoputación > 2 en 1/Convertibles', 1],
            ['tecno/computacion/notebooks-gamer', ['Notebook'],
             'Tecno > Computación > Notebooks gamer', 1],

            ['tecno/computacion/tablets-y-e-readers', ['Tablet'],
             'Tecno > Computación > Tablets y E-readers', 1],
            ['tecno/impresoras-y-tintas', ['Printer'],
             'Tecno > Computación > Impresoras y Tintas', 1],
            ['tecno/computacion/almacenamiento',
             ['UsbFlashDrive', 'ExternalStorageDevice'],
             'Tecno > Computación > Almacenamiento', 0.5],
            ['tecno/computacion/pc-all-in-one', ['AllInOne'],
             'Tecno > Computación > PC/All in one', 1],
            ['tecno/computacion/proyectores-y-monitores',
             ['Monitor', 'Projector'],
             'Tecno > Computación > Proyectores y monitores', 0.5],
            # ['computacion/computadores/notebooks-gamers', 'Notebook'],
            # ['mercado-ripley/gamer', 'Mouse'],

            ['tecno/television', ['Television'],
             'Tecno > Televisión', 1],
            ['tecno/television/smart-tv', ['Television'],
             'Tecno > Televisión > Smart TV', 1],
            # ['tecno/television/4k-uhd-nanocell', ['Television'],
            # 'Tecno > Televisión > 4K - UHD - NANOCELL', 1],
            # ['tecno/television/premium-oled-qled-8k', ['Television'],
            #  'Tecno > Televisión > PREMIUM - OLED - QLED - 8K', 1],
            # "['tecno/television/hd-full-hd', ['Television'],
            #  'Tecno > Televisión > HD - FULL HD', 1],

            ['electro/refrigeracion', ['Refrigerator'],
             'Electro > Refrigeración', 1],
            ['electro/refrigeracion/side-by-side', ['Refrigerator'],
             'Electro > Refrigeración > Side by Side', 1],
            ['electro/refrigeracion/refrigeradores', ['Refrigerator'],
             'Electro > Refrigeración > Refrigeradores', 1],
            ['electro/refrigeracion/freezers-y-congeladores', ['Refrigerator'],
             'Electro > Refrigeración > Freezers y congeladores', 1],
            ['electro/refrigeracion/frigobar', ['Refrigerator'],
             'Electro > Refrigeración > Frigobar', 1],
            ['electro/refrigeracion/door-in-door', ['Refrigerator'],
             'Electro > Refrigeración > Door in Door', 1],

            ['electro/cocina/cocinas', ['Stove'],
             'Electro > Cocina > Cocinas', 1],
            ['electro/cocina/microondas', ['Oven'],
             'Electro > Cocina > Microondas', 1],
            ['electro/cocina/hornos-y-microondas', ['Oven'],
             'Electro > Cocina > Hornos y Microondas', 1],
            # ['electro/cocina/hornos', ['Oven'],
            #  'Electro > Cocina > Hornos', 1],
            ['electro/cocina/lavavajillas', ['DishWasher'],
             'Electro > Cocina > Lavavajillas', 1],

            ['electro/aseo/aspiradoras-y-enceradoras', ['VacuumCleaner'],
             'Electro > Aseo > Aspiradoras y enceradoras', 1],

            ['electro/lavanderia', ['WashingMachine'],
             'Electro > Lavandería', 1],
            ['electro/lavanderia/lavadoras', ['WashingMachine'],
             'Electro > Lavandería > Lavadoras', 1],
            ['electro/lavanderia/secadoras', ['WashingMachine'],
             'Electro > Lavandería > Secadoras', 1],
            ['electro/lavanderia/lavadora-secadora', ['WashingMachine'],
             'Electro > Lavandería > Lavadora-secadora', 1],
            ['electro/lavanderia/doble-carga', ['WashingMachine'],
             'Electro > Lavandería > Doble carga', 1],

            # ['tecno/telefonia', ['Cell'],
            #  'Tecno > Telefonía', 1],
            ['tecno/telefonia/android', ['Cell'],
             'Tecno > Telefonía > Android', 1],
            ['tecno/telefonia/iphone', ['Cell'],
             'Tecno > Telefonía > iPhone', 1],
            ['tecno/telefonia/basicos', ['Cell'],
             'Tecno > Telefonía > Básicos', 1],

            ['tecno/fotografia-y-video/camaras-reflex', ['Camera'],
             'Tecno > Fotografía y Video > Camaras reflex', 1],
            ['tecno/fotografia-y-video/semi-profesionales', ['Camera'],
             'Tecno > Fotografía y Video > Semi profesionales', 1],
            # ['entretenimiento/fotografia/camaras-compactas', 'Camera'],

            ['tecno/audio-y-musica/equipos-de-musica', ['StereoSystem'],
             'Tecno > Audio y Música > Equipos de música', 1],
            ['tecno/audio-y-musica/parlantes-portables', ['StereoSystem'],
             'Tecno > Audio y Música > Parlantes Portables', 1],
            ['tecno/audio-y-musica/soundbar-y-home-theater', ['StereoSystem'],
             'Tecno > Audio y Música > Soundbar y Home theater', 1],
            # ['tecno/audio-y-musica/hi-fi', 'StereoSystem'],
            # ['tecno/audio-y-musica/parlantes-y-subwoofer', 'StereoSystem'],
            # ['tecno/audio-y-musica/microcomponentes', 'StereoSystem'],
            # ['tecno/audio-y-musica/home-cinema', 'StereoSystem'],

            ['tecno/television/bluray-dvd-y-tv-portatil',
             ['OpticalDiskPlayer'],
             'Tecno > Televisión > Bluray -DVD y TV Portátil', 1],

            # ['telefonia/accesorios-telefonia/4kmemorias', 'MemoryCard'],
            ['tecno/mundo-gamer/consolas', ['VideoGameConsole'],
             'Tecno > Mundo Gamer > Consolas', 1],

            ['electro/climatizacion/aire-acondicionado',
             ['AirConditioner'],
             'Electro > Climatización > Ventiladores y aire acondicionado', 1],
            ['electro/climatizacion/purificadores-y-humificadores',
             ['AirConditioner'],
             'Electro > Climatización > Purificadores y humidificadores', 1],
            ['electro/climatizacion/estufas-y-calefactores',
             ['SpaceHeater'],
             'Electro > Climatización > Estufas y calefactores', 1],
            ['tecno/corner-smartwatch', ['Wearable'],
             'Tecno > Telefonía > Smartwatches y Wearables', 1],
            ['tecno/especial-audifonos', ['Headphones'],
             'Tecno > Audio y Música > Audífonos', 1],
            # ['telefonia/smartwatches-and-wearables/smartwatch', 'Wearable'],
        ]

        session = get_cf_session(extra_args)
        product_entries = defaultdict(lambda: [])

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            page = 1
            current_position = 1

            while True:
                if page > 100:
                    raise Exception('Page overflow')

                category_url = url_base.format(category_path, page)
                print(category_url)
                response = session.get(category_url, allow_redirects=False)

                if response.status_code != 200 and page == 1:
                    raise Exception('Invalid section: ' + category_url)

                soup = BeautifulSoup(response.text, 'html.parser')
                product_link_container = soup.find(
                    'div', 'catalog-container')

                if not product_link_container:
                    if page == 1:
                        raise Exception('Empty category path: {} - {}'.format(
                            category, category_path))
                    else:
                        break

                product_link_containers = product_link_container.findAll(
                    'a', 'catalog-product-item')

                if not product_link_containers:
                    product_link_containers = product_link_container.findAll(
                        'a', 'ProductItem__Name')

                if not product_link_containers:
                    raise Exception('Category error: ' + category_path)

                for idx, link_tag in enumerate(product_link_containers):
                    product_url = 'https://simple.ripley.cl' + link_tag['href']
                    if cls.filter_url(product_url):
                        product_entries[product_url].append({
                            'category_weight': category_weight,
                            'section_name': section_name,
                            'value': current_position
                        })
                    current_position += 1

                page += 1

        return product_entries

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        return cls._products_for_url(url, category, extra_args)

    @classmethod
    def _products_for_url(cls, url, category=None, extra_args=None, retries=9):
        session = get_cf_session(extra_args)
        page_source = session.get(url).text

        soup = BeautifulSoup(page_source, 'html.parser')

        if soup.find('div', 'error-page'):
            return []

        product_data = re.search(r'window.__PRELOADED_STATE__ = (.+);',
                                 page_source)
        if not product_data:
            if retries:
                return cls._products_for_url(url, category, extra_args,
                                             retries=retries-1)
            else:
                return []
        product_json = json.loads(product_data.groups()[0])
        specs_json = product_json['product']['product']

        sku = specs_json['partNumber']
        name = specs_json['name']
        short_description = specs_json.get('shortDescription', '')

        # If it's a cell sold by Ripley directly (not Mercado Ripley) add the
        # "Prepago" information in its description
        if category in ['Cell', 'Unknown'] and 'MPM' not in sku:
            name += ' ({})'.format(short_description)

        if specs_json['isOutOfStock'] or specs_json['isUnavailable']:
            stock = 0
        else:
            stock = -1

        if 'offerPrice' in specs_json['prices']:
            normal_price = Decimal(specs_json['prices']['offerPrice'])
        elif 'listPrice' in specs_json['prices']:
            normal_price = Decimal(specs_json['prices']['listPrice'])
        else:
            return []

        offer_price = Decimal(specs_json['prices'].get('cardPrice',
                                                       normal_price))

        if offer_price > normal_price:
            offer_price = normal_price

        description = ''

        refurbished_notice = soup.find('div', 'emblemaReaccondicionados19')

        if refurbished_notice:
            description += html_to_markdown(str(refurbished_notice))

        if 'longDescription' in specs_json:
            description += html_to_markdown(specs_json['longDescription'])

        description += '\n\nAtributo | Valor\n-- | --\n'

        for attribute in specs_json['attributes']:
            if 'name' in attribute and 'value' in attribute:
                description += '{} | {}\n'.format(attribute['name'],
                                                  attribute['value'])

        description += '\n\n'
        condition = 'https://schema.org/NewCondition'

        if 'reacondicionado' in description.lower() or \
                'reacondicionado' in name.lower() or \
                'reacondicionado' in short_description.lower():
            condition = 'https://schema.org/RefurbishedCondition'

        if soup.find('img', {'src': '//home.ripley.cl/promo-badges/'
                                    'reacondicionado.png'}):
            condition = 'https://schema.org/RefurbishedCondition'

        picture_urls = []
        for path in specs_json['images']:
            picture_url = path

            if 'file://' in picture_url:
                continue

            if not picture_url.startswith('https'):
                picture_url = 'https:' + picture_url

            picture_urls.append(picture_url)

        if not picture_urls:
            picture_urls = None

        flixmedia_id = None
        video_urls = []

        flixmedia_urls = [
            '//media.flixfacts.com/js/loader.js',
            'https://media.flixfacts.com/js/loader.js'
        ]

        for flixmedia_url in flixmedia_urls:
            flixmedia_tag = soup.find(
                'script', {'src': flixmedia_url})
            if flixmedia_tag and flixmedia_tag.has_attr('data-flix-mpn'):
                flixmedia_id = flixmedia_tag['data-flix-mpn']
                video_urls = flixmedia_video_urls(flixmedia_id)
                break

        review_count = int(specs_json['powerReview']['fullReviews'])

        if review_count:
            review_avg_score = float(
                specs_json['powerReview']['averageRatingDecimal'])
        else:
            review_avg_score = None

        has_virtual_assistant = False

        for keyword in keywords:
            if keyword in url:
                has_virtual_assistant = True
                break

        if 'shopName' in specs_json['marketplace']:
            seller = specs_json['marketplace']['shopName']
        elif specs_json['isMarketplaceProduct']:
            seller = 'Mercado R'
        else:
            seller = None

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
            picture_urls=picture_urls,
            condition=condition,
            flixmedia_id=flixmedia_id,
            review_count=review_count,
            review_avg_score=review_avg_score,
            video_urls=video_urls,
            has_virtual_assistant=has_virtual_assistant,
            seller=seller
        )

        return [p]

    @classmethod
    def filter_url(cls, url):
        raise Exception('Subclasses of RipleyChileBase should implement this')
