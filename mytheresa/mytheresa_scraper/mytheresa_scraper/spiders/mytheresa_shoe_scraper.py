import scrapy
import re
import time
import random
from curl_cffi import requests
from parsel import Selector

class MytheresaScraper(scrapy.Spider):
    name = "mytheresa"
    start_urls = ['https://www.mytheresa.com/int/en/men/shoes?page=1']

    def parse(self, response):
        current_page = response.meta.get("page", 1)
        products = response.xpath('//div[@class="item item--sale"]')

        if not products:
            self.logger.info(f"No more products found on page {current_page}. Stopping.")
            return

        for product in products:
            product_url = product.xpath('.//a[@class="item__link"]/@href').get()
            if product_url:
                full_url = f'https://www.mytheresa.com{product_url}'
                meta_data = {
                    'brand': product.xpath('.//div[@class="item__info__header__designer"]/text()').get(),
                    'product_name': product.xpath('.//div[@class="item__info__name"]/a/text()').get(),
                    'discount': product.xpath('.//span[@class="pricing__info__percentage"]/text()').get()
                }
                yield from self.parse_with_curl(full_url, meta_data)

        next_page = current_page + 1
        next_url = f'https://www.mytheresa.com/int/en/men/shoes?page={next_page}'
        yield scrapy.Request(
            url=next_url,
            callback=self.parse,
            meta={'page': next_page},
            dont_filter=True
        )
    def parse_with_curl(self, url, meta):
        USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
        ]

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'cache-control': 'max-age=0',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            # 'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            "User-Agent": random.choice(USER_AGENTS)
        }


        try:
            response = requests.get(url,headers=headers ,impersonate='chrome')
            time.sleep(1)  # polite delay to reduce rate-limiting
        except Exception as e:
            self.logger.warning(f"Failed to fetch {url} using curl_cffi: {e}")
            return
        sel = Selector(text=response.text)

        brand = sel.xpath('//a[@class="product__area__branding__designer__link"]/text()').get() or meta.get('brand')
        name = sel.xpath('//div[@class="product__area__branding__name"]/text()').get() or meta.get('product_name')
        breadcrumb = sel.xpath('//div[@class="breadcrumb"]/div/a/text()').getall()
        images = sel.xpath('//img[@class="product__gallery__carousel__image"]/@src').getall()
        sizes = sel.xpath('//div[@class="sizeitem__wrapper"]/span/text()').getall()
        description = sel.xpath('//div[@data-overlayscrollbars-contents]//ul/li/text()').getall()
        listing_price = sel.xpath(
            'normalize-space(//span[contains(@class, "pricing__prices__value--original")]//span[contains(@class, "pricing__prices__price")])'
        ).get()
        discount_price = sel.xpath(
            'normalize-space(//span[contains(@class, "pricing__prices__value--discount")]//span[contains(@class, "pricing__prices__price")])'
        ).get()

        match = re.search(r'(p\d+)$', url)
        product_id = match.group(1) if match else None

        yield {
            'breadcrumbs': breadcrumb,
            'image_url': images[1] if images else '',
            'brand': brand,
            'product_name': name,
            'listing_price': listing_price,
            'offer_price': discount_price,
            'discount': meta.get('discount'),
            'product_id': product_id,
            'available_sizes': sizes,
            # 'product_url': url,
            'description': description,
            'other_images' : images
        }

