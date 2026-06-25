import requests
import time
import json

class ManusClient:
    BASE_URL = "https://api.manus.ai/v2"

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "x-manus-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def create_task(self, prompt, structured_output_schema=None):
        url = f"{self.BASE_URL}/task.create"
        payload = {
            "message": {"content": prompt}
        }
        if structured_output_schema:
            payload["structured_output_schema"] = structured_output_schema
        
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code != 200:
            print(f"[!] API Error: {response.status_code} - {response.text}")
            response.raise_for_status()
        
        data = response.json()
        if "task_id" in data:
            return data["task_id"]
        elif "data" in data and "task_id" in data["data"]:
            return data["data"]["task_id"]
        else:
            print(f"[!] Unexpected response structure: {data}")
            raise Exception("Missing task_id in response")

    def list_messages(self, task_id):
        url = f"{self.BASE_URL}/task.listMessages"
        params = {"task_id": str(task_id), "order": "desc", "limit": 10}
        for _ in range(5):
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 404:
                print(f"[*] Task not found yet. Waiting...")
                time.sleep(2)
                continue
            if response.status_code != 200:
                print(f"[!] listMessages Error: {response.status_code} - {response.text}")
                response.raise_for_status()
            
            data = response.json()
            if "data" in data and "messages" in data["data"]:
                return data["data"]["messages"]
            elif "messages" in data:
                return data["messages"]
            else:
                print(f"[!] Unexpected listMessages response: {data}")
                return []
        
        response.raise_for_status()

    def wait_for_completion(self, task_id, timeout=600):
        print(f"[*] Polling task {task_id} for completion...")
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < timeout:
            messages = self.list_messages(task_id)
            # Find the latest status update
            current_status = None
            for msg in messages:
                if msg["type"] == "status_update":
                    current_status = msg["status_update"]["agent_status"]
                    break
            
            if current_status and current_status != last_status:
                print(f"[*] Task status changed: {current_status}")
                last_status = current_status

            if current_status == "stopped":
                print("[*] Task completed successfully.")
                return messages
            elif current_status == "error":
                error_msg = "Unknown error"
                for msg in messages:
                    if msg["type"] == "error_message":
                        error_msg = msg["error_message"].get("content", error_msg)
                        break
                raise Exception(f"Task failed: {error_msg}")
            elif current_status == "waiting":
                # Check what it's waiting for
                for msg in messages:
                    if msg["type"] == "status_update" and msg["status_update"]["agent_status"] == "waiting":
                        detail = msg["status_update"]["status_detail"]
                        print(f"[*] Task waiting for: {detail['waiting_for_event_type']} - {detail.get('waiting_description', '')}")
                        break
            
            time.sleep(20) # Increase sleep to save credits and avoid rate limits
        raise Exception("Task timed out after 10 minutes")

    def get_structured_result(self, messages):
        for msg in messages:
            if msg["type"] == "structured_output_result":
                result = msg["structured_output_result"]
                if result["success"]:
                    return result["value"]
                else:
                    raise Exception(f"Structured output failed: {result['error']}")
        return None

if __name__ == "__main__":
    # Test Manus API client
    API_KEY = "sk-ai8dMrWnl_iEt9wvUz4YQuDSA5Qbz2aEpXLGZg31MMsZf3yMbtJJZsYokdf38_z58q5hXfVe6FhtrkhxFgn0aXwdq_aK"
    client = ManusClient(API_KEY)
    
    prompt = "Search Nyaa.si for high-quality batch releases of 'Anohana: The Flower We Saw That Day'. Return the best magnet link."
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "magnet_link": {"type": "string"},
            "size": {"type": "string"}
        },
        "required": ["title", "magnet_link", "size"],
        "additionalProperties": False
    }
    
    try:
        task_id = client.create_task(prompt, schema)
        print(f"[*] Task created: {task_id}")
        messages = client.wait_for_completion(task_id)
        result = client.get_structured_result(messages)
        print(f"[*] Search Result: {result}")
    except Exception as e:
        print(f"[!] Error: {e}")
