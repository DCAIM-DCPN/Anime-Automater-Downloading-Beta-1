import requests
import time

class TorBoxClient:
    BASE_URL = "https://api.torbox.app/v1/api"

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

    def check_cached(self, magnet_link):
        url = f"{self.BASE_URL}/torrents/checkcached"
        params = {"hash": magnet_link} # Torbox checkcached accepts magnet or hash
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        return None

    def add_torrent(self, magnet_link):
        url = f"{self.BASE_URL}/torrents/createtorrent"
        # Using simple form-data (application/x-www-form-urlencoded) as it also works
        # and might be more robust for simple string parameters.
        data = {
            "magnet": magnet_link
        }
        response = requests.post(url, headers=self.headers, data=data)
        if response.status_code != 200:
            print(f"[!] TorBox API Error: {response.status_code} - {response.text}")
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
            "token": self.api_key, # Explicitly adding token as some endpoints require it in params
            "torrent_id": torrent_id
        }
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                # TorBox returns the download link in the 'data' field.
                # If it's a single file, it's a string. If multiple, it might be a list.
                return data.get("data")
        else:
            print(f"[!] requestdl error: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    # Test with the provided API key (limited functionality without actual torrent)
    client = TorBoxClient("56195d14-8c39-48eb-90f4-546a1dc1fee5")
    print(client.get_torrent_status(0)) # Should return None or error
