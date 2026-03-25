
import requests
import urllib.parse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (UltimateFantasyLegends; admin@example.com)",
}

url = "https://upload.wikimedia.org/wikipedia/commons/c/c4/%28%EC%B6%94%EA%BE%B8%EB%AF%B8%29_%27%EC%9A%B8%EC%82%B0_%ED%95%A9%EB%A5%98%27_%EA%B9%80%EC%98%81%EA%B6%8C.jpg"

def test_api(filename):
    print(f"Testing Filename: {filename}")
    api_url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": f"File:{filename}",
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json"
    }
    r = requests.get(api_url, params=params, timeout=10, headers=HEADERS)
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Data: {data}")
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        if "imageinfo" in page:
            direct_url = page['imageinfo'][0]['url']
            print(f"FOUND URL: {direct_url}")
            
            headers_list = [
                {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
                {"User-Agent": "UltimateFantasyLegends/1.0 (admin@example.com) requests/2.26.0"},
                {"User-Agent": "Mozilla/5.0", "Referer": "https://www.google.com/"},
                {"User-Agent": "Mozilla/5.0", "Referer": ""},
            ]
            
            for i, h in enumerate(headers_list):
                print(f"Test {i+1} with headers: {h}")
                try:
                    r = requests.get(direct_url, timeout=10, headers=h)
                    print(f"  Status: {r.status_code}")
                    if r.status_code == 200:
                        print(f"  SUCCESS! Size: {len(r.content)}")
                except Exception as e:
                    print(f"  Error: {e}")
        else:
            print("NOT FOUND in this page")

filename_raw = url.split('/')[-1]
test_api(filename_raw)
test_api(urllib.parse.unquote(filename_raw))
