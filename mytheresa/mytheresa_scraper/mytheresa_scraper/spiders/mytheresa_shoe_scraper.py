import scrapy

class MytheresaScraper(scrapy.Spider):
    name = "mytheresa"
    start_urls = ['https://www.mytheresa.com/int/en/men/shoes?rdr']

    def crawler(self, response):
        for product in response.xpath('//div[@class="item item--sale"]'):
            product_url = product.xpath('.//a[@class="item__link"]/@href').get()
            if product_url:
                yield scrapy.Request(
                    url=response.urljoin(product_url),
                    callback=self.parse_product,
                    meta={
                        'brand': product.xpath('.//div[@class="item__info__header__designer"]/text()').get(),
                        'product_name': product.xpath('.//div[@class="item__info__name"]/a/text()').get(),
                        'discount': product.xpath('.//span[@class="pricing__info__percentage"]/text()').get()
                    }
                )

    def parser(self, response):
        brand = response.meta.get('brand')
        product_name = response.meta.get('product_name')
        discount = response.meta.get('discount')

        description = response.xpath('//div[@class="product-description__text"]/text()').get()
        price = response.xpath('//div[contains(@class,"product-info-price")]/span/text()').get()
        sizes = response.xpath('//select[@id="size"]/option/text()').getall()

        yield {
            'brand': brand,
            'product_name': product_name,
            'discount': discount,
            'product_url': response.url,
            'price': price,
            # 'description': description,
            # 'available_sizes': [size.strip() for size in sizes if size.strip()]
        }