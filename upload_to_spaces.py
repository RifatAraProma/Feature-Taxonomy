"""
Upload precomputed data to DigitalOcean Spaces
Uploads all files from precomputed/ directory to cloud storage
"""
import os
import boto3
from pathlib import Path
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

# DigitalOcean Spaces configuration
SPACE_NAME = os.getenv('DO_SPACE_NAME')
REGION = os.getenv('DO_REGION', 'sfo3')
ACCESS_KEY = os.getenv('DO_ACCESS_KEY')
SECRET_KEY = os.getenv('DO_SECRET_KEY')

# Initialize S3 client for DigitalOcean Spaces
session = boto3.session.Session()
client = session.client('s3',
    region_name=REGION,
    endpoint_url=f'https://{REGION}.digitaloceanspaces.com',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)

def upload_directory(local_dir, bucket_name, prefix=''):
    """Upload entire directory to Spaces, skipping already uploaded files"""
    local_path = Path(local_dir)
    
    if not local_path.exists():
        print(f"❌ Directory not found: {local_dir}")
        return
    
    # Get all files
    files = list(local_path.rglob('*'))
    files = [f for f in files if f.is_file()]
    
    total_size = sum(f.stat().st_size for f in files)
    print(f"📦 Found {len(files)} files ({total_size / 1e9:.2f} GB)")
    
    # Check which files already exist
    print(f"🔍 Checking for already uploaded files...")
    existing_keys = set()
    try:
        paginator = client.get_paginator('list_objects_v2')
        prefix_to_check = f"{prefix}/" if prefix else ""
        for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix_to_check):
            if 'Contents' in page:
                for obj in page['Contents']:
                    existing_keys.add(obj['Key'])
        print(f"   Found {len(existing_keys)} existing files, will skip them")
    except Exception as e:
        print(f"   Could not check existing files: {e}")
        print(f"   Will attempt to upload all files")
    
    print(f"🚀 Uploading to {bucket_name} in {REGION}...")
    
    uploaded = 0
    skipped = 0
    failed = 0
    
    for file_path in files:
        # Get relative path from local_dir
        relative_path = file_path.relative_to(local_path)
        
        # Construct S3 key (path in bucket)
        s3_key = f"{prefix}/{relative_path}".replace('\\', '/') if prefix else str(relative_path).replace('\\', '/')
        
        # Skip if already exists
        if s3_key in existing_keys:
            skipped += 1
            if (uploaded + skipped) % 100 == 0:
                progress = ((uploaded + skipped) / len(files)) * 100
                print(f"   Progress: {uploaded + skipped}/{len(files)} ({progress:.1f}%) - Uploaded: {uploaded}, Skipped: {skipped}")
            continue
        
        try:
            # Upload file
            client.upload_file(
                str(file_path),
                bucket_name,
                s3_key,
                ExtraArgs={'ACL': 'public-read'}  # Make files publicly readable
            )
            uploaded += 1
            
            # Progress indicator
            if (uploaded + skipped) % 100 == 0:
                progress = ((uploaded + skipped) / len(files)) * 100
                print(f"   Progress: {uploaded + skipped}/{len(files)} ({progress:.1f}%) - Uploaded: {uploaded}, Skipped: {skipped}")
                
        except ClientError as e:
            print(f"❌ Failed to upload {file_path}: {e}")
            failed += 1
    
    print(f"\n✅ Upload complete!")
    print(f"   Uploaded: {uploaded} files")
    print(f"   Skipped (already exists): {skipped} files")
    if failed > 0:
        print(f"   Failed: {failed} files")
    
    # Print CDN URL
    cdn_url = f"https://{bucket_name}.{REGION}.cdn.digitaloceanspaces.com"
    print(f"\n🌐 Your data is now accessible at:")
    print(f"   {cdn_url}/precomputed/")

def test_connection():
    """Test connection to Spaces"""
    try:
        # List objects in the specific space instead of all buckets
        response = client.list_objects_v2(Bucket=SPACE_NAME, MaxKeys=1)
        print("✅ Connection successful!")
        print(f"   Space '{SPACE_NAME}' is accessible")
        return True
    except ClientError as e:
        print(f"❌ Connection failed: {e}")
        print("\nPlease check:")
        print("1. Your credentials in .env file")
        print("2. Space name is correct")
        print("3. Access Key has read/write permissions")
        return False

if __name__ == '__main__':
    # Validate environment variables
    if not all([SPACE_NAME, ACCESS_KEY, SECRET_KEY]):
        print("❌ Missing credentials!")
        print("\nPlease create a .env file with:")
        print("DO_SPACE_NAME=your-space-name")
        print("DO_REGION=sfo3")
        print("DO_ACCESS_KEY=your-access-key")
        print("DO_SECRET_KEY=your-secret-key")
        exit(1)
    
    print("="*60)
    print("DIGITALOCEAN SPACES UPLOAD")
    print("="*60)
    print(f"Space: {SPACE_NAME}")
    print(f"Region: {REGION}")
    print("="*60)
    
    # Test connection first
    if not test_connection():
        exit(1)
    
    print("\n🚀 Starting upload...")
    print(f"   Scanning directory: precomputed/")
    
    # Upload precomputed data
    upload_directory('precomputed', SPACE_NAME, prefix='precomputed')
