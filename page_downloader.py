import asyncio
from playwright.async_api import async_playwright
import random
# import subprocess

class PageDownloader:
    """This class is the base class for downloading a page source using  Playwright library"""

    def __init__(self, output_folder, page_urls, use_chrome = True, use_firefox = True, use_webkit = False):
        self.page_urls = page_urls
        self.output_folder = output_folder
        self.use_chrome = use_chrome
        self.use_firefox = use_firefox
        self.use_webkit = use_webkit
        if not (self.use_chrome or self.use_firefox or self.use_webkit):
           raise Exception('please activate at least one browser engine')         
            
        # subprocess.run(["playwright", "install"]) 
        # subprocess.run(["playwright", "install-deps"]) 

    async def save_page(self, page_url, browser):
        page = await browser.new_page()
        await page.goto(page_url)
        await page.wait_for_load_state('networkidle')
        html = await page.content()
        #save html content into output folder
        with open(f"{self.output_folder}/{page_url.split('/')[-2]}.html", "w") as f:
            f.write(html)
        await page.close()

    def save_pages(self):
        #downloader = PageDownloader(output_folder=output_folder, page_urls=output, use_chrome=use_chrome, use_firefox=use_firefox, use_webkit=use_webkit)
        result = asyncio.run(self.launch_download())
        return result

    async def launch_download(self):
        """Download a repository from url"""
        async with async_playwright() as p:
            browsers = []
            if self.use_chrome:
                chromium = await p.chromium.launch()
                browsers.append(chromium)
            if self.use_firefox:
                firefox = await p.firefox.launch()
                browsers.append(firefox)
            if self.use_webkit:
                webkit = await p.webkit.launch()
                browsers.append(webkit)

            browser = random.choice(browsers)    
            for page_url in self.page_urls:
                await self.save_page(page_url, browser)
            return "all pages where saved"

if __name__ == "__main__":
    pages = ['https://surveyjs.io/documentation']
    output_folder = "./pages"
    downloader = PageDownloader(output_folder,  pages)
    result = downloader.save_pages()

    print(result)
