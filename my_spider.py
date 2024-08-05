import traceback
from urllib.parse import urlparse
from pathlib import Path
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.extensions.logstats import LogStats
from scrapy.extensions.closespider import CloseSpider
from scrapy.spidermiddlewares.depth import DepthMiddleware
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from twisted.internet import reactor
from multiprocessing import Process, Queue
# import pdb

class MySpider(CrawlSpider):
    name = 'my_spider'

    def __init__(self, url, found_pages, n=3, max_pages=10, save_pages=False, output_folder = 'pages', *args, **kwargs):
        super(MySpider, self).__init__(*args, **kwargs)
        self.start_urls = [url]
        domain = urlparse(url).netloc
        self.allowed_domains = [domain]
        self.n = int(n)
        self.max_pages = int(max_pages)
        self.save_pages = save_pages in [True, 'True', 'true', 't', 1, '1'] 
        self.output_folder = output_folder
        Path(f"{self.output_folder}").mkdir(parents=True, exist_ok=True)
        if self.save_pages:
            Path(f"{self.output_folder}/{domain}").mkdir(parents=True, exist_ok=True)
        self.found_pages = found_pages  # Initialize an empty set to store unique pages
        self.custom_settings = {
            "LOG_ENABLED": False,
            "LOG_LEVEL": "INFO",
            "CLOSESPIDER_ITEMCOUNT": self.max_pages,
            "CLOSESPIDER_PAGECOUNT": self.max_pages,
            "DEPTH_LIMIT": self.n,
            "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7"
        }
    
    rules = (
        Rule(LinkExtractor(), callback='parse_item', follow=True),
    )

    extensions = {
        scrapy.extensions.closespider.CloseSpider: 1,
        scrapy.spidermiddlewares.depth.DepthMiddleware: 1,
        scrapy.extensions.logstats.LogStats: 0
    }

    def parse_item(self, response):
        if (len(self.found_pages) >= self.max_pages):
            #pdb.set_trace()
            self.crawler.engine.close_spider(self, "max page limit reached")
            return

        #print(f'page found: {response.url}')
        domain = urlparse(self.start_urls[0]).netloc
        if self.save_pages:
            filename = f"{self.output_folder}/{domain}/page_{response.url.split('/')[-2]}.html"
            with open(filename, 'wb') as f:
                f.write(response.body)
        self.found_pages.add(response.url)  # Add the page url to the set
        if (len(self.found_pages) >= self.max_pages):
            #print('max page limit reached')
            self.crawler.engine.close_spider(self, "max page limit reached")
            return
        
        if response.meta.get('depth', 0) < self.n:
            try:
                yield from super().parse_item(response)
            except AttributeError as ae: 
                if "parse_item" not in ae.args[0]:
                    traceback.print_exc
                if hasattr(ae, 'message') and "parse_item" not in ae.message:
                    traceback.print_exc

    def closed(self, reason):
        # pdb.set_trace()
        result = { 'pages': sorted(list(self.found_pages)), 'count': len(self.found_pages) }
        domain = urlparse(self.start_urls[0]).netloc
        list_filename = Path(f"{self.output_folder}/{domain}.txt")

        with open(list_filename, 'wb') as f:
            f.write(b'\n'.join(self.start_urls[0].encode('utf-8')))
            for page in result['pages']:
                f.write(b'\n')
                f.write(page.encode('utf-8'))
        print(result)

    @classmethod
    def f(self, q, url, found_pages, n, max_pages, save_pages, output_folder):
        try:
            runner = CrawlerRunner()
            deferred = runner.crawl(MySpider, url, found_pages, n=3, max_pages=10, save_pages=False)
            deferred.addBoth(lambda _: reactor.stop())
            reactor.run()
            q.put(found_pages)
        except Exception as e:
            q.put(e)

    @classmethod
    def runme(self, url, found_pages, n=3, max_pages=10, save_pages=False, output_folder = 'pages'):
        q = Queue()
        p = Process(target=MySpider.f, args=(q, url, found_pages, n, max_pages, save_pages, output_folder))
        p.start()
        result = q.get()
        p.join()
        # print("----")
        # print(result)
        # print("----")
        return result

        # runner = CrawlerRunner()
        # d = runner.crawl(MySpider, url, found_pages, n=3, max_pages=10, save_pages=False)
        # d.addBoth(lambda _: reactor.stop())
        # reactor.run()
        # return found_pages

# Usage:
# Run the spider using the following command:
# scrapy runspider my_scraper.py -a url=https://surveyjs.io/documentation -a n=3 -a max_pages=10 -a save_pages=False --nolog

if __name__ == "__main__":
    from scrapy.crawler import CrawlerProcess
    url = 'https://surveyjs.io/documentation'
    found_pages = set()
    # runner = CrawlerRunner()
    # d = runner.crawl(MySpider, url, found_pages)
    # d.addBoth(lambda _: reactor.stop())
    # reactor.run()
    found_pages = MySpider.runme(url, found_pages)
    print(found_pages)