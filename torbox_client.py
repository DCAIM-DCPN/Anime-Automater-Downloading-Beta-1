import requests
import time

class TorBoxClient:
    BASE_URL = "https://api.torbox.app/v1/api"

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

    def add_torrent(self, magnet_link):
        url = f"{self.BASE_URL}/torrents/createtorrent"
        data = {
            "magnet": magnet_link
        }
        response = requests.post(url, headers=self.headers, data=data)
        return response.json()

    def get_torrent_status(self, torrent_id):
        # Using mylist to find the specific torrent status
        url = f"{self.BASE_URL}/torrents/mylist"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                for torrent in data.get("data", []):
                    if torrent.get("id") == torrent_id:
                        return torrent
        return None

    def get_download_links(self, torrent_id):
        url = f"{self.BASE_URL}/torrents/requestdl"
        params = {
            "token": self.api_key,
            "torrent_id": torrent_id
        }
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                # The response structure might vary, usually it's a link or a list of links
                return data.get("data")
        return None

if __name__ == "__main__":
    # Test with the provided API key (limited functionality without actual torrent)
    client = TorBoxClient("56195d14-8c39-48eb-90f4-546a1dc1fee5")
    print(client.get_torrent_status(0)) # Should return None or error
