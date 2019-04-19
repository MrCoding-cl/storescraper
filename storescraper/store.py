import traceback
from collections import defaultdict

from celery import shared_task, group
from celery.result import allow_join_result
from celery.utils.log import get_task_logger


from .product import Product
from .utils import get_store_class_by_name, chunks

logger = get_task_logger(__name__)


class StoreScrapError(Exception):
    def __init__(self, message):
        super(StoreScrapError, self).__init__(message)


class Store:
    preferred_discover_urls_concurrency = 3
    preferred_products_for_url_concurrency = 10
    prefer_async = True

    ##########################################################################
    # API methods
    ##########################################################################

    @classmethod
    def products(cls, categories=None, extra_args=None,
                 discover_urls_concurrency=None,
                 products_for_url_concurrency=None, use_async=None):
        sanitized_parameters = cls.sanitize_parameters(
            categories=categories,
            discover_urls_concurrency=discover_urls_concurrency,
            products_for_url_concurrency=products_for_url_concurrency,
            use_async=use_async)

        categories = sanitized_parameters['categories']
        discover_urls_concurrency = \
            sanitized_parameters['discover_urls_concurrency']
        products_for_url_concurrency = \
            sanitized_parameters['products_for_url_concurrency']
        use_async = sanitized_parameters['use_async']

        logger.info('Obtaining products from: {}'.format(cls.__name__))
        logger.info('Categories: {}'.format(', '.join(categories)))

        discovered_entries = cls.discover_entries_for_categories(
            categories=categories,
            extra_args=extra_args,
            discover_urls_concurrency=discover_urls_concurrency,
            use_async=use_async
        )

        return cls.products_for_urls(
            discovered_entries,
            extra_args=extra_args,
            products_for_url_concurrency=products_for_url_concurrency,
            use_async=use_async
        )

    @classmethod
    def discover_entries_for_categories(cls, categories=None,
                                        extra_args=None,
                                        discover_urls_concurrency=None,
                                        use_async=True):
        sanitized_parameters = cls.sanitize_parameters(
            categories=categories,
            discover_urls_concurrency=discover_urls_concurrency,
            use_async=use_async)

        categories = sanitized_parameters['categories']
        discover_urls_concurrency = \
            sanitized_parameters['discover_urls_concurrency']
        use_async = sanitized_parameters['use_async']

        logger.info('Discovering URLs for: {}'.format(cls.__name__))

        entry_positions = defaultdict(lambda: [])
        url_category_weights = defaultdict(lambda: defaultdict(lambda: 0))

        if use_async:
            category_chunks = chunks(categories, discover_urls_concurrency)

            for category_chunk in category_chunks:
                chunk_tasks = []

                logger.info('Discovering URLs for: {}'.format(
                    category_chunk))

                for category in category_chunk:
                    task = cls.discover_entries_for_category_task.s(
                        cls.__name__, category, extra_args)
                    task.set(
                        queue='storescraper',
                        max_retries=5
                    )
                    chunk_tasks.append(task)
                tasks_group = cls.create_celery_group(chunk_tasks)

                # Prevents Celery error for running a task inside another
                with allow_join_result():
                    task_results = tasks_group.get()

                for idx, task_result in enumerate(task_results):
                    category = category_chunk[idx]
                    logger.info('Discovered URLs for {}:'.format(category))
                    for entry in task_result:
                        logger.info(entry)
                        entry_positions[entry['url']].append(entry['positions'])
                        url_category_weights[entry['url']][category] += \
                            entry['category_weight']
        else:
            logger.info('Using sync method')
            for category in categories:
                for url, positions in cls.discover_entries_for_category(
                        category, extra_args).items():
                    logger.info('Discovered URL: {} ({})'.format(
                        url, category))
                    entry_positions[url].extend(positions)
                    for position in positions:
                        url_category_weights[url][category] += \
                            position['category_weight']

        discovered_entries = {}
        for url, positions in entry_positions.items():
            category, max_weight = max(url_category_weights[url].items(),
                                       key=lambda x: x[1])

            # Only include the url in the discovery set if it appears in a
            # weighted section, for example generic "Electrodomésticos"
            # section have 0 weight, but specific sections
            # (e.g. "Refrigeradores") have positive values. This allows us to
            # map generic section positioning without considering their
            # products if they don't appear in a specifically mapped
            # relevant section
            if max_weight:
                discovered_entries[url] = {
                    'positions': positions,
                    'category': category
                }

        return discovered_entries

    @classmethod
    def products_for_urls(cls, discovered_entries, extra_args=None,
                          products_for_url_concurrency=None,
                          use_async=True):
        sanitized_parameters = cls.sanitize_parameters(
            products_for_url_concurrency=products_for_url_concurrency,
            use_async=use_async)

        products_for_url_concurrency = \
            sanitized_parameters['products_for_url_concurrency']
        use_async = sanitized_parameters['use_async']

        logger.info('Retrieving products for: {}'.format(cls.__name__))

        for entry in discovered_entries:
            logger.info('{} ({})'.format(entry['url'], entry['category']))

        products = []
        discovery_urls_without_products = []

        if use_async:
            discovery_entries_chunks = chunks(
                discovered_entries, products_for_url_concurrency)

            task_counter = 1
            for discovery_entries_chunk in discovery_entries_chunks:
                chunk_tasks = []

                for discovered_entry in discovery_entries_chunk:
                    logger.info('Retrieving URL ({} / {}): {}'.format(
                        task_counter, len(discovered_entries),
                        discovered_entry['url']))
                    task = cls.products_for_url_task.s(
                        cls.__name__, discovered_entry['url'],
                        discovered_entry['category'], extra_args)
                    task.set(
                        queue='storescraper',
                        max_retries=5
                    )
                    chunk_tasks.append(task)
                    task_counter += 1

                tasks_group = cls.create_celery_group(chunk_tasks)

                # Prevents Celery error for running a task inside another
                with allow_join_result():
                    task_results = tasks_group.get()

                for idx, task_result in enumerate(task_results):
                    for serialized_product in task_result:
                        product = Product.deserialize(serialized_product)
                        product.positions = discovery_entries_chunk[idx][
                            'positions']

                        logger.info('{}\n'.format(product))
                        products.append(product)

                    if not task_result:
                        discovery_urls_without_products.append(
                            discovery_entries_chunk[idx]['url'])
        else:
            logger.info('Using sync method')
            for discovered_entry in discovered_entries:
                retrieved_products = cls.products_for_url(
                    discovered_entry['url'],
                    discovered_entry['category'],
                    extra_args)

                for product in retrieved_products:
                    product.positions = discovered_entry['positions']
                    logger.info('{}\n'.format(product))
                    products.append(product)

                if not retrieved_products:
                    discovery_urls_without_products.append(
                        discovered_entry['url'])

        return {
            'products': products,
            'discovery_urls_without_products': discovery_urls_without_products
        }

    ##########################################################################
    # Celery tasks wrappers
    ##########################################################################

    @staticmethod
    @shared_task(autoretry_for=(StoreScrapError,), max_retries=5,
                 default_retry_delay=5)
    def discover_entries_for_category_task(store_class_name, category,
                                           extra_args=None):
        store = get_store_class_by_name(store_class_name)
        logger.info('Discovering URLs')
        logger.info('Store: ' + store.__name__)
        logger.info('Category: ' + category)
        try:
            discovered_entries = store.discover_entries_for_category(
                category, extra_args)
        except Exception:
            error_message = 'Error discovering URLs from {}: {} - {}'.format(
                store_class_name,
                category,
                traceback.format_exc())
            logger.error(error_message)
            raise StoreScrapError(error_message)

        for idx, entry in enumerate(discovered_entries):
            logger.info('{} - {}'.format(idx, entry['url']))
        return discovered_entries

    @staticmethod
    @shared_task(autoretry_for=(StoreScrapError,), max_retries=5,
                 default_retry_delay=5)
    def products_for_url_task(store_class_name, url, category=None,
                              extra_args=None):
        store = get_store_class_by_name(store_class_name)
        logger.info('Obtaining products for URL')
        logger.info('Store: ' + store.__name__)
        logger.info('Category: {}'.format(category))
        logger.info('URL: ' + url)

        try:
            raw_products = store.products_for_url(
                url, category, extra_args)
        except Exception:
            error_message = 'Error retrieving products from {}: {} - {}' \
                            ''.format(store_class_name, url,
                                      traceback.format_exc())
            logger.error(error_message)
            raise StoreScrapError(error_message)

        serialized_products = [p.serialize() for p in raw_products]

        for idx, product in enumerate(serialized_products):
            logger.info('{} - {}'.format(idx, product))

        return serialized_products

    @staticmethod
    @shared_task(autoretry_for=(StoreScrapError,), max_retries=5,
                 default_retry_delay=5)
    def products_for_urls_task(store_class_name,
                               discovery_entries,
                               extra_args=None,
                               products_for_url_concurrency=None,
                               use_async=True):
        store = get_store_class_by_name(store_class_name)
        result = store.products_for_urls(
            discovery_entries, extra_args=extra_args,
            products_for_url_concurrency=products_for_url_concurrency,
            use_async=use_async)

        serialized_result = {
            'products': [p.serialize() for p in result['products']],
            'discovery_urls_without_products':
                result['discovery_urls_without_products']
        }

        return serialized_result

    ##########################################################################
    # Implementation dependant methods
    ##########################################################################

    @classmethod
    def categories(cls):
        raise NotImplementedError('This method must be implemented by '
                                  'subclasses of Store')

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        raise NotImplementedError('This method must be implemented by '
                                  'subclasses of Store')

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        raise NotImplementedError('This method must be implemented by '
                                  'subclasses of Store')

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        # If the concrete class does not implement it yet, call the old
        # discover_urls_for_category method and patch it
        urls = cls.discover_urls_for_category(category, extra_args)
        return {url: [] for url in urls}

    ##########################################################################
    # Utility methods
    ##########################################################################

    @classmethod
    def create_celery_group(cls, tasks):
        # REF: https://stackoverflow.com/questions/41371933/why-is-this-
        # construction-of-a-group-of-chains-causing-an-exception-in-celery
        if len(tasks) == 1:
            g = group(tasks)()
        else:
            g = group(*tasks)()
        return g

    @classmethod
    def sanitize_parameters(cls, categories=None,
                            discover_urls_concurrency=None,
                            products_for_url_concurrency=None, use_async=None):
        if categories is None:
            categories = cls.categories()
        else:
            categories = [category for category in cls.categories()
                          if category in categories]

        if discover_urls_concurrency is None:
            discover_urls_concurrency = cls.preferred_discover_urls_concurrency

        if products_for_url_concurrency is None:
            products_for_url_concurrency = \
                cls.preferred_products_for_url_concurrency

        if use_async is None:
            use_async = cls.prefer_async

        return {
            'categories': categories,
            'discover_urls_concurrency': discover_urls_concurrency,
            'products_for_url_concurrency': products_for_url_concurrency,
            'use_async': use_async,
        }
