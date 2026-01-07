"""
Generate datasets.json file for static CDN hosting.
Uses the same logic as server/util.py list_datasets()
"""
import json
import os
import sys

# Add server directory to path to import util
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))
from util import list_datasets

def main():
    print("=" * 60)
    print("GENERATE DATASETS.JSON FOR CDN")
    print("=" * 60)
    
    # Get datasets using server logic
    print("📦 Loading datasets from data/ folder...")
    datasets = list_datasets()
    
    print(f"✅ Found {len(datasets)} datasets")
    
    # Write to datasets.json
    output_file = "datasets.json"
    with open(output_file, 'w') as f:
        json.dump(datasets, f, indent=2)
    
    print(f"✅ Generated {output_file}")
    print(f"📝 Sample datasets:")
    for ds in datasets[:3]:
        print(f"   - {ds['id']} (n={ds['n']}, category={ds['category']})")
    
    print(f"\n🌐 Next step: Upload to DigitalOcean with:")
    print(f"   python upload_datasets_json.py")

if __name__ == "__main__":
    main()
