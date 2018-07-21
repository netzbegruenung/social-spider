import requests
import json
from pprint import pprint
import re
import sys

def decode(s):
    return s.replace("\\'", "'").replace("\\\\\"", "\\\"")

def scrapeInstagramData(username):
    url = "https://www.instagram.com/" + username
    r = requests.get(url)
    
    s = str(r.content)
    part1 = """<script type="text/javascript">window._sharedData = """
    part2 = """;</script>"""
    pattern = part1 + "(.*?)" + part2
    result = re.search(pattern, s)
    if result:
        decoded = decode(result[1])
        data = json.loads(decoded)
        data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"] = "----"
        return data["entry_data"]["ProfilePage"][0]["graphql"]["user"]
    else:
        print("No data found for", username, file=sys.stderr)
        
def scrapeFacebookLikes(username):
    url = "https://www.facebook.com/" + username
    r = requests.get(url)
    
    s = str(r.content)
    
    pattern = "Gef&#xe4;llt ([\d\.]+) Mal"
    result = re.search(pattern, s)
    if result:
        return int(result[1].replace(".", ""))
    else:
        print("No data found for", username, file=sys.stderr)
        return 0

if __name__ == '__main__':
    pprint(scrapeInstagramData("die_gruenen"))
    print(scrapeFacebookLikes("B90DieGruenen"))
