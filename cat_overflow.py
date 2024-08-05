'''cat_overflow plugin'''
import os
import threading
import requests
from pydantic import BaseModel
from cat.mad_hatter.decorators import tool, plugin
from cat.log import log
from urllib.parse import urlparse

from .gh_repo_finder import GhRepoFinder
from .gh_easy_downloader import GhEasyDownloader
from .gh_api_downloader import GhApiRepoDownloader
from .my_spider import MySpider
from .page_downloader import PageDownloader

import subprocess

CAT_OVERFLOW_DIR = "/catoverflow"

class MySettings(BaseModel):
    ''' settings for the cat_overflow plugin '''
    search_on_web: bool = False
    search_on_stack_overflow: bool = False
    use_api: bool = False
    github_api_key: str = None
    scraping_depth: int = 3
    scraping_max_pages: int = 100
    use_chrome: bool = True
    use_firefox: bool = True    
    use_webkit: bool = False

@plugin
def settings_model():
    '''retrieve settings'''
    return MySettings

@plugin
def activated(plugin):
    subprocess.run(["playwright", "install"]) 
    subprocess.run(["playwright", "install-deps"]) 

def raw_file_url_exists(raw_file_url):
    '''
    Check if an url exists'''
    try:
        r = requests.get(raw_file_url, timeout=5)
        r.raise_for_status()  # Raise exception for any HTTP errors
        return r.status_code == 200
    except Exception:
        return False

def ingest_archive(cat, root, relpath, file, fallback = True, tool_input = '', branch_name = ''):
    print(f"ingesting file: {os.path.join(root, file)}")
    try:
        cat.rabbit_hole.ingest_file(cat, os.path.join(root, file))
    except ValueError as e:
        if fallback:
            raw_file_url = f"https://raw.githubusercontent.com/{tool_input}/{branch_name}/{relpath}/{file}"
            if raw_file_url_exists(raw_file_url):
                log.info(f"falling back to raw github url: {raw_file_url}")
                cat.rabbit_hole.ingest_file(cat, raw_file_url)
            else:
                log.error(f"raw github url IS WRONG!!!: {raw_file_url}")
        else:
            raise e

def run_ingestion(cat, folder, fallback = True, tool_input = '', branch_name = ''):
    ingestion_threads = []

    for root, dirs, files in os.walk(folder):
        for file in files:
            relpath = f"{root.replace(folder, '')}"[1:]
            relpath = ''.join((relpath, '/'))
            relpath = '/'.join(relpath.split('/')[1:])[:-1]
            t = threading.Thread(target=ingest_archive, args=(cat, root, relpath, file, fallback, tool_input, branch_name))
            ingestion_threads.append(t)

    log.info(f"the number of ingestion threads is: {len(ingestion_threads)}")

    thread_count = len(ingestion_threads)
    for t in ingestion_threads:
        t.start()
        t.join()
    
    return thread_count

@tool(examples=[
    "@getcode cheshirecat", 
    "@getcode fastapi", 
    "@getcode react", 
    "@getcode angularjs"], return_direct=True)
def get_code(tool_input, cat):
    '''
    Download the code library sources from github and scrape stack overflow pages about that library. 
    Input must be prepended with @getcode followed by the library name
    
    '''

    settings = cat.mad_hatter.get_plugin().load_settings()
    github_key = None if 'github_api_key' not in settings else settings['github_api_key'].strip()
    use_api = False if 'use_api' not in settings else settings['use_api'] is True
    search_on_web = False if 'search_on_web' not in settings else settings['search_on_web'] is True
    search_on_stack_overflow = False if 'search_on_stack_overflow' not in settings else settings['search_on_stack_overflow'] is True
    log.info("*" * 80)
    log.info(f"CAT OVERFLOW => settings: {settings}")
    log.info("*" * 80)

    msg = f'''
    {'*' * 80}
    * Cat Overfl0w plugin: start searching for repository: {tool_input}
    {'*' * 80}
    * current settings:
    * use_api: {str(use_api)}
    * search_on_web: {str(search_on_web)}
    * search_on_stack_overflow: {str(search_on_stack_overflow)}
    {'*' * 80}                                
    '''
    cat.send_ws_message(content=msg, msg_type="chat")

    gh = GhRepoFinder(github_key=github_key)
    search_results = gh.find_repo(tool_input)

    log.info("*" * 80)
    log.info(f"CAT OVERFLOW => search_results: {search_results}")
    log.info("*" * 80)

    if search_results is None or len(search_results) == 0:
        content_msg = f'Sorry I was unable to find any repository with the key: {tool_input}'
        return content_msg

    if len(search_results) == 1:
        prefix = "Start downloading repository:"
        repository_name = search_results[0]['name']
        repository_url = search_results[0]['url']
        output_folder = f"{CAT_OVERFLOW_DIR}/repositories"

        msg = f'''
        {prefix}

        name: {repository_name}'
        url: {repository_url}'
        '''
        
        cat.send_ws_message(content=msg, msg_type="chat")
        log.info(msg)
        msg = f'output_directory: {output_folder}'
        #cat.send_ws_message(content=msg, msg_type="chat")
        log.info(msg)

        if github_key is not None and use_api is True:
            #raise ValueError("Not implemented")
            gh_repo_downloader = GhApiRepoDownloader(key = github_key, name = repository_name, output_folder = output_folder)
        else:
            gh_repo_downloader = GhEasyDownloader(name = repository_name, output_folder = output_folder)

        download_result = gh_repo_downloader.download_files_from_repo()
        log.info(f"download result: {download_result}")

        extract_result = gh_repo_downloader.extract_archive(download_result)
        branch_name = extract_result['branch']
        extraction_folder = extract_result['extraction_folder']

        cat.send_ws_message(content="ingesting library archive has <b>started</b>.", msg_type="chat")
        
        thread_count = run_ingestion(cat, output_folder, True, tool_input, branch_name)
    
        ingestion_finished_msg = "ingesting library archive has <b>finished</b>."

        cat.send_ws_message(content=ingestion_finished_msg, msg_type="chat")

        return f"All files have been ingested using {thread_count} threads, Miao!"

    else:
        prefix = "I found the following libraries on github:"

        if search_results:
            for dict_item in search_results:
                for key in dict_item:
                    log.info(dict_item[key])

            prompt = f'''
            Given the following python dictionary:
                    
            {search_results}

            please output it as an ordered list.
            Be sure to include the name of the library, and the corresponding url of the library. 
            with the following sentence before: {prefix}
            Always use markdown syntax to format your output.

            '''
            #log.info("prompt for llm:")
            #log.info(prompt)
            return cat.llm(prompt)


