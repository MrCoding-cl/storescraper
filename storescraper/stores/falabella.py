import json
import re
import time
import base64

from collections import defaultdict
from decimal import Decimal
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

from selenium.common.exceptions import NoSuchElementException

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy
from storescraper import banner_sections as bs
from storescraper.utils import HeadlessChrome


class Falabella(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 10

    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Television',
            'Tablet',
            'Refrigerator',
            'Printer',
            'Oven',
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
            'CellAccesory',
            'AllInOne',
            'AirConditioner',
            'Monitor',
            'WaterHeater',
            'SolidStateDrive',
            'Mouse',
            'SpaceHeater',
            'Keyboard',
            'KeyboardMouseCombo',
            'Wearable',
            'Headphones',
            'DishWasher'
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            ['cat70057', ['Notebook'],
             'Home > Computación-Notebooks', 1],
            ['cat5860031', ['Notebook'],
             'Home > Computación-Notebooks > Notebooks Tradicionales', 1],
            ['cat2028', ['Notebook'],
             'Home > Computación-Notebooks Gamers', 1],
            ['cat2450060', ['Notebook'],
             'Home > Computación-Notebooks > Notebooks Convertibles 2en1', 1],
            ['cat15880017', ['Notebook'],
             'Home > Especiales-Gamer', 1],
            ['cat5860030', ['Notebook'],
             'Home > Computación-Notebooks > MacBooks', 1],
            ['cat4850013', ['Notebook'],
             'Home > Computación-Computación Gamer', 1],
            ['cat1012', ['Television'],
             'Home > Tecnología-TV', 1],
            ['cat7190148', ['Television'],
             'Home > TV-Televisores LED', 1],
            # ['cat2850016', ['Television'],
            #  'Home > TV-Televisores OLED', 1],
            ['cat10020021', ['Television'],
             'Home > TV-Televisores QLED', 1],
            ['cat16430001', ['Television'],
             'Home > Tecnología-TELEVISORES LED HASTA 50"', 1],
            ['cat16440001', ['Television'],
             'Home > Tecnología-TELEVISORES LED ENTRE 55 Y 58"', 1],
            ['cat12910024', ['Television'],
             'Home > TV-Televisores LED Desde 65"', 1],
            ['cat18110002', ['Television'],
             'Home > Tecnología-Nueva Línea 2019', 1],
            ['cat18110001', ['Television'],
             'Home > Tecnología-Premium', 1],
            ['cat7230007', ['Tablet'],
             'Home > Computación-Tablets', 1],
            ['cat4074', ['Refrigerator'],
             'Home > Refrigeración-No Frost', 1],
            ['cat4091', ['Refrigerator'],
             'Home > Refrigeración-Side by Side', 1],
            ['cat4036', ['Refrigerator'],
             'Home > Refrigeración-Frío Directo', 1],
            ['cat4048', ['Refrigerator'],
             'Home > Refrigeración-Freezers', 1],
            ['cat4049', ['Refrigerator'],
             'Home > Refrigeración-Frigobar', 1],
            ['cat1840004', ['Refrigerator'],
             'Home > Refrigeración-Cavas', 1],
            ['cat1820006', ['Printer'],
             'Home > Computación-Impresión > Impresoras Multifuncionales', 1],
            # ['cat6680042/Impresoras-Tradicionales', 'Printer'],
            # ['cat11970007/Impresoras-Laser', 'Printer'],
            # ['cat11970009/Impresoras-Fotograficas', 'Printer'],
            ['cat3151', ['Oven'],
             'Home > Microondas', 1],
            ['cat3114', ['Oven'],
             'Home > Electrodomésticos Cocina- Electrodomésticos de cocina > '
             'Hornos Eléctricos', 1],
            ['cat3025', ['VacuumCleaner'],
             'Home > Electrohogar- Aspirado y Limpieza > Aspiradoras', 1],
            ['cat4060', ['WashingMachine'],
             'Home > Lavado-Lavadoras', 1],
            ['cat1700002', ['WashingMachine'],
             'Home > Lavado-Lavadoras-Secadoras', 1],
            ['cat4088', ['WashingMachine'],
             'Home > Lavado-Secadoras', 1],
            ['cat1280018', ['Cell'],
             'Home > Telefonía- Celulares y Teléfonos > Celulares Básicos', 1],
            ['cat720161', ['Cell'],
             'Home > Telefonía- Celulares y Teléfonos > Smartphones', 1],
            ['cat70028', ['Camera'],
             'Home > Fotografía-Cámaras Compactas', 1],
            ['cat70029', ['Camera'],
             'Home > Fotografía-Cámaras Semiprofesionales', 1],
            ['cat3091', ['StereoSystem'],
             'Home > Audio-Equipos de Música y Karaokes', 1],
            ['cat3171', ['StereoSystem'],
             'Home > Computación- Accesorios Tecnología > Accesorios Audio > '
             'Parlantes Bluetooth', 1],
            ['cat2045', ['StereoSystem'],
             'Home > Audio-Soundbar y Home Theater', 1],
            ['cat1130010', ['StereoSystem'],
             'Home > Audio- Hi-Fi > Tornamesas', 1],
            ['cat6260041', ['StereoSystem'],
             'Home > Día del Niño Chile- Tecnología > Audio > Karaoke', 1],
            ['cat2032', ['OpticalDiskPlayer'],
             'Home > TV-Blu Ray y DVD', 1],
            ['cat3087', ['ExternalStorageDrive'],
             'Home > Computación- Almacenamiento > Discos duros', 1],
            ['cat3177', ['UsbFlashDrive'],
             'Home > Computación- Almacenamiento > Pendrives', 1],
            ['cat70037', ['MemoryCard'],
             'Home > Computación- Accesorios Tecnología > '
             'Accesorios Fotografía > Tarjetas de Memoria', 1],
            ['cat2070', ['Projector'],
             'Home > TV-Proyectores', 1],
            ['cat3770004', ['VideoGameConsole'],
             'Home > Tecnología- Videojuegos > Consolas', 1],
            ['cat40051', ['AllInOne'],
             'Home > Computación-All In One', 1],
            ['cat7830015', ['AirConditioner'],
             'Home > Electrohogar- Aire Acondicionado > Portátiles', 1],
            ['cat7830014', ['AirConditioner'],
             'Home > Electrohogar- Aire Acondicionado >Split', 1],
            ['cat3197', ['AirConditioner'],
             'Home > Electrohogar- Aire Acondicionado > Purificadores', 1],
            ['cat2062', ['Monitor'],
             'Home > Computación-Monitores', 1],
            ['cat2013', ['WaterHeater'],
             'Home > Electrohogar- Aire Acondicionado > Calefont y Termos', 1],
            ['cat3155', ['Mouse'],
             'Home > Computación- Accesorios Tecnología > '
             'Accesorios Computación > Mouse', 1],
            ['cat9900007', ['SpaceHeater'],
             'Home > Electrohogar- Calefacción > Estufas Parafina Láser', 1],
            ['cat9910024', ['SpaceHeater'],
             'Home > Electrohogar- Calefacción > Estufas Gas', 1],
            ['cat9910006', ['SpaceHeater'],
             'Home > Electrohogar- Calefacción > Estufas Eléctricas', 1],
            ['cat9910027', ['SpaceHeater'],
             'Home > Electrohogar- Calefacción > Estufas Pellet y Leña', 1],
            ['cat4290063', ['Wearable'],
             'Home > Telefonía- Wearables > SmartWatch', 1],
            ['cat4730023', ['Keyboard'],
             'Home > Computación- Accesorios Tecnología > '
             'Accesorios Computación > Teclados > Teclados Gamers', 1],
            ['cat2370002', ['Keyboard'],
             'Home > Computación- Accesorios Tecnología > '
             'Accesorios Computación > Teclados', 1],
            ['cat2930003', ['Keyboard'],
             'Home > Computación- Accesorios Tecnología > Accesorios TV > '
             'Teclados Smart', 1],
            ['cat1640002', ['Headphones'],
             'Home > Computación- Accesorios Tecnología > Accesorios Audio > '
             'Audífonos', 1],
            ['cat4061', ['DishWasher'],
             'Home > Lavado-Lavavajillas', 1],
        ]

        session = session_with_proxy(extra_args)
        product_entries = defaultdict(lambda: [])

        for e in category_paths:
            category_id, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            category_product_urls = cls._get_product_urls(
                session, category_id)

            for idx, url in enumerate(category_product_urls):
                product_entries[url].append({
                    'category_weight': category_weight,
                    'section_name': section_name,
                    'value': idx + 1
                })

        return product_entries

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = session_with_proxy(extra_args)

        base_url = "https://www.falabella.com/falabella-cl/search?" \
                   "Ntt={}&page={}"

        discovered_urls = []
        page = 1
        while True:
            if page > 60:
                raise Exception('Page overflow ' + keyword)

            search_url = base_url.format(keyword, page)

            res = session.get(search_url, timeout=None)

            if res.status_code == 500:
                break

            soup = BeautifulSoup(res.text, 'html.parser')

            products_containers = soup.find_all('div', 'pod-4_GRID')

            for product_container in products_containers:
                product_url = 'https://www.falabella.com{}'.format(
                    product_container.find('a')['href'])
                discovered_urls.append(product_url)

                if len(discovered_urls) == threshold:
                    return discovered_urls
            page += 1

        return discovered_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        return cls._products_for_url(url, category=category,
                                     extra_args=extra_args)

    @classmethod
    def _get_product_urls(cls, session, category_id):
        discovered_urls = []
        base_url = 'https://www.falabella.com/s/browse/v1/listing/cl?' \
                   'zone=13&categoryId={}&page={}'
        page = 1

        while True:
            if page > 60:
                raise Exception('Page overflow: ' + category_id)

            pag_url = base_url.format(category_id, page)
            res = session.get(pag_url, timeout=None)
            res = json.loads(res.content.decode('utf-8'))['data']

            if 'results' not in res:
                if page == 1:
                    raise Exception('Empty category: {}'.format(category_id))
                break

            for result in res['results']:
                product_url = 'https://www.falabella.com{}'\
                    .format(result['url'])

                discovered_urls.append(product_url)

            page += 1

        return discovered_urls

    @classmethod
    def _products_for_url(cls, url, retries=5, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        content = session.get(url, timeout=30).text.replace('&#10;', '')

        soup = BeautifulSoup(content, 'html.parser')

        panels = ['fb-product-information__product-information-tab',
                  'fb-product-information__specification']

        description = ''
        video_urls = []

        for panel_class in panels:
            panel = soup.find('div', panel_class)
            if not panel:
                continue

            description += html_to_markdown(str(panel)) + '\n\n'
            for iframe in panel.findAll('iframe'):
                match = re.search(r'//www.youtube.com/embed/(.+)\?',
                                  iframe['src'])
                if match:
                    video_urls.append('https://www.youtube.com/watch?v={}'
                                      ''.format(match.groups()[0]))

        raw_json_data = re.search('var fbra_browseMainProductConfig = (.+);\r',
                                  content)

        if not raw_json_data:
            if retries:
                time.sleep(5)
                return cls._products_for_url(
                    url, retries=retries-1, category=category,
                    extra_args=extra_args)
            else:
                return []

        product_data = json.loads(raw_json_data.groups()[0])
        slug = product_data['state']['product']['displayName'].replace(
            ' ', '-')
        publication_id = product_data['state']['product']['id']
        global_id = product_data['state']['product']['id']
        media_asset_url = product_data['endPoints']['mediaAssetUrl']['path']
        pictures_resource_url = 'https://falabella.scene7.com/is/image/' \
                                'Falabella/{}?req=set,json'.format(global_id)
        pictures_response = session.get(pictures_resource_url, timeout=30).text
        pictures_json = json.loads(
            re.search(r's7jsonResponse\((.+),""\);',
                      pictures_response).groups()[0])

        picture_urls = []

        picture_entries = pictures_json['set']['item']
        if not isinstance(picture_entries, list):
            picture_entries = [picture_entries]

        for picture_entry in picture_entries:
            picture_url = 'https:{}{}?scl=1.0'.format(media_asset_url,
                                                      picture_entry['i']['n'])
            picture_urls.append(picture_url)

        brand = product_data['state']['product']['brand'] or 'Genérico'
        base_name = '{} {}'.format(
            brand, product_data['state']['product']['displayName'])

        products = []

        if 'skus' not in product_data['state']['product']:
            return []

        for model in product_data['state']['product']['skus']:
            if 'stockAvailable' not in model:
                continue

            sku = model['skuId']
            sku_url = 'https://www.falabella.com/falabella-cl/product/{}/{}/' \
                      '{}'.format(publication_id, slug, sku)

            prices = {e['type']: e for e in model['price']}

            if 3 in prices:
                normal_price_key = 3
            else:
                normal_price_key = 2

            lookup_field = 'originalPrice'
            if lookup_field not in prices[normal_price_key]:
                lookup_field = 'formattedLowestPrice'

            normal_price = Decimal(remove_words(
                prices[normal_price_key][lookup_field]))

            if 1 in prices:
                lookup_field = 'originalPrice'
                if lookup_field not in prices[1]:
                    lookup_field = 'formattedLowestPrice'
                offer_price = Decimal(
                    remove_words(prices[1][lookup_field]))
            else:
                offer_price = normal_price

            stock = model['stockAvailable']

            reviews_url = 'https://api.bazaarvoice.com/data/reviews.json?' \
                          'apiversion=5.4&passkey=mk9fosfh4vxv20y8u5pcbwipl&' \
                          'Filter=ProductId:{}&Include=Products&Stats=Reviews'\
                .format(sku)
            review_data = json.loads(session.get(reviews_url).text)
            review_count = review_data['TotalResults']

            review_stats = review_data['Includes']

            if 'Products' in review_stats:
                review_avg_score = review_stats['Products'][str(sku)][
                    'ReviewStatistics']['AverageOverallRating']
            else:
                review_avg_score = None

            if 'reacondicionado' in base_name.lower():
                condition = 'https://schema.org/RefurbishedCondition'
            else:
                condition = 'https://schema.org/NewCondition'

            p = Product(
                '{} ({})'.format(base_name, model['name']),
                cls.__name__,
                category,
                sku_url,
                url,
                sku,
                stock,
                normal_price,
                offer_price,
                'CLP',
                sku=sku,
                description=description,
                picture_urls=picture_urls,
                video_urls=video_urls,
                review_count=review_count,
                review_avg_score=review_avg_score,
                condition=condition
            )

            products.append(p)

        return products

    @classmethod
    def banners(cls, extra_args=None):
        base_url = 'https://www.falabella.com/falabella-cl/{}'

        sections_data = [
            [bs.HOME, 'Home', bs.SUBSECTION_TYPE_HOME, ''],
            # [LINEA_BLANCA_FALABELLA,
            # 'Electro y Tecnología-Línea Blanca',
            #  SUBSECTION_TYPE_CATEGORY_PAGE,
            #  'category/cat7090035/Linea-Blanca'],

            # # CATEGORY PAGES # #
            # Currently displaying a smart picker
            # [bs.REFRIGERATION, 'Refrigeradores',
            #  bs.SUBSECTION_TYPE_CATEGORY_PAGE,
            #  'category/cat3205/Refrigeradores'],
            # [bs.WASHING_MACHINES, 'Lavadoras',
            #  bs.SUBSECTION_TYPE_CATEGORY_PAGE,'category/cat3136/Lavadoras '],
            # [bs.TELEVISIONS, 'TV', bs.SUBSECTION_TYPE_CATEGORY_PAGE,
            #  'category/cat1012/TV '],
            # [bs.AUDIO, 'Audio', bs.SUBSECTION_TYPE_CATEGORY_PAGE,
            #  'category/cat2005/Audio'],
            # [bs.CELLS, 'Electro y Tecnología-Teléfonos',
            #  bs.SUBSECTION_TYPE_CATEGORY_PAGE, 'category/cat2018/Telefonos'],

            # # MOSAICS ##
            [bs.LINEA_BLANCA_FALABELLA, 'Electro y Tecnología-Línea Blanca',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat7090035/Linea-Blanca?isPLP=1'],
            [bs.REFRIGERATION, 'Refrigeradores-No Frost',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat4074/No-Frost'],
            [bs.REFRIGERATION, 'Refrigeradores-Side by Side',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat4091/Side-by-Side'],
            [bs.WASHING_MACHINES, 'Lavadoras', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat3136/Lavadoras '],
            [bs.WASHING_MACHINES, 'Lavadoras-Lavadoras',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat4060/Lavadoras'],
            [bs.WASHING_MACHINES, 'Lavadoras-Lavadoras-Secadoras',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat1700002/Lavadoras-Secadoras'],
            [bs.WASHING_MACHINES, 'Lavadoras-Secadoras',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat4088/Secadoras'],
            [bs.WASHING_MACHINES, ' Lavadoras-Lavadoras Doble Carga',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat11400002/Lavadoras-Doble-Carga'],
            [bs.TELEVISIONS, 'TV-LED', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat2850014/LED'],
            [bs.TELEVISIONS, 'TV-Smart TV', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat3040054/Smart-TV'],
            [bs.TELEVISIONS, 'TV-4K UHD', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat3990038/4K-UHD'],
            [bs.TELEVISIONS, 'TV-Televisores OLED', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat2850016/Televisores-OLED'],
            [bs.TELEVISIONS, 'TV', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat1012/TV?isPLP=1'],
            [bs.TELEVISIONS, 'TV-Pulgadas Altas',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat12910024/Televisores-LED-Desde-65"'],
            [bs.AUDIO, 'Audio-Soundbar y Home Theater',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat2045/Home-Theater'],
            [bs.AUDIO, 'Home Theater', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat3050040/Home-Theater'],
            [bs.AUDIO, 'Soundbar', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat1700004/Soundbar'],
            [bs.AUDIO, 'Minicomponente', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat70018/Minicomponente'],
            [bs.AUDIO, 'Audio-Equipos de Música y Karaokes',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat3091/?mkid=CA_P2_MIO1_024794'],
            [bs.AUDIO, 'Audio-Hi-Fi', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat3203/Hi-Fi'],
            [bs.AUDIO, 'Audio', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat2005/Audio?isPLP=1'],
            [bs.CELLS, 'Smartphones', bs.SUBSECTION_TYPE_MOSAIC,
             'category/cat720161/Smartphones'],
            [bs.CELLS, 'Electro y Tecnología-Teléfonos',
             bs.SUBSECTION_TYPE_MOSAIC, 'category/cat2018/Telefonos?isPLP=1'],
        ]

        session = session_with_proxy(extra_args)
        banners = []

        for section, subsection, subsection_type, url_suffix in sections_data:
            url = base_url.format(url_suffix)
            print(url)

            if subsection_type == bs.SUBSECTION_TYPE_HOME:
                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                slides = soup.findAll('div', 'fb-hero-carousel-slide')

                for index, slide in enumerate(slides):
                    picture_url = list(filter(None, slide.find(
                        'picture', 'fb-responsive-background').find(
                        'source')['srcset'].split(' ')))[2]
                    destination_urls = [a['href'] for a in slide.findAll('a')]
                    destination_urls = list(set(destination_urls))

                    banners.append({
                        'url': url,
                        'picture_url': picture_url,
                        'destination_urls': destination_urls,
                        'key': picture_url,
                        'position': index+1,
                        'section': section,
                        'subsection': subsection,
                        'type': subsection_type})

                # with HeadlessChrome(images_enabled=True) as driver:
                #     driver.set_window_size(1920, 1080)
                #     driver.get(url)
                #
                #     images = driver\
                #         .find_element_by_class_name('swiper-container')\
                #         .find_elements_by_class_name('dy_unit')[1:-1]
                #
                #     index = 1
                #
                #     for image in images:
                #         picture_array = image.find_element_by_tag_name(
                #             'picture').find_elements_by_tag_name('source')
                #         destination_urls = [
                #             d.get_property('href') for d in
                #             image.find_elements_by_tag_name('a')]
                #         destination_urls = list(set(destination_urls))
                #         for picture in picture_array:
                #             picture_url = picture.get_property(
                #                 'srcset').split(' ')[0]
                #
                #             if 'https://www.falabella.com' not in picture_url
                #                 picture_url = 'https://www.falabella.com' \
                #                               '{}'.format(picture_url)
                #
                #             if picture_url:
                #                 banners.append({
                #                     'url': url,
                #                     'picture_url': picture_url,
                #                     'destination_urls': destination_urls,
                #                     'key': picture_url,
                #                     'position': index,
                #                     'section': section,
                #                     'subsection': subsection,
                #                     'type': subsection_type
                #                 })
                #                 break
                #         else:
                #             raise Exception(
                #                 'No valid banners found for {} in position '
                #                 '{}'.format(url, index + 1))
                #         index += 1
            elif subsection_type == bs.SUBSECTION_TYPE_CATEGORY_PAGE:
                with HeadlessChrome(images_enabled=True) as driver:

                    driver.set_window_size(1920, 1080)
                    driver.get(url)

                    pictures = []

                    try:
                        elements = driver.find_element_by_class_name(
                            'fb-hero-carousel__pips')\
                            .find_elements_by_class_name(
                            'fb-hero-carousel__pips__pip')

                        for element in elements:
                            element.click()
                            time.sleep(2)
                            image = Image.open(
                                BytesIO(driver.get_screenshot_as_png()))
                            image = image.crop((0, 187, 1920, 769))
                            buffered = BytesIO()
                            image.save(buffered, format='PNG')
                            pictures.append(
                                base64.b64encode(buffered.getvalue()))
                    except NoSuchElementException:
                        image = Image.open(
                            BytesIO(driver.get_screenshot_as_png()))
                        image = image.crop((0, 187, 1920, 769))
                        buffered = BytesIO()
                        image.save(buffered, format='PNG')
                        pictures.append(base64.b64encode(buffered.getvalue()))

                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    images_div = soup.findAll('div', 'fb-hero-carousel-slide')
                    images_article = soup.findAll('article',
                                                  'fb-hero-carousel-slide')
                    images_module = soup.findAll('div',
                                                 'hero fb-module-wrapper')

                    images = images_div + images_article + images_module

                    assert len(images) == len(pictures)

                    for index, image in enumerate(images):
                        picture_array = image.findAll('picture')[-1].findAll(
                            'source')
                        destination_urls = [d['href'] for d in
                                            image.findAll('a')]
                        destination_urls = list(set(destination_urls))

                        for picture in picture_array:
                            key = picture['srcset'].split(' ')[0]
                            if 'webp' not in key:
                                banners.append({
                                    'url': url,
                                    'picture': pictures[index],
                                    'destination_urls': destination_urls,
                                    'key': 'https:{}'.format(key),
                                    'position': index + 1,
                                    'section': section,
                                    'subsection': subsection,
                                    'type': subsection_type
                                })
                                break
                        else:
                            raise Exception(
                                'No valid banners found for {} in position '
                                '{}'.format(url, index + 1))

            elif subsection_type == bs.SUBSECTION_TYPE_MOSAIC:
                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                image_container = soup.find(
                    'div', {'data-module': 'editorial'})

                if not image_container or not image_container.find('source'):
                    continue

                picture_url = image_container.find('source')['srcset']

                if '//' not in picture_url:
                    picture_url = 'https://www.falabella.com{}'.format(
                        picture_url)

                elif 'https:' not in picture_url:
                    picture_url = 'https:{}'.format(picture_url)

                destination_urls = [image_container.find('a')['href']]

                banners.append({
                    'url': url,
                    'picture_url': picture_url,
                    'destination_urls': destination_urls,
                    'key': picture_url,
                    'position': 1,
                    'section': section,
                    'subsection': subsection,
                    'type': subsection_type})

        return banners
