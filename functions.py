import json
import ast
from typing import List, Dict, Union

def parse_maybe_json_blob(blob: str) -> Union[Dict, List, None]:
    """
    Try to turn `blob` into a Python object:
    - First via json.loads
    - Then, if that fails, via ast.literal_eval
    Returns dict, list, or None if both fail.
    """
    # 1) strip wrapping quotes if it looks doubly quoted
    if blob.startswith('"') and blob.endswith('"'):
        blob = blob[1:-1]

    # 2) try normal JSON
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        pass

    # 3) try literal_eval for Python‐style literals
    try:
        val = ast.literal_eval(blob)
        # if that gives us a str again, try json.loads one more time
        if isinstance(val, str):
            return json.loads(val)
        return val
    except Exception:
        return None

def combine_blobs(raw_blobs: List[str]) -> List[Dict]:
    combined: List[Dict] = []
    for i, blob in enumerate(raw_blobs):
        obj = parse_maybe_json_blob(blob)
        if obj is None:
            print(f"⚠️ Skipping blob #{i}: not valid JSON or literal")
            continue

        if isinstance(obj, dict):
            combined.append(obj)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict):
                    combined.append(item)
                else:
                    print(f"⚠️ Skipping non‐dict in list from blob #{i}: {item}")
        else:
            print(f"⚠️ Blob #{i} parsed to {type(obj)}, skipping")

    return combined
