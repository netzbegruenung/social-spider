import requests
import json
from pprint import pprint
import re
import sys


def scrapeInstagramData(username):
    url = "https://www.instagram.com/" + username
    r = requests.get(url)
    
    s = str(r.content)
    part1 = """<script type="text/javascript">window._sharedData = """
    part2 = """;</script>"""
    pattern = part1 + "(.*?)" + part2
    print(pattern)
    result = re.search(pattern, s)
    if result:
        data = json.loads(result[1])
        data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"] = "----"
        return data["entry_data"]["ProfilePage"][0]["graphql"]["user"]
    else:
        print("No data found", file=sys.stderr)
        
def scrapeFacebookLikes(username):
    url = "https://www.facebook.com/" + username
    r = requests.get(url)
    
    s = str(r.content)
    
    pattern = "Gef&#xe4;llt ([\d\.]+) Mal"
    result = re.search(pattern, s)
    if result:
        return int(result[1].replace(".", ""))
    else:
        print("No data found", file=sys.stderr)

if __name__ == '__main__':
    pprint(scrapeInstagramData("die_gruenen"))
    print(scrapeFacebookLikes("B90DieGruenen"))
