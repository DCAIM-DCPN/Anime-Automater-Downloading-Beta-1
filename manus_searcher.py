from manus_client import ManusClient
from nyaa_scraper import NyaaScraper

class ManusSearcher:
    def __init__(self, primary_key, secondary_key=None):
        self.primary_key = primary_key
        self.secondary_key = secondary_key
        self.client = ManusClient(primary_key)
        self.fallback_scraper = NyaaScraper()

    def find_best_batch(self, anime_title):
        prompt = (
            f"Search Nyaa.si and other reliable sources for the absolute best high-quality  releases of '{anime_title}'. "
            "Prioritize 1080p, Blu-ray (BD) quality, and complete series batches and if there is no batches Gather select episodes research and find out what the series has like if they have x numbe episodes movie names ovs etc once done with that search on nyaa.si for the magnet links make sure no duplicates are added please and thank you very much. "
            "Identify if it includes Movies, OVAs, or Specials. "
            "Return the result in structured JSON format with 'title', 'magnet_link', 'size', and 'content_type' (e.g., 'Series Batch')."
        )
        
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "magnet_link": {"type": "string"},
                "size": {"type": "string"},
                "content_type": {"type": "string"}
            },
            "required": ["title", "magnet_link", "size", "content_type"],
            "additionalProperties": False
        }
        
        print(f"[*] Asking Manus to find the best batch for '{anime_title}'...")
        try:
            task_id = self.client.create_task(prompt, schema)
            messages = self.client.wait_for_completion(task_id)
            result = self.client.get_structured_result(messages)
            return result
        except Exception as e:
            print(f"[!] Manus Search with primary key failed: {e}")
            if self.secondary_key:
                print("[*] Attempting with secondary Manus API key...")
                try:
                    self.client = ManusClient(self.secondary_key)
                    task_id = self.client.create_task(prompt, schema)
                    messages = self.client.wait_for_completion(task_id)
                    result = self.client.get_structured_result(messages)
                    return result
                except Exception as e2:
                    print(f"[!] Manus Search with secondary key failed: {e2}")
            
            print("[!] Falling back to NyaaScraper...")
            results = self.fallback_scraper.search_anime(anime_title)
            if results:
                best = self.fallback_scraper.select_best_torrent(results)
                if best:
                    return {
                        "title": best["title"],
                        "magnet_link": best["magnet_link"],
                        "size": best["size"],
                        "content_type": "Series Batch (Fallback)"
                    }
            return None

if __name__ == "__main__":
    # Test ManusSearcher
    API_KEY = "sk-ai8dMrWnl_iEt9wvUz4YQuDSA5Qbz2aEpXLGZg31MMsZf3yMbtJJZsYokdf38_z58q5hXfVe6FhtrkhxFgn0aXwdq_aK"
    searcher = ManusSearcher(API_KEY)
    result = searcher.find_best_batch("Anohana: The Flower We Saw That Day")
    print(f"[*] Result: {result}")
