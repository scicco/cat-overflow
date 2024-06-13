"""This class is used to download a repository from GitHub API"""
import os
import threading
from github import Github, Auth
from cat.log import log
from .base_downloader import BaseDownloader
#import pdb

#https://docs.github.com/en/search-github/github-code-search/understanding-github-code-search-syntax#query-for-an-exact-match
class GhApiRepoDownloader(BaseDownloader):
    """Download a repository from GitHub API"""

    def __init__(self, name, output_folder, key = None):
        self.repository_name = name
        self.output_directory = output_folder
        self.auth_key = key

        # Authenticate with GitHub
        if self.auth_key is not None:
            auth = Auth.Token(self.auth_key)
            self.g = Github(auth=auth)
            # Access the repository
            self.repo = self.g.get_repo(self.repository_name)
        else:
            raise ValueError('No auth key provided')
        
        #pdb.set_trace()
        archive_path = f"{self.output_directory}/{self.repository_name.split('/')[0]}"
        if not os.path.exists(archive_path):
            log.info(f"creating output directory: {archive_path}")
            os.makedirs(archive_path, exist_ok=True)
        else:
            log.info(f"output directory already exists: {archive_path}")

    def _download_files_recursively(self, content_path = ""):
        # Retrieve the list of files and directories in the current directory
        #pdb.set_trace()
        os.makedirs(os.path.join(f"{self.output_directory}/{self.repo.full_name}", content_path), exist_ok=True)
        contents = []
        try:
            contents = self.repo.get_contents(content_path)
        except Exception as e:
            log.error(f"Error occurred: {e}")

        threads = []

        # Iterate through each file or directory
        for content in contents:
            # if os.path.exists(os.path.join(self.output_directory, content.name)):
            #   log.info(f"Skipping: {content.name}")
            #   continue
            if content.type == "file":
                try:
                    # Download the file
                    t = threading.Thread(target=self._download_file, kwargs={'file': content})
                    threads.append(t)
                except Exception as e:
                    log.info(f"Error occurred during download_file: {e}")
            elif content.type == "dir":
                # Recursively call the function for subdirectories
                if content_path != "":
                    next_path = content_path + "/" + content.name
                else:
                    next_path = content.name
                #log.info(f"next_path: {next_path}")
                t = threading.Thread(target=self._download_files_recursively, kwargs={'content_path': next_path})
                threads.append(t)

        for t in threads:
            t.start()
            t.join()
        return True

    # download file
    def _download_file(self, file):
        # Download the file
        content = file.decoded_content
        output_path = os.path.join(f"{self.output_directory}/{self.repo.full_name}", file.path)
        if not os.path.exists(output_path):
            with open(output_path, "wb") as f:
                f.write(content)
            log.info(f"Downloaded: {file.path}")
        else:
            log.info(f"Skipping: {file.path}")

    def download_files_from_repo(self):
        """download files from repo"""

        if self.auth_key is not None:
            result = self._download_files_recursively()
            file_path = f"{self.output_directory}/{self.repo.full_name}.zip"
            return {"result": result, "path": file_path, "branch": self.repo.default_branch}
        else:
            log.error('No auth key provided')
            raise ValueError('No auth key provided')

    def extract_archive(self, result):
        """extract previously downloaded archive"""

        if result['result'] is True:
            log.info(f"start extracting archive: {result['path']}")
            #archive_path = result['path']
            branch_name = result['branch']
            if self.auth_key is not None:
                extraction_folder = f"{self.output_directory}/{self.repo.full_name}"
            return { "result": result['result'], "path": result['path'], "branch": branch_name, "extraction_folder": extraction_folder}
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

    AUTH_KEY = 'somekey'
    downloader = GhApiRepoDownloader(AUTH_KEY, REPOSITORY_NAME, OUTPUT_FOLDER)
    result = downloader.download_files_from_repo()
    print(result)
