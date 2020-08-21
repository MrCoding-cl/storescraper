import re
import time
from bs4 import BeautifulSoup

from storescraper.utils import get_cf_session, HeadlessChrome, \
    load_driver_cf_cookies, session_with_proxy
from storescraper import banner_sections as bs
from .ripley_chile_base import RipleyChileBase
from selenium.common.exceptions import NoSuchElementException


class Ripley(RipleyChileBase):
    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = get_cf_session(extra_args)
        product_urls = []

        page = 1

        while True:
            if page > 40:
                raise Exception('Page overflow')

            search_url = 'https://simple.ripley.cl/search/{}?page={}'\
                .format(keyword, page)
            response = session.get(search_url, allow_redirects=False)

            if response.status_code != 200:
                raise Exception('Invalid search: ' + keyword)

            soup = BeautifulSoup(response.text, 'html.parser')

            products_container = soup.find('div', 'catalog-container')

            if not products_container:
                break

            products = products_container.findAll('a', 'catalog-product-item')

            for product in products:
                product_url = 'https://simple.ripley.cl' + product['href']
                product_urls.append(product_url)
                if len(product_urls) == threshold:
                    return product_urls

            page += 1

        return product_urls

    @classmethod
    def banners(cls, extra_args=None):
        from .ripley_chile_base_cf import RipleyChileBaseCf

        extra_args = RipleyChileBaseCf._extra_args_with_preflight(extra_args)

        base_url = 'https://simple.ripley.cl/{}'

        sections_data = [
            [bs.HOME, 'Home', bs.SUBSECTION_TYPE_HOME, ''],
            [bs.ELECTRO_RIPLEY, 'Electro Ripley',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE, 'electro/'],
            [bs.TECNO_RIPLEY, 'Tecno Ripley',
             bs.SUBSECTION_TYPE_CATEGORY_PAGE, 'tecno/'],
            [bs.REFRIGERATION, 'Refrigeración',
             bs.SUBSECTION_TYPE_MOSAIC, 'electro/refrigeracion/'],
            [bs.REFRIGERATION, 'Refrigeradores', bs.SUBSECTION_TYPE_MOSAIC,
             'electro/refrigeracion/refrigeradores/'],
            [bs.WASHING_MACHINES, 'Lavandería',
             bs.SUBSECTION_TYPE_MOSAIC, 'electro/lavanderia'],
            [bs.WASHING_MACHINES, 'Lavadoras',
             bs.SUBSECTION_TYPE_MOSAIC, 'electro/lavanderia/lavadoras'],
            [bs.WASHING_MACHINES, 'Lavadora-secadora',
             bs.SUBSECTION_TYPE_MOSAIC,
             'electro/lavanderia/lavadora-secadora'],
            [bs.WASHING_MACHINES, 'Doble Carga',
             bs.SUBSECTION_TYPE_MOSAIC, 'electro/lavanderia/doble-carga'],
            [bs.TELEVISIONS, 'Televisión',
             bs.SUBSECTION_TYPE_MOSAIC, 'tecno/television'],
            [bs.TELEVISIONS, 'Smart TV',
             bs.SUBSECTION_TYPE_MOSAIC, 'tecno/television/smart-tv'],
            [bs.TELEVISIONS, '4K – UHD - NanoCell',
             bs.SUBSECTION_TYPE_MOSAIC, 'tecno/television/4k-uhd-nanocell'],
            [bs.TELEVISIONS, 'Premium - OLED - QLED - 8K',
             bs.SUBSECTION_TYPE_MOSAIC,
             'tecno/television/premium-oled-qled-8k'],
            [bs.TELEVISIONS, 'HD - Full HD',
             bs.SUBSECTION_TYPE_MOSAIC, 'tecno/television/hd-full-hd'],
            [bs.AUDIO, 'Audio y Música',
             bs.SUBSECTION_TYPE_MOSAIC, 'tecno/audio-y-musica'],
            # [AUDIO, 'Parlantes y Subwoofer', SUBSECTION_TYPE_MOSAIC,
            #  'tecno/audio-y-musica/parlantes-y-subwoofer'],
            # [AUDIO, 'Microcomponentes',
            #  SUBSECTION_TYPE_MOSAIC,
            #  'tecno/audio-y-musica/microcomponentes'],
            [bs.AUDIO, 'Soundbar y Home theater',
             bs.SUBSECTION_TYPE_MOSAIC,
             'tecno/audio-y-musica/soundbard-y-home-theater'],
            [bs.AUDIO, 'Parlantes Portables',
             bs.SUBSECTION_TYPE_MOSAIC,
             'tecno/audio-y-musica/parlantes-portables'],
            [bs.CELLS, 'Telefonía',
             bs.SUBSECTION_TYPE_MOSAIC, 'tecno/telefonia'],
            [bs.CELLS, 'Android',
             bs.SUBSECTION_TYPE_MOSAIC, 'tecno/telefonia/android'],
            [bs.CELLS, 'iPhone',
             bs.SUBSECTION_TYPE_MOSAIC, 'tecno/telefonia/iphone']
        ]

        debug = extra_args.get('debug', False)
        if debug:
            session = session_with_proxy(extra_args)
        else:
            session = get_cf_session(extra_args)
        banners = []

        for section, subsection, subsection_type, url_suffix in sections_data:
            url = base_url.format(url_suffix)
            response = session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            if subsection_type == bs.SUBSECTION_TYPE_HOME:
                banners = banners + cls.get_owl_banners(
                    url, section, subsection, subsection_type, extra_args)

            elif subsection_type == bs.SUBSECTION_TYPE_CATEGORY_PAGE:
                if soup.find('div', 'owl-carousel'):
                    banners = banners + cls.get_owl_banners(
                        url, section, subsection, subsection_type, extra_args)
                else:
                    images = soup.findAll('a', 'item')

                    if not images:
                        print('No banners')

                    for index, image in enumerate(images):
                        picture = image.find('span', 'bg-item')
                        picture_url = re.search(
                            r'url\((.*?)\)', picture['style']).group(1)

                        destination_urls = [image['href']]

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
            elif subsection_type == bs.SUBSECTION_TYPE_MOSAIC:
                picture_container = soup.find('section', 'catalog-top-banner')

                if not picture_container:
                    print('No banners')
                    continue

                picture_url = picture_container.find('img')

                if not picture_url:
                    continue

                destination = soup.find(
                    'section', 'catalog-top-banner').find('a')
                destination_urls = []

                if destination:
                    destination_urls = [destination['href']]

                banners.append({
                    'url': url,
                    'picture_url': picture_url.get('src') or
                    picture_url.get('data-src'),
                    'destination_urls': destination_urls,
                    'key': picture_url.get('src') or
                    picture_url.get('data-src'),
                    'position': 1,
                    'section': section,
                    'subsection': subsection,
                    'type': subsection_type
                })
            else:
                raise Exception('Invalid subsection type')

        return banners

    @classmethod
    def get_owl_banners(cls, url, section, subsection, type, extra_args):
        with HeadlessChrome(images_enabled=True, timeout=60,
                            proxy=extra_args['proxy']) as driver:
            print(url)
            banners = []
            driver.set_window_size(1920, 1080)
            driver.set_page_load_timeout(240)
            # Open the page first so that the CF cookies can be loaded in
            # this domain
            driver.get(url)
            # Then set the sesion cookies
            load_driver_cf_cookies(driver, extra_args, '.ripley.cl')
            # Then re-open the page
            driver.get(url)
            driver.execute_script("scrollTo(0, 0);")

            pictures = []

            banner_container = driver \
                .find_element_by_class_name('owl-carousel')

            controls = banner_container \
                .find_elements_by_class_name('owl-page')

            for control in controls:
                control.click()
                time.sleep(1)
                pictures.append(
                    banner_container.screenshot_as_base64)

            images = banner_container.find_elements_by_class_name('owl-item')

            assert len(images) == len(pictures)

            for index, image in enumerate(images):
                try:
                    image_style = image.find_element_by_tag_name(
                        'span').get_attribute('style')
                    key = re.search(r'url\((.*?)\)', image_style) \
                        .group(1)
                except NoSuchElementException:
                    key = image.find_element_by_tag_name(
                        'source').get_attribute('srcset')

                destinations = image.find_elements_by_tag_name('a')
                destination_urls = [a.get_attribute('href')
                                    for a in destinations]
                destination_urls = list(set(destination_urls))

                destination_urls = list(set(destination_urls))

                banners.append({
                    'url': url,
                    'picture': pictures[index],
                    'destination_urls': destination_urls,
                    'key': key,
                    'position': index + 1,
                    'section': section,
                    'subsection': subsection,
                    'type': type
                })

            return banners

    @classmethod
    def filter_url(cls, url):
        return '-mpm' not in url
