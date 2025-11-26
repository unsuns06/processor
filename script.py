# Create an updated setup with FastAPI to serve the MKV files
fastapi_app_content = '''#!/usr/bin/env python3
"""
N_m3u8DL-RE DRM Processor with FastAPI File Server
Serves processed MKV files to Stremio clients
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
import subprocess
from datetime import datetime
import uvicorn

app = FastAPI(title="N_m3u8DL-RE DRM Processor")

# Enable CORS for Stremio clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path("/app")
STREAM_DIR = BASE_DIR / "stream"
STREAM_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files directory for direct file access
app.mount("/stream", StaticFiles(directory=str(STREAM_DIR)), name="stream")

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "N_m3u8DL-RE DRM Processor",
        "version": "1.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "list_files": "/files",
            "stream_file": "/stream/{filename}"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    tools_status = {}
    
    # Check N_m3u8DL-RE
    try:
        result = subprocess.run(["/usr/local/bin/N_m3u8DL-RE", "--version"], 
                              capture_output=True, text=True, timeout=5)
        tools_status["N_m3u8DL-RE"] = "available" if result.returncode == 0 else "error"
    except:
        tools_status["N_m3u8DL-RE"] = "unavailable"
    
    # Check FFmpeg
    try:
        result = subprocess.run(["/usr/bin/ffmpeg", "-version"], 
                              capture_output=True, text=True, timeout=5)
        tools_status["ffmpeg"] = "available" if result.returncode == 0 else "error"
    except:
        tools_status["ffmpeg"] = "unavailable"
    
    # Check mp4decrypt
    try:
        subprocess.run(["/usr/local/bin/mp4decrypt"], 
                      capture_output=True, text=True, timeout=5)
        tools_status["mp4decrypt"] = "available"
    except:
        tools_status["mp4decrypt"] = "unavailable"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "tools": tools_status,
        "stream_directory": str(STREAM_DIR),
        "files_available": len(list(STREAM_DIR.glob("*.mkv")))
    }

@app.get("/files")
async def list_files():
    """List all available MKV files in the stream directory."""
    try:
        files = []
        for file_path in STREAM_DIR.glob("*.mkv"):
            stat = file_path.stat()
            files.append({
                "filename": file_path.name,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "url": f"/stream/{file_path.name}"
            })
        
        return {
            "count": len(files),
            "files": sorted(files, key=lambda x: x["modified"], reverse=True)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")


@app.get("/info")
async def system_info():
    """Get system and directory information."""
    return {
        "base_directory": str(BASE_DIR),
        "stream_directory": str(STREAM_DIR),
        "disk_usage": {
            "total_files": len(list(STREAM_DIR.glob("*"))),
            "mkv_files": len(list(STREAM_DIR.glob("*.mkv")))
        },
        "tools": {
            "N_m3u8DL-RE": "/usr/local/bin/N_m3u8DL-RE",
            "ffmpeg": "/usr/bin/ffmpeg",
            "mp4decrypt": "/usr/local/bin/mp4decrypt"
        }
    }

if __name__ == "__main__":
    print("🎥 N_m3u8DL-RE DRM Processor - FastAPI Server")
    print("=" * 50)
    print(f"Stream directory: {STREAM_DIR}")
    print("Server starting on port 7860...")
    print()
    print("Available endpoints:")
    print("  • GET /              - Service information")
    print("  • GET /health        - Health check")
    print("  • GET /files         - List all MKV files")
    print("  • GET /stream/{filename} - Stream/access file directly")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="info")
'''

# Update requirements.txt with FastAPI dependencies
requirements_updated = '''fastapi==0.115.0
uvicorn[standard]==0.30.6
python-multipart==0.0.9
'''

# Update Dockerfile to install FastAPI requirements
dockerfile_with_fastapi = '''# Optimized Dockerfile for N_m3u8DL-RE with FastAPI file server
FROM mcr.microsoft.com/dotnet/runtime:8.0-bookworm-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \\
    TZ=UTC \\
    DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1

# Create user as required by Hugging Face Spaces  
RUN useradd -m -u 1000 user

# Install system dependencies in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \\
    wget \\
    curl \\
    unzip \\
    ca-certificates \\
    ffmpeg \\
    python3 \\
    python3-pip \\
    && rm -rf /var/lib/apt/lists/* \\
    && apt-get clean

# Download and install Bento4 tools (mp4decrypt, mp4info)
RUN cd /tmp \\
    && wget -q "https://www.bok.net/Bento4/binaries/Bento4-SDK-1-6-0-641.x86_64-unknown-linux.zip" \\
    && unzip -j "Bento4-SDK-1-6-0-641.x86_64-unknown-linux.zip" \\
       'Bento4-SDK-1-6-0-641.x86_64-unknown-linux/bin/mp4decrypt' \\
       'Bento4-SDK-1-6-0-641.x86_64-unknown-linux/bin/mp4info' \\
       -d /usr/local/bin/ \\
    && chmod +x /usr/local/bin/mp4decrypt /usr/local/bin/mp4info \\
    && rm -f "Bento4-SDK-1-6-0-641.x86_64-unknown-linux.zip" \\
    && cd /

# Download and install N_m3u8DL-RE
RUN cd /tmp \\
    && wget -q "https://github.com/nilaoda/N_m3u8DL-RE/releases/download/v0.3.0-beta/N_m3u8DL-RE_v0.3.0-beta_linux-x64_20241203.tar.gz" \\
    && tar -xzf "N_m3u8DL-RE_v0.3.0-beta_linux-x64_20241203.tar.gz" \\
    && mv N_m3u8DL-RE /usr/local/bin/N_m3u8DL-RE \\
    && chmod +x /usr/local/bin/N_m3u8DL-RE \\
    && rm -f "N_m3u8DL-RE_v0.3.0-beta_linux-x64_20241203.tar.gz" \\
    && cd /

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Create directory structure for organized downloads
RUN mkdir -p stream \\
    && chown -R user:user /app

# Copy application files
COPY --chown=user app.py .

# Switch to non-root user
USER user

# Set user environment variables
ENV HOME=/home/user \\
    PATH=/home/user/.local/bin:$PATH

# Expose port for FastAPI server
EXPOSE 7860

# Start FastAPI server
CMD ["python3", "/app/app.py"]
'''

