import requests
from bs4 import BeautifulSoup
import urllib.parse

class NyaaScraper:
    BASE_URL = "https://nyaa.si"

    def search_anime(self, title):
        query = urllib.parse.quote(title)
        url = f"{self.BASE_URL}/?f=0&c=1_2&q={query}&s=seeders&o=desc"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error searching Nyaa.si: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        rows = soup.select('tr.success, tr.default, tr.danger')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 8:
                continue
                
            title_cell = cols[1].find_all('a')[-1]
            title_text = title_cell.get('title') or title_cell.text
            
            magnet_link = cols[2].find_all('a')[1]['href']
            size = cols[3].text
            seeders = int(cols[5].text)
            leechers = int(cols[6].text)
            
            results.append({
                "title": title_text,
                "magnet_link": magnet_link,
                "size": size,
                "seeders": seeders,
                "leechers": leechers
            })
            
        return results

    def select_best_torrent(self, results):
        if not results:
            return None
        # Since the search is already sorted by seeders, the first result is usually the best
        return results[0]

if __name__ == "__main__":
    scraper = NyaaScraper()
    results = scraper.search_anime("Spy x Family")
    best = scraper.select_best_torrent(results)
    if best:
        print(f"Found: {best['title']} ({best['size']}) with {best['seeders']} seeders.")
    else:
        print("No results found.")
