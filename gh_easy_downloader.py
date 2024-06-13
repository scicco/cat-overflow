"""This class is used to download a repository from GitHub without any authentication"""
#import pdb
import os
import zipfile
import requests
from cat.log import log
from .base_downloader import BaseDownloader

# https://docs.github.com/en/search-github/github-code-search/understanding-github-code-search-syntax#query-for-an-exact-match
class GhEasyDownloader(BaseDownloader):
    """Download a repository from GitHub without any authentication"""

    def __init__(self, name, output_folder):
        self.repository_name = name
        self.output_directory = output_folder

        #pdb.set_trace()
        archive_path = f"{self.output_directory}/{self.repository_name.split('/')[0]}"
        if not os.path.exists(archive_path):
            log.info(f"creating output directory: {archive_path}")
            os.makedirs(archive_path, exist_ok=True)
        else:
            log.info(f"output directory already exists: {archive_path}")


    # download zip archive
    def _download_zip_archive(self, branch):
        url = f'https://github.com/{self.repository_name}/archive/refs/heads/{branch}.zip'
        try:
            r = requests.get(url, stream=True)
            r.raise_for_status()  # Raise exception for any HTTP errors
            archive_path = f"{self.output_directory}/{self.repository_name.split('/')[0]}"
            file_path = f"{archive_path}/{self.repository_name.split('/')[-1]}.zip"
            log.info(f"writing file in: {file_path}")
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=16*1024):
                    f.write(chunk)
            f.close()
            log.info(f'archive from branch {branch} downloaded successfully')
            return True
        except requests.exceptions.RequestException as e:
            log.error(f"Error occurred: {e}")
            return False

    def download_files_from_repo(self):
        """download files from repo"""
        try:
            #pdb.set_trace()
            result = True
            if self._download_zip_archive(branch='main'):
                branch = 'main'
            elif self._download_zip_archive(branch='master'):
                branch = 'master'
            elif self._download_zip_archive(branch='latest'):
                branch = 'latest'
            else:
                result = False
            log.info(f"download result: {result}")
            file_path = f"{self.output_directory}/{self.repository_name.split('/')[0]}/{self.repository_name.split('/')[-1]}.zip"
            return {"result": result, "path": file_path, "branch": branch}
        except requests.exceptions.RequestException:
            pass

    def extract_archive(self, result):
        """extract previously downloaded archive"""

        if result['result'] is True:
            log.info(f"start extracting archive: {result['path']}")
            archive_path = result['path']
            branch_name = result['branch']
            extraction_folder = f"{self.output_directory}/{self.repository_name.split('/')[0]}/{self.repository_name.split('/')[-1]}"
            if os.path.exists(archive_path):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    os.makedirs(extraction_folder, exist_ok=True)
                    zip_ref.extractall(extraction_folder)
                log.info(f"archive extracted successfully to {extraction_folder}")
            else:
                pass
            return {
                "result": result['result'], 
                "path": result['path'], 
                "branch": branch_name, 
                "extraction_folder": extraction_folder
            }
        else:
            message = 'Something went wrong during archive download'
            log.error(message)
            raise Exception(message)


# Example usage
#repository_name = "repository_name"
#output_directory = "output_directory"

#downloader = GhRepoDownloader(auth, repository_name, output_directory)
#downloader.download_files_from_repo()

if __name__ == "__main__":
    # Input repository name
    #REPOSITORY_NAME = input("Enter the name of the library: ")
    REPOSITORY_NAME = 'cheshire-cat-ai/docs'
    OUTPUT_FOLDER = "output"

    downloader = GhEasyDownloader(REPOSITORY_NAME, OUTPUT_FOLDER)
    result_value = downloader.download_files_from_repo()
    print(result_value)
