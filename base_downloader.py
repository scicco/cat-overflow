"""This class is the base class for downloading a repository from GitHub"""

class BaseDownloader:
    """This class is the base class for downloading a repository from GitHub"""

    def __init__(self, name, output_folder, key = None):
        self.key = key
        self.name = name
        self.output_folder = output_folder

    def download_files_from_repo(self):
        """download files from repo"""

        raise NotImplementedError

    def extract_archive(self, result):
        """extract previously downloaded archive"""

        raise NotImplementedError
