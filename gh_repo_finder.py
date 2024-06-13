"""This class is used to search a repository in GitHub with or without authentication"""
import requests
from cat.log import log
#import pdb
class GhRepoFinder:
    """This class is used to search a repository in GitHub with or without authentication"""

    def __init__(self, github_key = None) -> None:
        self.github_key = github_key

    def parse_raw_response(self, data):
        """Parse the raw response from GitHub search"""
        results = []
        try:
            for item in data['payload']['results']:
                name = item['hl_name']
                name = name.replace("<em>","")
                name = name.replace("</em>","")
                name = name.replace("&#x2F;","/")
                url = f"https://github.com/{name}"
                results.append({'name': name, 'url': url})
        except KeyError as error:
            log.error(f'wrong result data object: {data.keys()}')
            raise error
        return results

    def parse_api_response(self, data):
        """Parse the API response"""
        results = []
        try:
            for item in data['items']:
                name = item['full_name']
                url = item['html_url']
                results.append({'name': name, 'url': url})
        except KeyError as error:
            log.error(f'wrong result data object: {data.keys()}')
            raise error
        return results

    def search_library(self, library_name):
        """Search for a library in GitHub repositories"""

        if self.github_key in [None, '']:
            url = f"https://github.com/search?q={library_name}+in%3Aname&type=repositories"
        else:
            # GitHub API endpoint for repository search
            url = 'https://api.github.com/search/repositories'

        # Parameters for the search query
        params = {'q': library_name}

        try:
            # Sending GET request to GitHub API
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()  # Raise exception for any HTTP errors

            # Extracting JSON data from the response
            data = response.json()

            # Returning the search results
            return data
        except requests.exceptions.RequestException as e:
            log.error(f"Error occurred: {e}")
            return None

    def find_repo(self, repo_name):
        """find repo in github"""

        log.info(f"start search for: {repo_name}")
        api_response = self.search_library(repo_name)
        if self.github_key in [None, '']:
            search_results = self.parse_raw_response(api_response)
        else:
            search_results = self.parse_api_response(api_response)
        log.info(search_results)
        for dict_item in search_results:
            if dict_item['name'] == repo_name:
                result = []
                result.append(dict_item)
                return result
        log.error('this should not happen')
        return search_results

if __name__ == "__main__":
    # Input library name
    library_name = input("Enter the name of the library: ")

    # Searching GitHub for the library
    gh = GhRepoFinder()

    search_results = gh.find_repo(library_name)

    if search_results:
        print("Search results:")
        print(search_results)
        for dict_item in search_results:
            for key in dict_item:
                print(dict_item[key])
