"""Wrapper for pushing data to the Go API."""
import requests
from typing import Dict, Any

class PuzzleAPIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8080"):
        self.base_url = base_url
        self.session = requests.Session()

    def sync_room(self, payload: Dict[str, Any]) -> bool:
        url = f"{self.base_url}/api/v1/sync"
        response = self.session.post(url, json=payload)
        return response.status_code == 202