# Create an updated README
readme_updated = '''---
title: N_m3u8DL-RE DRM Processor
emoji: 📺
colorFrom: blue
colorTo: red
sdk: docker
app_port: 7860
pinned: false
---

# N_m3u8DL-RE DRM Content Processor with File Server

This Docker space provides N_m3u8DL-RE with all necessary dependencies for processing DRM-protected content and serving processed MKV files via HTTP to clients like Stremio.

## Features

- **N_m3u8DL-RE v0.3.0-beta**: Cross-platform DASH/HLS/MSS downloader
- **FFmpeg**: Complete multimedia framework
- **mp4decrypt (Bento4)**: DRM decryption utility
- **FastAPI Server**: HTTP server for streaming/downloading processed files
- **Direct URL Access**: Each processed file gets a direct HTTP URL

## API Endpoints

### Service Information
- `GET /` - Service information and available endpoints
- `GET /health` - Health check and tool status
- `GET /info` - System and directory information

### File Access
- `GET /files` - List all available MKV files with URLs
- `GET /stream/{filename}` - Direct access to MKV file (streamable)

## Direct URL Format

After processing a video with N_m3u8DL-RE, the file will be accessible at:

```
https://{your-username}-{space-name}.hf.space/stream/{filename}.mkv
```

For example, if your file is named `clip_13141002.mkv`, the URL would be:
```
https://your-username-your-space.hf.space/stream/clip_13141002.mkv
```

## Usage

### 1. Process DRM Content

Access the terminal/console and run:

```bash
cd /app/stream

N_m3u8DL-RE "https://your-stream-url.mpd" \\
  --save-name "clip_13141002" \\
  --select-video best \\
  --select-audio all \\
  --select-subtitle all \\
  -mt -M format=mkv \\
  --log-level Debug \\
  --key YOUR_DECRYPTION_KEY
```

### 2. Access Processed Files

Once processing completes:

1. **View all files**: Visit `https://your-space.hf.space/files`
2. **Stream directly**: Use `https://your-space.hf.space/stream/clip_13141002.mkv`

### 3. Use in Stremio

Point your Stremio addon to the direct stream URL:
```
https://your-space.hf.space/stream/{filename}.mkv
```

## File Storage

All processed files are stored in `/app/stream/` and are automatically served via the FastAPI server with proper CORS headers for client access.

## Notes

- Files are served with `Accept-Ranges: bytes` header for seeking support
- CORS is enabled for all origins (suitable for Stremio clients)
- The server runs on port 7860 (standard for Hugging Face Spaces)
- Terminal access is available for running N_m3u8DL-RE commands
'''

# Save all updated files
with open('Dockerfile', 'w') as f:
    f.write(dockerfile_with_fastapi)
    
with open('app.py', 'w') as f:
    f.write(fastapi_app_content)
    
with open('requirements.txt', 'w') as f:
    f.write(requirements_updated)
    
with open('README.md', 'w') as f:
    f.write(readme_updated)

print("✅ Updated files with FastAPI server for serving MKV files!")
print()
print("📁 Files updated:")
print("   • Dockerfile - Added Python and FastAPI dependencies")
print("   • app.py - FastAPI server with file streaming endpoints")
print("   • requirements.txt - FastAPI and uvicorn dependencies")
print("   • README.md - Updated with URL format and API documentation")
print()
print("🌐 Direct URL Format:")
print("   https://{username}-{spacename}.hf.space/stream/{filename}.mkv")
print()
print("📋 Example for your command:")
print("   After processing: clip_13141002.mkv")
print("   Direct URL: https://your-space.hf.space/stream/clip_13141002.mkv")
print()
print("🎯 API Endpoints:")
print("   • GET /files - List all available files")
print("   • GET /stream/{filename} - Stream/access file directly")
