"""
Upload data/ folder JSON files to DigitalOcean Spaces
"""
import os
import boto3
from pathlib import Path

# DigitalOcean Spaces configuration
SPACE_NAME = 'feature-taxonomy-precomputed'
REGION = 'sfo3'
ENDPOINT = f'https://{REGION}.digitaloceanspaces.com'

def main():
    print("=" * 60)
    print("UPLOAD DATA FOLDER TO DIGITALOCEAN")
    print("=" * 60)
    print(f"Space: {SPACE_NAME}")
    print(f"Region: {REGION}")
    print("=" * 60)
    
    # Initialize client
    session = boto3.session.Session()
    client = session.client('s3',
        region_name=REGION,
        endpoint_url=ENDPOINT,
        aws_access_key_id=os.getenv('DIGITALOCEAN_SPACES_KEY'),
        aws_secret_access_key=os.getenv('DIGITALOCEAN_SPACES_SECRET')
    )
    
    data_dir = Path('data')
    if not data_dir.exists():
        print("❌ data/ folder not found")
        return
    
    # Upload all JSON files from data/ subdirectories
    uploaded = 0
    for json_file in data_dir.rglob('*.json'):
        # Get relative path (e.g., 'climate_awnd/climate_atl_awnd.json')
        rel_path = json_file.relative_to(data_dir.parent)
        s3_key = str(rel_path).replace('\\', '/')
        
        try:
            client.upload_file(
                str(json_file),
                SPACE_NAME,
                s3_key,
                ExtraArgs={
                    'ACL': 'public-read',
                    'ContentType': 'application/json'
                }
            )
            uploaded += 1
            if uploaded % 10 == 0:
                print(f"  Uploaded: {uploaded} files...")
        except Exception as e:
            print(f"❌ Failed to upload {json_file}: {e}")
    
    print(f"✅ Upload complete! Uploaded {uploaded} JSON files")
    print(f"\n🌐 Files accessible at:")
    print(f"   https://{SPACE_NAME}.{REGION}.cdn.digitaloceanspaces.com/data/{{category}}/{{dataset}}.json")

if __name__ == "__main__":
    main()
