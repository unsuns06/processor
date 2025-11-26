#!/usr/bin/env python3
"""
Example usage of the N_m3u8DL-RE DRM Processor API
with Google Drive and Real-Debrid integration
"""

import requests
import time
import json

# API Configuration
API_BASE = "http://localhost:7860"

def process_stream(url, save_name, key):
    """
    Submit a stream for processing
    """
    endpoint = f"{API_BASE}/process"
    
    payload = {
        "url": url,
        "save_name": save_name,
        "key": key,
        "binary_merge": True,
        "format": "mkv"  # Will be auto-converted to MP4
    }
    
    print(f"📤 Submitting job for processing...")
    print(f"   URL: {url}")
    print(f"   Save name: {save_name}")
    
    response = requests.post(endpoint, json=payload)
    response.raise_for_status()
    
    result = response.json()
    job_id = result['job_id']
    
    print(f"✅ Job submitted: {job_id}")
    print()
    
    return job_id

def check_job_status(job_id):
    """
    Check the status of a job
    """
    endpoint = f"{API_BASE}/jobs/{job_id}"
    
    response = requests.get(endpoint)
    response.raise_for_status()
    
    return response.json()

def wait_for_completion(job_id, max_wait=3600):
    """
    Wait for a job to complete
    """
    print(f"⏳ Waiting for job {job_id} to complete...")
    
    start_time = time.time()
    
    while True:
        status_data = check_job_status(job_id)
        status = status_data['status']
        
        if status == 'completed':
            print(f"✅ Job completed!")
            return status_data
        elif status == 'error':
            print(f"❌ Job failed: {status_data.get('error', 'Unknown error')}")
            return status_data
        else:
            elapsed = int(time.time() - start_time)
            print(f"   Status: {status} (elapsed: {elapsed}s)")
            time.sleep(5)
        
        if time.time() - start_time > max_wait:
            print(f"⏰ Timeout after {max_wait}s")
            return status_data

def main():
    """
    Example workflow
    """
    print("=" * 60)
    print("🎬 N_m3u8DL-RE API Example Usage")
    print("=" * 60)
    print()
    
    # Example parameters (replace with real values)
    stream_url = "https://example.com/stream.mpd"
    save_name = "my_video"
    decryption_key = "your_key_here"
    
    print("⚠️  This is an example script.")
    print("Replace the URL and key with real values to test.")
    print()
    
    # Uncomment to run with real values:
    # job_id = process_stream(stream_url, save_name, decryption_key)
    # result = wait_for_completion(job_id)
    # 
    # if result['status'] == 'completed':
    #     print()
    #     print("=" * 60)
    #     print("📊 Results:")
    #     print("=" * 60)
    #     print(f"Filename: {result['filename']}")
    #     print(f"File Size: {result['file_size_mb']} MB")
    #     print(f"Local URL: {API_BASE}{result['url']}")
    #     
    #     if 'gdrive_link' in result:
    #         print(f"\n📁 Google Drive Link:")
    #         print(f"   {result['gdrive_link']}")
    #     
    #     if 'rd_direct_link' in result:
    #         print(f"\n🚀 Real-Debrid Direct Link:")
    #         print(f"   {result['rd_direct_link']}")
    #         print()
    #         print("✅ You can now download from the Real-Debrid link!")
    
    # Show health check instead
    print("🏥 Checking API health...")
    response = requests.get(f"{API_BASE}/health")
    health = response.json()
    print(json.dumps(health, indent=2))

if __name__ == "__main__":
    main()

