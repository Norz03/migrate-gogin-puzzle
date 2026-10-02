"""Hashing utilities for manifest checksum generation."""
import hashlib
from typing import List

def generate_checksum(room_ids: List[int]) -> str:
    """Generates a SHA-256 hash of concatenated sorted room IDs."""
    sorted_ids = sorted(room_ids)
    concatenated = "".join(str(rid) for rid in sorted_ids)
    return hashlib.sha256(concatenated.encode('utf-8')).hexdigest()