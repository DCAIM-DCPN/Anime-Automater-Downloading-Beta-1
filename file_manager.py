import os
import re

class FileManager:
    def __init__(self, base_output_dir="Anime"):
        self.base_output_dir = base_output_dir
        if not os.path.exists(self.base_output_dir):
            os.makedirs(self.base_output_dir)

    def create_anime_directory(self, anime_title: str) -> str:
        # Sanitize anime title for directory name
        sanitized_title = re.sub(r'[^a-zA-Z0-9_.-]', '_', anime_title)
        anime_dir = os.path.join(self.base_output_dir, sanitized_title)
        if not os.path.exists(anime_dir):
            os.makedirs(anime_dir)
        return anime_dir

    def determine_content_type(self, filename: str) -> str:
        filename_lower = filename.lower()
        if re.search(r'movie|film', filename_lower):
            return "Movies"
        elif re.search(r'ova|oav', filename_lower):
            return "OVAs"
        elif re.search(r'special| sp |sp[0-9]', filename_lower):
            return "Specials"
        elif re.search(r'extra|bonus|omake', filename_lower):
            return "Extras"
        else:
            return "Episodes"

    def determine_audio_subtitle_type(self, filename: str) -> str:
        filename_lower = filename.lower()
        if re.search(r'dub|dual audio|dual-audio', filename_lower):
            return "Dub"
        elif re.search(r'hardsub|h\.sub|hc|hard-sub', filename_lower):
            return "Hard_Sub"
        else:
            return "Soft_Sub" # Default to soft sub if no specific indicators

    def get_target_path(self, anime_title: str, filename: str) -> str:
        anime_base_dir = self.create_anime_directory(anime_title)
        content_type_dir = os.path.join(anime_base_dir, self.determine_content_type(filename))
        audio_sub_type_dir = os.path.join(content_type_dir, self.determine_audio_subtitle_type(filename))
        
        if not os.path.exists(audio_sub_type_dir):
            os.makedirs(audio_sub_type_dir)
            
        return os.path.join(audio_sub_type_dir, os.path.basename(filename))

    def process_downloaded_file(self, source_path: str, target_path: str, file_size_gb: float):
        # This function will simulate file processing. In a real scenario, it would
        # move/copy the file and handle chunking if necessary.
        print(f"[FileManager] Processing file: {os.path.basename(source_path)}")
        print(f"[FileManager] Moving/Copying to: {target_path}")
        if file_size_gb > 30:
            print(f"[FileManager] File size {file_size_gb}GB exceeds 30GB. Conceptual chunking would occur here.")
        # Simulate file creation for demonstration
        with open(target_path, 'w') as f:
            f.write(f"Simulated content for {os.path.basename(source_path)}")
        print(f"[FileManager] Successfully processed {os.path.basename(source_path)}")

