import requests
import re
import sys


def scrape(username):
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
    print(scrape("GrueneStgt"))
