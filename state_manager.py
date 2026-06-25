import json
import os

class StateManager:
    def __init__(self, state_file='state.json'):
        self.state_file = state_file
        self.state = self.load_state()

    def load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            "last_run_anime": None,
            "processed_torrents": [],
            "downloaded_files": []
        }

    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=4)

    def add_processed_torrent(self, torrent_info):
        self.state["processed_torrents"].append(torrent_info)
        self.save_state()

    def add_downloaded_file(self, file_identifier):
        if file_identifier not in self.state["downloaded_files"]:
            self.state["downloaded_files"].append(file_identifier)
            self.save_state()

    def set_last_run_anime(self, anime_title):
        self.state["last_run_anime"] = anime_title
        self.save_state()

    def is_file_processed(self, file_identifier):
        return file_identifier in self.state["downloaded_files"]

