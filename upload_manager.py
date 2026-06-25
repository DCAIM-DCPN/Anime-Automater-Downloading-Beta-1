import os
import json
import requests

class UploadManager:
    def __init__(self, p2p_api_key=None, rpm_api_key=None):
        self.platforms = []
        if p2p_api_key:
            self.platforms.append({
                "name": "StreamP2P",
                "base_url": "https://streamp2p.com/api/v1",
                "headers": {"api-token": p2p_api_key, "Content-Type": "application/json"}
            })
        if rpm_api_key:
            self.platforms.append({
                "name": "RPMShare",
                "base_url": "https://rpmshare.com/api/v1",
                "headers": {"api-token": rpm_api_key, "Content-Type": "application/json"}
            })

    def get_or_create_folder(self, platform, name, parent_id=None):
        base_url = platform["base_url"]
        headers = platform["headers"]
        
        resp = requests.get(f"{base_url}/video/folder", headers=headers)
        if resp.status_code == 200:
            for f in resp.json():
                if f["name"].lower() == name.lower():
                    if parent_id and f.get("parentId") != parent_id:
                        continue
                    if not parent_id and f.get("parentId") is not None:
                        continue
                    return f["id"]
        
        payload = {"name": name}
        if parent_id:
            payload["folderId"] = parent_id
        resp = requests.post(f"{base_url}/video/folder", headers=headers, json=payload)
        if resp.status_code == 201:
            return resp.json()["id"]
        return None

    def build_folder_structure(self, anime_title, content_type, audio_sub_type):
        platform_folders = {}
        for platform in self.platforms:
            print(f"[*] Building folder structure on {platform['name']}: Anime/{anime_title}/{content_type}/{audio_sub_type}")
            anime_root = self.get_or_create_folder(platform, "Anime")
            title_folder = self.get_or_create_folder(platform, anime_title, anime_root)
            content_folder = self.get_or_create_folder(platform, content_type, title_folder)
            audio_folder = self.get_or_create_folder(platform, audio_sub_type, content_folder)
            platform_folders[platform["name"]] = audio_folder
            
        return platform_folders

    def trigger_advance_upload(self, download_link, filename, target_folders):
        results = {}
        for platform in self.platforms:
            p_name = platform["name"]
            print(f"[*] Triggering advance upload on {p_name} for robustness...")
            payload = {
                "url": download_link,
                "name": filename
            }
            
            # Add folderId if we successfully created/found one for this platform
            if p_name in target_folders and target_folders[p_name]:
                payload["folderId"] = target_folders[p_name]
                
            resp = requests.post(f"{platform['base_url']}/video/advance-upload", headers=platform["headers"], json=payload)
            if resp.status_code == 201:
                task_id = resp.json().get('id')
                print(f"[*] {p_name} advance upload created successfully. Task ID: {task_id}")
                results[p_name] = True
            else:
                print(f"[!] {p_name} advance upload failed: {resp.status_code} - {resp.text}")
                results[p_name] = False
                
        return results
