"""
Upload datasets.json to DigitalOcean Spaces
"""
import os
import boto3
from botocore.exceptions import ClientError

# DigitalOcean Spaces configuration
SPACE_NAME = 'feature-taxonomy-precomputed'
REGION = 'sfo3'
ENDPOINT = f'https://{REGION}.digitaloceanspaces.com'

def main():
    print("=" * 60)
    print("UPLOAD DATASETS.JSON TO DIGITALOCEAN")
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
    
    # Check if datasets.json exists
    if not os.path.exists('datasets.json'):
        print("❌ datasets.json not found. Run generate_datasets_json.py first")
        return
    
    # Upload file
    print("🚀 Uploading datasets.json...")
    try:
        client.upload_file(
            'datasets.json',
            SPACE_NAME,
            'datasets.json',
            ExtraArgs={
                'ACL': 'public-read',
                'ContentType': 'application/json'
            }
        )
        print("✅ Upload successful!")
        print(f"\n🌐 File accessible at:")
        print(f"   https://{SPACE_NAME}.{REGION}.cdn.digitaloceanspaces.com/datasets.json")
        
    except ClientError as e:
        print(f"❌ Upload failed: {e}")
        return

if __name__ == "__main__":
    main()
