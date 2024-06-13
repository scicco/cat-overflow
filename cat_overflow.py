'''cat_overflow plugin'''
import os
import threading
import requests
from pydantic import BaseModel
from cat.mad_hatter.decorators import tool, plugin
from cat.log import log

from .gh_repo_finder import GhRepoFinder
from .gh_easy_downloader import GhEasyDownloader
from .gh_api_downloader import GhApiRepoDownloader

CAT_OVERFLOW_DIR = "/catoverflow"

class MySettings(BaseModel):
    ''' settings for the cat_overflow plugin '''
    search_on_web: bool = False
    search_on_stack_overflow: bool = False
    use_api: bool = False
    github_api_key: str = None

@plugin
def settings_model():
    '''retrieve settings'''
    return MySettings

def raw_file_url_exists(raw_file_url):
    '''
    Check if an url exists'''
    try:
        r = requests.get(raw_file_url, timeout=5)
        r.raise_for_status()  # Raise exception for any HTTP errors
        return r.status_code == 200
    except Exception:
        return False

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

        def ingest_archive(cat, tool_input, root, relpath, file, branch_name):
            print(f"ingesting file: {os.path.join(root, file)}")
            try:
                cat.rabbit_hole.ingest_file(cat, os.path.join(root, file))
            except ValueError:
                # if "Unsupported" in e.args[0]:
                #     pass
                # else:
                #     log.warning(f"error ingesting file: {os.path.join(root, file)}")

                raw_file_url = f"https://raw.githubusercontent.com/{tool_input}/{branch_name}/{relpath}/{file}"
                if raw_file_url_exists(raw_file_url):
                    log.info(f"falling back to raw github url: {raw_file_url}")
                    cat.rabbit_hole.ingest_file(cat, raw_file_url)
                else:
                    log.error(f"raw github url IS WRONG!!!: {raw_file_url}")

        ingestion_threads = []
        for root, dirs, files in os.walk(extraction_folder):
            for file in files:
                #log.info(f"adding file: {file} from {os.path.join(root, file)}")
                #relpath = os.path.relpath(extraction_folder, os.path.join(root, file))
                relpath = f"{root.replace(extraction_folder, '')}"[1:]
                relpath = ''.join((relpath, '/'))
                relpath = '/'.join(relpath.split('/')[1:])[:-1]
                #log.info(f"GINO adding extraction_folder: {extraction_folder} file: {file} root {root} from {os.path.join(root, file)} partial path: {os.path.join(root, file).replace(extraction_folder, '')} relpath: {relpath}")
                t = threading.Thread(target=ingest_archive, args=(cat, tool_input, root, relpath, file, branch_name))
                #t.start()
                ingestion_threads.append(t)

        log.info(f"the number of ingestion threads is: {len(ingestion_threads)}")

        cat.send_ws_message(content="ingesting library archive has <b>started</b>.", msg_type="chat")
        thread_count = len(ingestion_threads)
        for t in ingestion_threads:
            t.start()
            t.join()

        ingestion_finished_msg = "ingesting library archive has <b>finished</b>."

        cat.send_ws_message(content=ingestion_finished_msg, msg_type="chat")

        return f"All files have been ingested using {thread_count} threads"

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
