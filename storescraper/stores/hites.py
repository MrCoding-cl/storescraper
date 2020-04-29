import json
import time
from collections import defaultdict

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.flixmedia import flixmedia_video_urls
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy,\
    HeadlessChrome
from storescraper import banner_sections as bs


class Hites(Store):
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
            'VacuumCleaner',
            'WashingMachine',
            'Cell',
            'Camera',
            'StereoSystem',
            'OpticalDiskPlayer',
            'VideoGameConsole',
            'AllInOne',
            'SpaceHeater',
            'CellAccesory',
            'Keyboard',
            'KeyboardMouseCombo',
            'Mouse',
            'Headphones',
            'ExternalStorageDrive',
            'Monitor',
            'Projector',
            'AirConditioner',
            'WaterHeater',
            'UsbFlashDrive',
            'Wearable',
            'DishWasher',
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            ['electro-hogar/refrigeradores', ['Refrigerator'],
             'Inicio > Electro Hogar > Refrigeradores', 1],
            ['electro-hogar/refrigeradores/frio-directo', ['Refrigerator'],
             'Inicio > Electro Hogar > Refrigeradores > Frío Directo', 1],
            ['electro-hogar/refrigeradores/no-frost', ['Refrigerator'],
             'Inicio > Electro Hogar > Refrigeradores > No Frost', 1],
            ['electro-hogar/refrigeradores/side-by-side', ['Refrigerator'],
             'Inicio > Electro Hogar > Refrigeradores > Side by Side', 1],
            ['electro-hogar/refrigeradores/freezers-y-frigobar',
             ['Refrigerator'],
             'Inicio > Electro Hogar > Refrigeradores > Freezers y Frigobar',
             1],

            ['electro-hogar/lavado-y-secado', ['WashingMachine', 'DishWasher'],
             'Inicio > Electro Hogar > Lavado y Secado', 0.5],
            ['electro-hogar/lavado-y-secado/lavadoras', ['WashingMachine'],
             'Inicio > Electro Hogar > Lavado y Secado > Lavadoras', 1],
            ['electro-hogar/lavado-y-secado/secadoras', ['WashingMachine'],
             'Inicio > Electro Hogar > Lavado y Secado > Secadoras', 1],
            ['electro-hogar/lavado-y-secado/lavadoras-secadoras',
             ['WashingMachine'],
             'Inicio > Electro Hogar > Lavado y Secado > Lavadoras-Secadoras',
             1],
            ['electro-hogar/lavado-y-secado/lavavajillas', ['DishWasher'],
             'Inicio > Electro Hogar > Lavado y Secado > Lavavajillas', 1],

            ['electro-hogar/cocina', ['Oven', 'Stove'],
             'Inicio > Electro Hogar > Cocina', 0],
            ['electro-hogar/cocina/cocinas', ['Stove'],
             'Inicio > Electro Hogar > Cocina > Cocinas', 1],
            ['electro-hogar/cocina/encimeras', ['Stove'],
             'Inicio > Electro Hogar > Cocina > Encimeras', 1],
            ['electro-hogar/cocina/hornos-empotrados', ['Oven'],
             'Inicio > Electro Hogar > Cocina > Hornos Empotrados', 1],
            ['electro-hogar/cocina/hornos-electricos', ['Oven'],
             'Inicio > Electro Hogar > Cocina > Hornos Eléctricos', 1],
            ['electro-hogar/cocina/microondas', ['Oven'],
             'Inicio > Electro Hogar > Cocina > Microondas', 1],

            ['electro-hogar/climatizacion',
             ['AirConditioner', 'SpaceHeater', 'WaterHeater'],
             'Inicio > Electro Hogar > Climatización', 0],
            ['electro-hogar/climatizacion/enfriadores-y-aire-acondicionado',
             ['AirConditioner'], 'Inicio > Electro Hogar > Climatizacioń >  '
                                 'Enfriadores y Aire Acondicionado', 1],
            # ['electro-hogar/climatizacion/estufas-a-parafinas',
            #  ['SpaceHeater'],
            #  'Inicio > Electro Hogar > Climatizacioń > Estufas a Parafinas',
            #  1],
            ['electro-hogar/climatizacion/estufas-a-gas', ['SpaceHeater'],
             'Inicio > Electro Hogar > Climatización > Estufas a Gas', 1],
            # ['electro-hogar/climatizacion/estufa-a-lena', ['SpaceHeater'],
            #  'Inicio > Electro Hogar > Climatización > Estufa a Leña', 1],
            ['electro-hogar/climatizacion/estufas-electricas', ['SpaceHeater'],
             'Inicio > Electro Hogar > Climatización > Estufas Eléctricas', 1],
            ['electro-hogar/climatizacion/calefont-y-termos', ['WaterHeater'],
             'Inicio > Electro Hogar > Climatización > Calefont y Termos', 1],

            ['tecnologia/tv-video', ['Television', 'OpticalDiskPlayer'],
             'Inicio > Tecnología > TV Video', 0],
            ['tecnologia/tv-video/todos-los-led', ['Television'],
             'Inicio > Tecnología > Tv Video > Todos los Led', 1],
            ['tecnologia/tv-video/smart-tv-hasta-50', ['Television'],
             'Inicio > Tecnología > Tv Video > Smart TV Hasta 50', 1],
            ['tecnologia/tv-video/smart-tv-entre-55-y-60', ['Television'],
             'Inicio > Tecnología > Tv Video > Smart TV Entre 55 y 60', 1],
            ['tecnologia/tv-video/smart-tv-desde-65', ['Television'],
             'Inicio > Tecnología > Tv Video > Smart TV Desde 65', 1],
            ['tecnologia/tv-video/led-samsung', ['Television'],
             'Inicio > Tecnología > Tv Video > Led Samsung', 1],
            ['tecnologia/tv-video/led-lg', ['Television'],
             'Inicio > Tecnología > Tv Video > Led LG', 1],
            # ['tecnologia/tv-video/led-extra-grandes', ['Television'],
            #  'Inicio > Tecnología > Tv Video > Led Extra Grandes', 1],
            ['tecnologia/tv-video/todos-los-led', ['Television'],
             'Inicio > Tecnología > Tv Video > Todos los Led', 1],
            # ['tecnologia/tv-video/dvd-y-blu-ray', ['OpticalDiskPlayer'],
            #  'Inicio > Tecnología > TV Video > DVD y Blu-Ray', 1],
            ['tecnologia/computacion',
             ['Notebook', 'Tablet', 'Printer', 'Monitor', 'Projector',
              'Pendrive', 'ExternalStorageDrive'],
             'Inicio > Tecnología > Computación', 0],
            ['tecnologia/computacion/notebook', ['Notebook'],
             'Inicio > Tecnología > Computación > Notebook', 1],
            ['tecnologia/computacion/tablets', ['Tablet'],
             'Inicio > Tecnología > Computación > Tablets', 1],
            ['tecnologia/computacion/all-in-one', ['AllInOne'],
             'Inicio > Tecnología > Computacioń > All in One', 1],
            # ['tecnologia/computacion/monitores-y-proyectores',
            #  ['Monitor', 'Projector'],
            #  'Inicio > Tecnología > Computación > Monitores y Proyectores',
            #  0.5],
            ['tecnologia/computacion/impresoras-y-multifuncionales',
             ['Printer'],
             'Inicio > Tecnología > Computación > '
             'Impresoras y Multifuncionales', 1],
            ['tecnologia/computacion/pendrive', ['UsbFlashDrive'],
             'Inicio > Tecnología > Computación > Pendrive', 1],
            ['tecnologia/computacion/disco-duro', ['ExternalStorageDrive'],
             'Inicio > Tecnología > Computación > Disco Duro', 1],

            ['tecnologia/video-juego/consolas', ['VideoGameConsole'],
             'Inicio > Tecnología > Video Juego > Consolas', 1],

            ['tecnologia/audio', ['StereoSystem', 'Headphones'],
             'Inicio > Tecnología > Audio', 0],
            ['tecnologia/audio/parlantes-bluetooth', ['StereoSystem'],
             'Inicio > Tecnología > Audio > Parlantes Bluetooth', 1],
            ['tecnologia/audio/karaokes', ['StereoSystem'],
             'Inicio > Tecnología > Audio > Karaokes', 1],
            ['tecnologia/audio/minicomponentes', ['StereoSystem'],
             'Inicio > Tecnología > Audio > Minicomponentes', 1],
            ['tecnologia/audio/soundbar-y-home-theater', ['StereoSystem'],
             'Inicio > Tecnología > Audio > Soundbar y Home Theater', 1],
            # ['tecnologia/audio/microcomponentes', ['StereoSystem'],
            #  'Inicio > Tecnología > Audio > Microcomponentes', 1],
            ['tecnologia/audio/audifonos', ['Headphones'],
             'Inicio > Tecnología > Audio > Audífonos', 1],

            ['celulares/accesorios/audifonos', ['Headphones'],
             'Inicio > Celulares > Accesorios > Audífonos', 1],
            ['tecnologia/accesorios-y-otros/mouse-y-teclados',
             ['Mouse', 'Keyboard'],
             'Inicio > Tecnología > Accesorios y Otros > Mouse y Teclados',
             0.5],
            ['tecnologia/accesorios-y-otros/tarjetas-de-memoria',
             ['MemoryCard'],
             'Inicio > Tecnología > Accesorios y Otros > Tarjetas de Memoria',
             1],

            ['celulares/smartphone', ['Cell', 'Wearable'],
             'Inicio > Celulares > Smartphone', 0],
            ['celulares/smartphone/smartphone', ['Cell'],
             'Inicio > Celulares > Smartphone > Smartphone', 1],
            ['celulares/smartphone/smartphone-liberados', ['Cell'],
             'Inicio > Celulares > Smartphone > Smartphone Liberados', 1],
            # ['celulares/smartphone/celulares-basicos', ['Cell'],
            #  'Inicio > Celulares > Smartphone > Celulares Basicos', 1],
            ['celulares/accesorios/wearables', ['Wearable'],
             'Inicio > Celulares > Accesorios > Wearables', 1],

            ['electro-hogar/electrodomesticos/aspiradoras-y-enceradoras',
             ['VacuumCleaner'],
             'Inicio > Electro Hogar > Electrodomésticos > '
             'Aspiradoras y Enceradoras', 1]
        ]

        product_entries = defaultdict(lambda: [])
        session = session_with_proxy(extra_args)

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            page = 1
            current_position = 1

            while True:
                category_url = 'https://www.hites.com/{}?pageSize=48&page={}' \
                               ''.format(category_path, page)

                print(category_url)

                if page >= 20:
                    raise Exception('Page overflow: ' + category_url)

                response = session.get(category_url, timeout=60)

                if response.status_code in [404, 500]:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                json_data = json.loads(soup.find(
                    'script', {'id': 'hy-data'}).text)

                if not json_data.get('result'):
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                product_data = json_data['result']['products']

                if not product_data:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                for product_entry in product_data:
                    slug = product_entry['productString']
                    product_url = 'https://www.hites.com/' + slug
                    product_entries[product_url].append({
                        'category_weight': category_weight,
                        'section_name': section_name,
                        'value': current_position
                    })
                    current_position += 1

                page += 1

        return product_entries

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        page = 1

        while True:
            if page > 40:
                raise Exception('Page overflow')

            search_url = 'https://www.hites.com/search/{}?page={}'\
                .format(keyword, page)
            print(search_url)

            response = session.get(search_url, timeout=60)

            if response.status_code in [404, 500]:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            json_data = json.loads(soup.find(
                'script', {'id': 'hy-data'}).text)
            product_data = json_data['result']['products']

            if not product_data:
                break

            for product_entry in product_data:
                slug = product_entry['productString']
                product_url = 'https://www.hites.com/' + slug
                product_urls.append(product_url)
                if len(product_urls) == threshold:
                    return product_urls

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, timeout=60)

        if response.status_code == 404:
            return []

        page_source = response.text
        soup = BeautifulSoup(page_source, 'html.parser')

        if soup.find('section', 'error-page'):
            return []

        if soup.find('img', {'src': '/public/statics/images/404.svg'}):
            return []

        json_data = json.loads(soup.find('script', {'id': 'hy-data'}).text)[
            'product']

        if 'name' in json_data and json_data['name']:
            name = json_data['name']
        else:
            name = "N/A"

        sku = json_data['partNumber']

        delivery_stock_container = soup.find(
            'div', 'accordion__desktop').findAll('div')[0]

        if 'product__service--unavailable' in \
                delivery_stock_container.attrs['class']:
            pickup_store_codes = [
                '0%2640001',
                '1%2640002',
                '2%2640003',
                '3%2640004'
            ]
            for code in pickup_store_codes:
                pickup_url = 'https://www.hites.com/api/product/{}001/' \
                             'pickup?value={}'.format(sku, code)
                pickup_data = json.loads(session.get(pickup_url).text)
                if pickup_data['phyStoreListDataBean']:
                    stock = -1
                    break
            else:
                # No "break" was called above
                stock = 0
        else:
            stock = -1

        if json_data['isOutOfStock'] or \
                'images' not in json_data['children'][0]:
            picture_urls = [json_data['fullImage']]
        else:
            picture_urls = json_data['children'][0]['images']

        if 'prices' not in json_data["children"][0].keys():
            return []

        reference_price = json_data["children"][0]['prices']['listPrice']
        normal_price = json_data["children"][0]['prices']['offerPrice']

        if normal_price:
            normal_price = Decimal(normal_price)
        else:
            normal_price = Decimal(reference_price)

        offer_price = json_data["children"][0]['prices']['cardPrice']

        if offer_price:
            offer_price = Decimal(offer_price)
        else:
            offer_price = normal_price

        if offer_price > normal_price:
            offer_price = normal_price

        long_description = json_data.get('longDescription', '') or ''
        description = html_to_markdown(long_description)

        for attribute in json_data['attributes']:
            if attribute['displayable']:
                description += '\n{} {}'.format(attribute['name'],
                                                attribute.get('value', ''))

        has_virtual_assistant = \
            'cdn.livechatinc.com/tracking.js' in response.text

        ld_soup = BeautifulSoup(long_description, 'html.parser')

        flixmedia_container = ld_soup.find(
            'script', {'src': '//media.flixfacts.com/js/loader.js'})
        flixmedia_id = None

        if flixmedia_container:
            mpn = flixmedia_container['data-flix-mpn']
            video_urls = flixmedia_video_urls(mpn)
            if video_urls is not None:
                flixmedia_id = mpn

        if 'reacondicionado' in name.lower():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

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
            condition=condition,
            description=description,
            picture_urls=picture_urls,
            flixmedia_id=flixmedia_id,
            has_virtual_assistant=has_virtual_assistant
        )

        return [p]

    @classmethod
    def banners(cls, extra_args=None):
        base_url = 'https://www.hites.com/{}'

        sections_data = [
            [bs.HOME, 'Home', bs.SUBSECTION_TYPE_HOME, ''],
            [bs.TELEVISIONS, 'TV Video', bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/tv-video'],
            [bs.TELEVISIONS, 'Todos los Led', bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/tv-video/todos-los-led'],
            [bs.TELEVISIONS, 'Smart TV Hasta 50', bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/tv-video/smart-tv-hasta-50'],
            [bs.TELEVISIONS, 'Smart TV Entre 55 y 60',
             bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/tv-video/smart-tv-entre-55-y-60'],
            [bs.TELEVISIONS, 'Smart TV Desde 65', bs.SUBSECTION_TYPE_MOSAIC,
             'tecnologia/tv-video/smart-tv-desde-65'],
            [bs.CELLS, 'Smartphone', bs.SUBSECTION_TYPE_MOSAIC,
             'celulares/smartphone'],
            [bs.CELLS, 'Smartphone-Smartphone', bs.SUBSECTION_TYPE_MOSAIC,
             'celulares/smartphone/smartphone'],
            [bs.CELLS, 'Smartphone Liberados', bs.SUBSECTION_TYPE_MOSAIC,
             'celulares/smartphone/smartphone-liberados'],
            [bs.REFRIGERATION, 'Refrigeradores', bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/refrigeradores'],
            [bs.REFRIGERATION, 'No Frost', bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/refrigeradores/no-frost'],
            [bs.REFRIGERATION, 'Side by Side', bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/refrigeradores/side-by-side'],
            [bs.WASHING_MACHINES, 'Lavado y Secado', bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/lavado-y-secado'],
            [bs.WASHING_MACHINES, 'Lavadoras', bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/lavado-y-secado/lavadoras'],
            [bs.WASHING_MACHINES, 'Lavadoras-Secadoras',
             bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/lavado-y-secado/lavadoras-secadoras'],
            [bs.WASHING_MACHINES, 'Secadoras', bs.SUBSECTION_TYPE_MOSAIC,
             'electro-hogar/lavado-y-secado/secadoras'],
            [bs.AUDIO, 'Audio', bs.SUBSECTION_TYPE_MOSAIC, 'tecnologia/audio'],
            # [bs.AUDIO, 'Minicomponentes', bs.SUBSECTION_TYPE_MOSAIC,
            #  'tecnologia/audio/minicomponentes'],
            # [bs.AUDIO, 'Soundbar y Home Theater', bs.SUBSECTION_TYPE_MOSAIC,
            #  'tecnologia/audio/soundbar-y-home-theater']
        ]

        session = session_with_proxy(extra_args)
        banners = []

        for section, subsection, subsection_type, url_suffix in sections_data:
            url = base_url.format(url_suffix)
            print(url)

            if subsection_type == bs.SUBSECTION_TYPE_HOME:
                with HeadlessChrome(images_enabled=True,
                                    timeout=120) as driver:
                    driver.set_window_size(1920, 1080)
                    driver.get(url)

                    pictures = []

                    banner_container = driver\
                        .find_element_by_class_name('slick-list')

                    # banner_container = driver \
                    #     .find_element_by_class_name('owl-stage-outer')

                    controls = driver.find_element_by_class_name(
                        'slick-dots')\
                        .find_elements_by_tag_name('li')

                    # controls = driver.find_elements_by_class_name('owl-dot')

                    for control in controls:
                        control.click()
                        time.sleep(1)
                        pictures.append(
                            banner_container.screenshot_as_base64)

                    soup = BeautifulSoup(driver.page_source, 'html.parser')

                    images = soup.find('div', 'slick-track')\
                        .findAll('div', 'slick-slide')

                    # images = soup.find('div', 'owl-stage') \
                    #     .findAll('div', 'owl-item')

                    images = [a for a in images if
                              'slick-cloned' not in a['class']]

                    # images = [a for a in images if
                    #           'cloned' not in a['class']]

                    assert len(images) == len(pictures)

                    for index, image in enumerate(images):
                        product_box = image.find('div', 'boxproductos')

                        if not product_box:
                            product_box = image.find('div', 'box-producto')

                        if not product_box:
                            product_box = image.find('div', 'box-foto')

                        if not product_box:
                            product_box = image.find(
                                'div', 'slide-new__products')

                        if not product_box:
                            product_box = image.find('div', 'images_llamados')

                        if not product_box:
                            product_box = image.find(
                                'div', 'products-item__img')

                        if not product_box:
                            product_box = image.find('a', 'boxproducto')

                        if not product_box:
                            product_box = image

                        if not (product_box.find('source') or
                                product_box.find('img')):
                            product_box = image.find('div', 'img_boxproducto')

                        if not product_box:
                            product_box = image.find('div', 'logocampana')

                        key_container = product_box.find('source')

                        if key_container:
                            key = key_container['srcset']
                        else:
                            key = product_box.find('img')['src']

                        destinations = [d for d in image.findAll('a')]
                        destination_urls = []

                        for destination in destinations:
                            if destination.get('href'):
                                destination_urls.append(destination['href'])

                        destination_urls = list(set(destination_urls))

                        banners.append({
                            'url': url,
                            'picture': pictures[index],
                            'destination_urls': destination_urls,
                            'key': key,
                            'position': index + 1,
                            'section': section,
                            'subsection': subsection,
                            'type': subsection_type
                        })
            elif subsection_type == bs.SUBSECTION_TYPE_MOSAIC:
                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')

                banners_container = soup.find('section')\
                    .findAll('div', 'espot', recursive=False)

                for index, banner in enumerate(banners_container):
                    destination_urls = [d['href'] for d in
                                        banner.findAll('a')]

                    destination_urls = list(set(destination_urls))

                    picture_container = banner.find('picture')

                    if picture_container:
                        picture_source = picture_container.find('source')

                        if not picture_source:
                            continue

                        picture_url = picture_source['srcset']
                        banners.append({
                            'url': url,
                            'picture_url': picture_url,
                            'destination_urls': destination_urls,
                            'key': picture_url,
                            'position': index + 1,
                            'section': section,
                            'subsection': subsection,
                            'type': subsection_type
                        })
                    else:
                        with HeadlessChrome(images_enabled=True, timeout=120) \
                                as driver:
                            driver.set_window_size(1920, 1080)
                            driver.get(url)

                            s_banner = driver.find_elements_by_css_selector(
                                '#main>.espot')[index]

                            key_container = banner.find('img')

                            if not key_container or \
                                    s_banner.size['height'] == 0:
                                continue

                            key = key_container['src']

                            picture = s_banner.screenshot_as_base64
                            banners.append({
                                'url': url,
                                'picture': picture,
                                'destination_urls': destination_urls,
                                'key': key,
                                'position': index + 1,
                                'section': section,
                                'subsection': subsection,
                                'type': subsection_type
                            })

        return banners
