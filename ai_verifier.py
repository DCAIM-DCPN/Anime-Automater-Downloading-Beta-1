import json
import os

class AIVerifier:
    def __init__(self, state_manager):
        self.state_manager = state_manager

    def is_duplicate(self, file_identifier: str) -> bool:
        return self.state_manager.is_file_processed(file_identifier)

    def add_processed_file(self, file_identifier: str):
        self.state_manager.add_downloaded_file(file_identifier)

    def generate_file_identifier(self, anime_title: str, filename: str, file_size: str) -> str:
        # A simple identifier can be a combination of anime title, filename, and size.
        # For more robust deduplication, one might use file hashes.
        return f"{anime_title}_{filename}_{file_size}"
