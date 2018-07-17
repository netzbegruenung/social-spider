import facebook
from git import Repo
import os
import shutil
from ruamel import yaml
from pprint import pprint
import sys
import re
import twitter

# Git repo for our data
green_directory_repo = 'https://github.com/netzbegruenung/green-directory.git'

# folder in that repo that holds the data
green_direcory_data_path = 'data/countries/de'
green_directory_local_path = './cache/green-directory'
facebook_access_token = os.getenv("secret_facebook_access_token")
twitter_consumer_key = os.getenv("twitter_consumer_key")
twitter_consumer_secret = os.getenv("twitter_consumer_secret")
twitter_access_token_key = os.getenv("twitter_access_token_key")
twitter_access_token_secret = os.getenv("twitter_access_token_secret")


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
                for doc in yaml.load_all(yamlfile, Loader=yaml.Loader):
                    yield doc

                
def onerror(func, path, _):
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


def getFacebookName(url):
    if "/groups/" in url:
        return None
    if re.match(r".+-(\d)+", url):
        result = re.match(r".+-(\d+)", url).group(1)
        if len(result) < 10:
            print(url, "--", result, file=sys.stderr)
            return
        return result
    
    if url.split("/")[-1]:
        return url.split("/")[-1]
    
    elif url.split("/")[-2]:
        return url.split("/")[-2]

    
def getTwitterName(url):
    if url.split("/")[-1]:
        return url.split("/")[-1]
    elif url.split("/")[-2]:
        return url.split("/")[-2]


def main():
    get_green_directory()
    if not facebook_access_token:
        print("No access token found", file=sys.stderr)
        return
    
    twitterAPI = twitter.Api(consumer_key=twitter_consumer_key,
                      consumer_secret=twitter_consumer_secret,
                      access_token_key=twitter_access_token_key,
                      access_token_secret=twitter_access_token_secret)
    # user = twitterapi.GetUser(screen_name="die_gruenen")
    # pprint(user.AsDict())

    facebookGraphAPI = facebook.GraphAPI(access_token=facebook_access_token)
    # pprint(graph.get_object("B90DieGruenen", fields="fan_count,username,verification_status,website"))
    doc = []
    fbcount = 0
    twtcount = 0
    for entry in dir_entries():
        if not entry.get("urls"):
            continue
        for url in entry["urls"]:
            if url["type"] == "FACEBOOK":
                fbname = getFacebookName(url["url"])
                if fbname:
                    try:
                        fbdata = facebookGraphAPI.get_object(fbname, fields="fan_count,username,verification_status,website")
                    except Exception as e:
                        print("FACEBOOK ERROR for", url["url"], "--", fbname, file=sys.stderr)
                        print(e, file=sys.stderr)
                        continue
                    entry.update({"facebookData": fbdata, "facebookID": fbname})
                    print(fbname)
                    fbcount += 1

            elif url["type"] == "TWITTER":
                twtname = getTwitterName(url["url"])
                twtcount += 1
                try:
                    user = twitterAPI.GetUser(screen_name=twtname)
                    twtData = user.AsDict()
                except Exception as e:
                    print("TWITTER ERROR for", url["url"], "--", twtname, file=sys.stderr)
                    print(e, file=sys.stderr)
                    continue
                entry.update({"twitterData": twtData, "twitterName": twtname})
                print(twtname)

        doc.append(entry)
                    
    with open("result.yaml", "w") as f:
        yaml.dump_all(doc, f)
    print("facebook:", fbcount, "twitter:", twtcount)


if __name__ == "__main__":
    main()