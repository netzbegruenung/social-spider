import facebook
from git import Repo
import os
import shutil
from ruamel import yaml
from pprint import pprint
import sys

# Git repo for our data
green_directory_repo = 'https://github.com/netzbegruenung/green-directory.git'

# folder in that repo that holds the data
green_direcory_data_path = 'data/countries/de'
green_directory_local_path = './cache/green-directory'
access_token = os.getenv("secret_facebook_access_token")


def get_green_directory():
    """
    Clones the source of website URLs, the green directory,
    into the local file system using git
    """
    if os.path.exists(green_directory_local_path):
        shutil.rmtree(green_directory_local_path, onerror=onerror)
    Repo.clone_from(green_directory_repo, green_directory_local_path)


def dir_entries():
    """
    Iterator over all data files in the cloned green directory
    """
    path = os.path.join(green_directory_local_path, green_direcory_data_path)
    for root, dirs, files in os.walk(path):
        for fname in files:

            filepath = os.path.join(root, fname)
            if not filepath.endswith(".yaml"):
                continue

            with open(filepath, 'r') as yamlfile:
                for doc in yaml.load_all(yamlfile):
                    yield doc

                
def onerror(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def main():
    get_green_directory()
    if not access_token:
        print("No access token found", file=sys.stderr)
    graph = facebook.GraphAPI(access_token=access_token)
    pprint(graph.get_object("B90DieGruenen", fields="fan_count,username,verification_status,website"))


if __name__ == "__main__":
    main()
