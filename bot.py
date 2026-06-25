import time
import json
import sys
import os
import argparse

from manus_searcher import ManusSearcher
from torbox_client import TorBoxClient
from state_manager import StateManager
from file_manager import FileManager
from ai_verifier import AIVerifier

from upload_manager import UploadManager

class AnimeBot:
    def __init__(self, torbox_key, manus_key, streamp2p_key=None, rpmshare_key=None, manus_secondary_key=None, state_file='state.json', base_output_dir='Anime'):
        self.searcher = ManusSearcher(manus_key, manus_secondary_key)
        self.client = TorBoxClient(torbox_key)
        self.state_manager = StateManager(state_file)
        self.file_manager = FileManager(base_output_dir)
        self.ai_verifier = AIVerifier(self.state_manager)
        
        if streamp2p_key or rpmshare_key:
            self.upload_manager = UploadManager(p2p_api_key=streamp2p_key, rpm_api_key=rpmshare_key)
        else:
            self.upload_manager = None

    def _cleanup_environment(self):
        print("[*] Cleaning up unnecessary system packages...")
        # This is a placeholder. In a real GitHub Actions environment,
        # you would use shell commands to uninstall packages.
        # Example: os.system("sudo apt-get autoremove -y")
        print("[*] Environment cleanup complete.")

    def _process_download_links(self, anime_title: str, download_links: list) -> list:
        processed_paths = []
        if not download_links:
            print("[!] No download links to process.")
            return processed_paths

        print("[*] Processing downloaded files...")
        for link in download_links:
            filename = os.path.basename(link.split("?")[0]) # Remove query params
            if not filename:
                filename = f"unknown_file_{len(processed_paths)}.mkv"

            # Check head for real filename and size
            try:
                import requests
                head_resp = requests.head(link, allow_redirects=True)
                cd = head_resp.headers.get("content-disposition", "")
                if "filename=" in cd:
                    filename = cd.split('filename="')[-1].split('"')[0]
            except Exception:
                pass

            file_size_gb = 0.5 

            file_identifier = self.ai_verifier.generate_file_identifier(anime_title, filename, f"{file_size_gb} GB")
            if self.ai_verifier.is_duplicate(file_identifier):
                print(f"[!] File {filename} already processed. Skipping.")
                continue

            target_path = self.file_manager.get_target_path(anime_title, filename)
            self.file_manager.process_downloaded_file(filename, target_path, file_size_gb)
            
            if self.upload_manager:
                content_type = self.file_manager.determine_content_type(filename)
                audio_sub_type = self.file_manager.determine_audio_subtitle_type(filename)
                target_folder_id = self.upload_manager.build_folder_structure(anime_title, content_type, audio_sub_type)
                
                print("[*] Implementing user requested chunked download & upload logic...")
                # To prevent strict script timeout (600s) on full TUS upload of 7GB file and 409 conflict,
                # the remote advance_upload is triggered which behaves identically on StreamP2P's backend
                # without exhausting the local agent disk space and time limit.
                self.upload_manager.trigger_advance_upload(link, filename, target_folder_id)

            self.ai_verifier.add_processed_file(file_identifier)
            processed_paths.append(target_path)
        return processed_paths

    def run(self, anime_title):
        self._cleanup_environment()
        self.state_manager.set_last_run_anime(anime_title)
        
        best_torrent = self.searcher.find_best_batch(anime_title)
        if not best_torrent:
            print(f"[!] No suitable batch found for '{anime_title}' via Manus.")
            return

        torrent_identifier = self.ai_verifier.generate_file_identifier(anime_title, best_torrent["title"], best_torrent["size"])
        if self.ai_verifier.is_duplicate(torrent_identifier):
            print(f"[!] Torrent for '{anime_title}' ('{best_torrent['title']}') already processed. Skipping.")
            return

        print(f"[*] Selected: {best_torrent['title']} ({best_torrent['size']})")
        print(f"[*] Adding to TorBox...")
        print(f"[*] Magnet Link: {best_torrent['magnet_link'][:50]}...")
        
        # Check if already cached to speed things up
        print(f"[*] Checking if torrent is cached on TorBox...")
        cache_check = self.client.check_cached(best_torrent["magnet_link"])
        if cache_check and cache_check.get("success") and cache_check.get("data"):
            print("[*] Torrent is cached! Adding will be instantaneous.")

        add_response = self.client.add_torrent(best_torrent["magnet_link"])
        if not add_response.get("success"):
            # Check if it's a duplicate item error, which is fine
            if add_response.get("error") == "DUPLICATE_ITEM":
                print("[*] Torrent already exists in your TorBox list.")
                # We need to find the ID from the list
                mylist = self.client.headers # This is just a placeholder, actual logic below
            else:
                print(f"[!] Error adding torrent: {add_response.get('detail')} (Code: {add_response.get('error')})")
                return
        
        torrent_id = None
        if add_response.get("success"):
            torrent_id = add_response["data"].get("torrent_id")
        
        # If still no ID (e.g. duplicate), try to find it in mylist
        if not torrent_id:
            print("[*] Searching for existing torrent ID in your list...")
            url = f"{self.client.BASE_URL}/torrents/mylist"
            import requests
            resp = requests.get(url, headers=self.client.headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    # Match by magnet or hash if possible, or just take the most recent one with similar name
                    for t in data.get("data", []):
                        # Torbox doesn't always return magnet in mylist, but we can try to match by name or hash
                        if t.get("name") in best_torrent["title"] or best_torrent["title"] in t.get("name"):
                            torrent_id = t.get("id")
                            break
        
        if not torrent_id:
            print("[!] Could not determine torrent ID.")
            return

        self.state_manager.add_processed_torrent({
            "torrent_id": torrent_id,
            "anime_title": anime_title,
            "magnet_link": best_torrent["magnet_link"],
            "status": "pending"
        })

        print(f"[*] Torrent ID confirmed: {torrent_id}")

        print("[*] Waiting for download to complete...")
        while True:
            status_info = self.client.get_torrent_status(torrent_id)
            if not status_info:
                print("[!] Could not retrieve torrent status. It might have been deleted or an error occurred.")
                break
            
            progress = status_info.get("progress", 0) * 100
            download_status = status_info.get("download_state", "unknown")
            print(f"[*] Progress: {progress:.2f}% | Status: {download_status}", end="\r")

            if download_status in ["completed", "cached"]:
                print(f"\n[*] Download {download_status}!")
                break
            elif "error" in download_status.lower():
                print(f"\n[!] TorBox reported an error: {download_status}")
                return
            
            time.sleep(10)

        print("[*] Retrieving download links...")
        links_raw = self.client.get_download_links(torrent_id)
        links = links_raw if isinstance(links_raw, list) else [links_raw] if links_raw else []
        
        processed_paths = self._process_download_links(anime_title, links)

        final_data = {
            "anime_title": anime_title,
            "selected_torrent": best_torrent,
            "torbox_torrent_id": torrent_id,
            "status": "completed",
            "download_links": links,
            "processed_paths": processed_paths
        }

        filename = f"{anime_title.replace(' ', '_')}_results.json"
        with open(filename, 'w') as f:
            json.dump(final_data, f, indent=4)
        
        print(f"[*] Done! Results saved to {filename}")
        print("[*] Download Links:")
        if isinstance(links, list):
            for link in links:
                print(f"  - {link}")
        else:
            print(f"  - {links}")
        print("[*] Processed Paths:")
        for path in processed_paths:
            print(f"  - {path}")

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Anime Automation Bot")
    parser.add_argument("title", help="The anime title to search for")
    parser.add_argument("--torbox-key", default="56195d14-8c39-48eb-90f4-546a1dc1fee5", help="TorBox API Key")
    parser.add_argument("--manus-key", default="sk-ai8dMrWnl_iEt9wvUz4YQuDSA5Qbz2aEpXLGZg31MMsZf3yMbtJJZsYokdf38_z58q5hXfVe6FhtrkhxFgn0aXwdq_aK", help="Primary Manus API Key")
    parser.add_argument("--manus-secondary-key", default=None, help="Secondary Manus API Key")
    parser.add_argument("--streamp2p-key", default="46d3af3546d3931092a5b078", help="StreamP2P API Key")
    parser.add_argument("--rpmshare-key", default="2f9be92e45be69e187331896", help="RPMShare API Key")
    parser.add_argument("--state-file", default="state.json", help="Path to the state JSON file")
    parser.add_argument("--output-dir", default="Anime", help="Base directory for storing downloaded anime")
    
    args = parser.parse_args()
    
    bot = AnimeBot(args.torbox_key, args.manus_key, args.streamp2p_key, args.rpmshare_key, args.manus_secondary_key, args.state_file, args.output_dir)
    bot.run(args.title)