def retrieve_contents(page_urls):     
    output_folder = f"{CAT_OVERFLOW_DIR}/html_pages"
    downloader = PageDownloader(output_folder=output_folder, page_urls=page_urls)
    result = downloader.save_pages()
    cat.send_ws_message(content=result, msg_type="chat")

@tool(examples=[
    "@getcodedoc https://cheshire-cat-ai.github.io/docs/", 
    "@getcodedoc https://fastapi.tiangolo.com/", 
    "@getcodedoc https://it.legacy.reactjs.org/", 
    "@getcodedoc https://vuejs.org/"], return_direct=True)
def get_code_documentation(tool_input, cat):
    '''
    Scrape an url and find all pages about a library.
    Input must be prepended with @getcodedoc followed by the site url
    '''
    settings = cat.mad_hatter.get_plugin().load_settings()
    print(settings)
    max_pages = settings['scraping_max_pages']
    max_depth = settings['scraping_depth']
    use_chrome = True if 'use_chrome' not in settings else settings['use_chrome'] is True
    use_firefox = False if 'use_firefox' not in settings else settings['use_firefox'] is True
    use_webkit = False if 'use_webkit' not in settings else settings['use_webkit'] is True

    msg = f'''
    {'*' * 80}
    * Cat Overfl0w plugin: get documentation: {tool_input}
    {'*' * 80}
    * current settings:
    * max_pages: {str(max_pages)}
    * max_depth: {str(max_depth)}
    * use_chrome: {str(use_chrome)}
    * use_firefox: {str(use_firefox)}
    * use_webkit: {str(use_webkit)}
    {'*' * 80}                                
    '''
    cat.send_ws_message(content=msg, msg_type="chat")

    cat.send_ws_message(content=f"Start Scraping url: <b>{tool_input}</b>", msg_type="chat")
    domain = urlparse(tool_input).netloc
    output_folder = f"{CAT_OVERFLOW_DIR}/html_pages/{domain}"
    os.makedirs(output_folder, exist_ok=True)
    found_pages = MySpider.runme(tool_input, set(), n=max_depth, max_pages=max_pages, save_pages=False, output_folder=output_folder)
    
    content = "Scraping ended. These are the results:\n"
    output = []
    for page in found_pages:
        output.append(page)
    content += "\n".join(output)
    cat.send_ws_message(content=content, msg_type="chat")

    downloader = PageDownloader(output_folder=output_folder, page_urls=output, use_chrome=use_chrome, use_firefox=use_firefox, use_webkit=use_webkit)
    #result = asyncio.run(downloader.save_pages())
    result = downloader.save_pages()
    log.info(result)

    cat.send_ws_message(content=result, msg_type="chat")

    cat.send_ws_message(content="Page Download ended", msg_type="chat")

    cat.send_ws_message(content="ingesting document pages has <b>started</b>.", msg_type="chat")
    
    thread_count = run_ingestion(cat, output_folder, False)

    ingestion_finished_msg = "ingesting document pages has <b>finished</b>."

    cat.send_ws_message(content=ingestion_finished_msg, msg_type="chat")

    return f"All files have been ingested using {thread_count} threads, Miao!"
