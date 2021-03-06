import json

from collections import defaultdict
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Wom(Store):
    prepago_url = 'http://www.wom.cl/prepago/'
    planes_url = 'https://www.wom.cl/seguro/planes/'

    @classmethod
    def categories(cls):
        return [
            'CellPlan',
            'Cell'
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        discovered_entries = defaultdict(lambda: [])

        if category == 'CellPlan':
            discovered_entries[cls.prepago_url].append({
                'category_weight': 1,
                'section_name': 'Planes',
                'value': 1
            })

            discovered_entries[cls.planes_url].append({
                'category_weight': 1,
                'section_name': 'Planes',
                'value': 2
            })

        elif category == 'Cell':
            session = session_with_proxy(extra_args)
            session.headers[
                'Content-Type'] = 'application/x-www-form-urlencoded'
            equipos_url = 'https://store-srv.wom.cl/rest/V1/content/getList?' \
                          'searchCriteria[filterGroups][1][filters][0]' \
                          '[field]=type_id&searchCriteria[filterGroups][1]' \
                          '[filters][0][value]=configurable&searchCriteria' \
                          '[filterGroups][10][filters][0][field]=status&' \
                          'searchCriteria[filterGroups][10][filters][0]' \
                          '[value]=1'
            response = session.get(equipos_url)

            json_response = json.loads(response.text)

            for idx, cell_entry in enumerate(json_response['items']):
                cell_url = 'https://store.wom.cl/equipos/' + \
                           str(cell_entry['sku']) + '/' + cell_entry[
                               'name'].replace(' ', '-')
                discovered_entries[cell_url].append({
                    'category_weight': 1,
                    'section_name': 'Equipos',
                    'value': idx + 1
                })

        return discovered_entries

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = []
        if url == cls.prepago_url:
            # Plan Prepago
            p = Product(
                'WOM Prepago',
                cls.__name__,
                category,
                url,
                url,
                'WOM Prepago',
                -1,
                Decimal(0),
                Decimal(0),
                'CLP',
            )
            products.append(p)
        elif url == cls.planes_url:
            # Plan Postpago
            products.extend(cls._plans(url, extra_args))
        elif '/equipos/' in url:
            # Equipo postpago
            products.extend(cls._celular_postpago(url, extra_args))
        else:
            raise Exception('Invalid URL: ' + url)
        return products

    @classmethod
    def _plans(cls, url, extra_args):
        session = session_with_proxy(extra_args)
        json_data = session.get('https://store.wom.cl/page-data/planes/'
                                'page-data.json').json()
        products = []

        variants = [
            'sin cuota de arriendo',
            'con cuota de arriendo',
        ]

        for entry in json_data['result']['data'][
                'allContentfulProduct']['nodes']:
            plan_name = entry['name']

            # Skip planes "Solo Voz" or "Solo Datos"
            # Also skip "Grupal" plans
            if 'Solo' in plan_name or 'Grupal' in plan_name:
                continue

            context = json.loads(entry['context']['context'])
            plan_price = Decimal(context['price'])

            for variant in variants:
                for suffix in ['', ' Portabilidad']:
                    adjusted_plan_name = '{}{} ({})'.format(
                        plan_name, suffix, variant)

                    products.append(Product(
                        adjusted_plan_name,
                        cls.__name__,
                        'CellPlan',
                        url,
                        url,
                        adjusted_plan_name,
                        -1,
                        plan_price,
                        plan_price,
                        'CLP',
                    ))

        return products

    @classmethod
    def _celular_postpago(cls, url, extra_args):
        print(url)
        session = session_with_proxy(extra_args)

        path = url.split('/', 3)[-1]
        endpoint = 'https://store.wom.cl/page-data/{}/' \
                   'page-data.json'.format(path)
        json_data = session.get(endpoint).json()
        products = []
        plans = [
            'Plan WOM 10 Gigas',
            'Plan Womers 20 GB',
            'Plan Acumula 40 GB',
            'Plan Acumula 60 GB',
            'Plan Acumula 80 GB',
            'Plan Acumula 100 GB',
            'Plan Womers Libre'
        ]

        for entry in json_data['result']['data']['contentfulProduct'][
                'productVariations']:
            name = entry['name']
            context = json.loads(entry['context']['context'])
            graphql_data = json.loads(context['graphql_data'])

            portability_choices = [
                ('', 'newConnection'),
                (' Portabilidad', 'portIn'),
            ]

            for portability_name_suffix, portability_json_field in \
                    portability_choices:
                price_without_installments = None
                initial_price_with_installments = None
                installment_price = None

                for related_price in graphql_data['productOfferingPrice'][
                        portability_json_field]['relatedPrice']:
                    if related_price['priceType'] == 'price':
                        price_without_installments = Decimal(
                            related_price['price']['value'])
                    elif related_price['priceType'] == 'initialPrice':
                        initial_price_with_installments = Decimal(
                            related_price['price']['value'])
                    elif related_price['priceType'] == 'installmentPrice':
                        installment_price = Decimal(
                            related_price['price']['value'])

                assert price_without_installments is not None
                assert initial_price_with_installments is not None
                assert installment_price is not None

                for plan in plans:
                    # Without installments
                    products.append(Product(
                        name,
                        cls.__name__,
                        'Cell',
                        url,
                        url,
                        '{} {}{}'.format(name, plan, portability_name_suffix),
                        -1,
                        price_without_installments,
                        price_without_installments,
                        'CLP',
                        cell_plan_name='{}{}'.format(
                            plan,
                            portability_name_suffix,
                        ),
                        cell_monthly_payment=Decimal(0)
                    ))

                    # With installments
                    products.append(Product(
                        name,
                        cls.__name__,
                        'Cell',
                        url,
                        url,
                        '{} {}{} Cuotas'.format(name, plan,
                                                portability_name_suffix),
                        -1,
                        initial_price_with_installments,
                        initial_price_with_installments,
                        'CLP',
                        cell_plan_name='{}{} Cuotas'.format(
                            plan,
                            portability_name_suffix,
                        ),
                        cell_monthly_payment=installment_price
                    ))

            # Prepaid
            prepaid_price = Decimal(
                graphql_data['productOfferingPrice']['standard'][
                    'relatedPrice'][0]['price']['value'])

            products.append(Product(
                name,
                cls.__name__,
                'Cell',
                url,
                url,
                '{} Prepago'.format(name),
                -1,
                prepaid_price,
                prepaid_price,
                'CLP',
                cell_plan_name='WOM Prepago',
                cell_monthly_payment=Decimal(0)
            ))

        return products
