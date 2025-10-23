import json, os
from typing import Dict, Any, List

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def list_datasets() -> List[Dict[str, Any]]:
    out = []
    
    # Scan root directory for JSON files
    for fn in os.listdir(DATA_DIR):
        if fn.endswith(".json"):
            try:
                with open(os.path.join(DATA_DIR, fn), "r") as f:
                    d = json.load(f)
                
                # Handle both formats: raw array or object with id/y
                if isinstance(d, list):
                    # Raw array format
                    series_id = fn[:-5]  # filename without .json
                    out.append({"id": series_id, "n": len(d), "category": "root"})
                elif isinstance(d, dict) and "y" in d:
                    # Object format with id and y
                    out.append({"id": d.get("id", fn[:-5]), "n": len(d.get("y", [])), "category": "root"})
            except Exception:
                pass
    
    # Scan subdirectories for JSON files
    for subdir in os.listdir(DATA_DIR):
        subdir_path = os.path.join(DATA_DIR, subdir)
        if os.path.isdir(subdir_path) and not subdir.startswith("_"):
            for fn in os.listdir(subdir_path):
                if fn.endswith(".json"):
                    try:
                        with open(os.path.join(subdir_path, fn), "r") as f:
                            d = json.load(f)
                        
                        # Handle both formats
                        if isinstance(d, list):
                            series_id = fn[:-5]
                            out.append({
                                "id": series_id, 
                                "n": len(d),
                                "category": subdir
                            })
                        elif isinstance(d, dict) and "y" in d:
                            out.append({
                                "id": d.get("id", fn[:-5]), 
                                "n": len(d.get("y", [])),
                                "category": subdir
                            })
                    except Exception:
                        pass
    
    return sorted(out, key=lambda x: (x.get("category", ""), x.get("id", "")))

def load_series(series_id: str) -> Dict[str, Any]:
    # First, try direct file in root directory
    path1 = os.path.join(DATA_DIR, f"{series_id}.json")
    if os.path.exists(path1):
        with open(path1, "r") as f:
            d = json.load(f)
            # Normalize format
            if isinstance(d, list):
                return {"id": series_id, "y": d}
            return d
    
    # Scan root directory for matching id inside files
    for fn in os.listdir(DATA_DIR):
        if fn.endswith(".json"):
            try:
                with open(os.path.join(DATA_DIR, fn), "r") as f:
                    d = json.load(f)
                if isinstance(d, dict) and d.get("id") == series_id:
                    return d
            except Exception:
                pass
    
    # Scan subdirectories for matching files
    for subdir in os.listdir(DATA_DIR):
        subdir_path = os.path.join(DATA_DIR, subdir)
        if os.path.isdir(subdir_path) and not subdir.startswith("_"):
            # Try direct file match
            path2 = os.path.join(subdir_path, f"{series_id}.json")
            if os.path.exists(path2):
                with open(path2, "r") as f:
                    d = json.load(f)
                    # Normalize format
                    if isinstance(d, list):
                        return {"id": series_id, "y": d}
                    return d
            
            # Scan for matching id inside files
            for fn in os.listdir(subdir_path):
                if fn.endswith(".json"):
                    try:
                        with open(os.path.join(subdir_path, fn), "r") as f:
                            d = json.load(f)
                        if isinstance(d, dict) and d.get("id") == series_id:
                            return d
                    except Exception:
                        pass
    
    raise FileNotFoundError(f"Series {series_id} not found in data/ or subdirectories")
