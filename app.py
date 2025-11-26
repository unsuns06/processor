#!/usr/bin/env python3
"""
N_m3u8DL-RE DRM Processor with API-triggered Processing
Allows triggering file processing via HTTP requests
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
from pathlib import Path
import subprocess
import asyncio
from datetime import datetime
from typing import Optional, Dict, List
import uuid
import uvicorn
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

app = FastAPI(title="N_m3u8DL-RE DRM Processor")

# Enable CORS for all origins
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

# Job tracking
active_jobs: Dict[str, dict] = {}
completed_jobs: Dict[str, dict] = {}

# Mount static files directory
app.mount("/stream", StaticFiles(directory=str(STREAM_DIR)), name="stream")

# Request models
class ProcessRequest(BaseModel):
    url: str = Field(..., description="MPD/M3U8 stream URL")
    save_name: str = Field(..., description="Output filename (without extension)")
    key: Optional[str] = Field(default=None, description="DRM decryption key (single key, deprecated - use keys instead)")
    keys: Optional[List[str]] = Field(default=None, description="DRM decryption keys (list of keys for multi-key content)")
    select_video: str = Field(default="best", description="Video track selection")
    select_audio: str = Field(default="all", description="Audio track selection")
    select_subtitle: str = Field(default="all", description="Subtitle track selection")
    format: str = Field(default="mkv", description="Output format")
    log_level: str = Field(default="Debug", description="Log level")
    binary_merge: bool = Field(default=False, description="Enable binary merge mode")
    additional_args: Optional[List[str]] = Field(default=None, description="Additional N_m3u8DL-RE arguments")

class JobStatus(BaseModel):
    job_id: str
    status: str
    filename: Optional[str]
    url: Optional[str]
    started_at: str
    completed_at: Optional[str]
    error: Optional[str]

@app.get("/")
async def root():
    """Service information."""
    return {
        "service": "N_m3u8DL-RE DRM Processor",
        "version": "2.0",
        "status": "running",
        "endpoints": {
            "process": "POST /process - Trigger file processing",
            "jobs": "GET /jobs - List all jobs",
            "job_status": "GET /jobs/{job_id} - Get job status",
            "files": "GET /files - List processed files",
            "stream": "GET /stream/{filename} - Stream file (playback)",
            "download": "GET /download/{filename} - Download file",
            "health": "GET /health - Health check",
            "check_gdrive": "GET /check_gdrive - Verify Google Drive credentials",
            "debug": "GET /debug - Show detailed system info"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    tools_status = {}

    try:
        result = subprocess.run(["/usr/local/bin/N_m3u8DL-RE", "--version"], 
                              capture_output=True, text=True, timeout=5)
        tools_status["N_m3u8DL-RE"] = "available" if result.returncode == 0 else "error"
    except:
        tools_status["N_m3u8DL-RE"] = "unavailable"

    try:
        result = subprocess.run(["/usr/bin/ffmpeg", "-version"], 
                              capture_output=True, text=True, timeout=5)
        tools_status["ffmpeg"] = "available" if result.returncode == 0 else "error"
    except:
        tools_status["ffmpeg"] = "unavailable"

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
        "active_jobs": len(active_jobs),
        "completed_jobs": len(completed_jobs),
        "files_available": len(list(STREAM_DIR.glob("*.mkv"))) + len(list(STREAM_DIR.glob("*.mp4")))
    }

def upload_to_google_drive(file_path: Path) -> Optional[str]:
    """
    Upload file to Google Drive and return shareable link.
    Uses settings.yaml for authentication configuration.
    Requires credentials.json to be pre-generated locally.
    """
    try:
        # Debug: Print current working directory and check files
        print(f"🔍 Current working directory: {os.getcwd()}")
        print(f"🔍 Environment: HuggingFace Space")
        print(f"🔍 Checking for credentials.json...")

        # List all files in current directory first
        try:
            all_files = os.listdir('.')
            print(f"🔍 ALL files in directory: {sorted(all_files)}")
            print(f"   Total files: {len(all_files)}")

            # Check for our specific files
            json_files = [f for f in all_files if f.endswith('.json')]
            yaml_files = [f for f in all_files if f.endswith('.yaml')]
            py_files = [f for f in all_files if f.endswith('.py')]
            print(f"   JSON files found: {json_files}")
            print(f"   YAML files found: {yaml_files}")
            print(f"   Python files found: {py_files}")

            # Check file permissions and details
            for filename in all_files:
                try:
                    file_path = Path(filename)
                    if file_path.exists():
                        size = file_path.stat().st_size
                        print(f"   📄 {filename}: {size} bytes")
                    else:
                        print(f"   ❌ {filename}: not accessible")
                except Exception as e:
                    print(f"   ⚠️  {filename}: error checking - {e}")

        except Exception as e:
            print(f"   ❌ Error listing directory: {e}")
            import traceback
            traceback.print_exc()

        # Check multiple possible locations for credentials file
        possible_paths = [
            Path("credentials.json"),
            Path("/app/credentials.json"),
            Path(os.getcwd()) / "credentials.json"
        ]

        credentials_file = None
        for path in possible_paths:
            exists = path.exists()
            print(f"   Checking: {path} -> exists: {exists}")
            if exists:
                try:
                    size = path.stat().st_size
                    print(f"     ✅ File exists! Size: {size} bytes")
                except Exception as e:
                    print(f"     ⚠️  File exists but error getting size: {e}")
                credentials_file = path
                break
            else:
                print(f"     ❌ File not found")

        if not credentials_file:
            print("⚠️  credentials.json not found in any expected location.")
            print("   Please ensure credentials.json is uploaded to the same directory as app.py")
            print("   Expected locations:")
            for path in possible_paths:
                print(f"     - {path}")
            return None

        print(f"✅ Found credentials.json at: {credentials_file}")

        # Check file size to ensure it's not empty
        file_size = credentials_file.stat().st_size
        print(f"📄 credentials.json size: {file_size} bytes")

        if file_size == 0:
            print("❌ credentials.json is empty!")
            return None

        # Initialize GoogleAuth with settings - try multiple paths
        settings_paths = ['settings.yaml', '/app/settings.yaml', Path(os.getcwd()) / 'settings.yaml']
        settings_file = None

        for settings_path in settings_paths:
            if Path(settings_path).exists():
                settings_file = settings_path
                break

        if not settings_file:
            print("⚠️  settings.yaml not found!")
            return None

        print(f"✅ Found settings.yaml at: {settings_file}")
        gauth = GoogleAuth(settings_file=str(settings_file))

        # Load saved credentials with absolute path
        print(f"🔄 Loading credentials from: {credentials_file}")
        try:
            gauth.LoadCredentialsFile(str(credentials_file))

            if gauth.credentials is None:
                print("❌ No valid credentials found in credentials.json")
                print("   This usually means the credentials file is corrupted or expired")
                print("   Please regenerate credentials.json locally and upload again")
                print()
                print("🔧 TROUBLESHOOTING:")
                print("   1. Run 'python authenticate_gdrive.py' locally")
                print("   2. Upload the generated credentials.json to HuggingFace")
                print("   3. Make sure credentials.json is in the same directory as app.py")
                print(f"   4. Current directory: {os.getcwd()}")
                print(f"   5. Expected location: {credentials_file.absolute()}")
                return None

            print("✅ Credentials loaded successfully!")

        except Exception as e:
            print(f"❌ Error loading credentials: {e}")
            print("   This suggests the credentials.json file is corrupted")
            print("   Please regenerate it locally using: python authenticate_gdrive.py")
            return None

        if gauth.access_token_expired:
            # Refresh them if expired
            print("🔄 Refreshing expired access token...")
            gauth.Refresh()
            # Save refreshed credentials
            gauth.SaveCredentialsFile(str(credentials_file))
        else:
            # Initialize the saved creds
            gauth.Authorize()
        
        # Create GoogleDrive instance
        drive = GoogleDrive(gauth)
        
        # Upload file
        file_drive = drive.CreateFile({'title': file_path.name})
        file_drive.SetContentFile(str(file_path))
        file_drive.Upload()
        
        # Make file shareable (anyone with link can view)
        file_drive.InsertPermission({
            'type': 'anyone',
            'value': 'anyone',
            'role': 'reader'
        })
        
        # Get shareable link
        shareable_link = file_drive['alternateLink']
        return shareable_link
        
    except Exception as e:
        print(f"Error uploading to Google Drive: {e}")
        return None

async def run_n_m3u8dl_process(job_id: str, request: ProcessRequest):
    """Run N_m3u8DL-RE process in background."""

    # Validate that at least one key is provided
    if not request.keys and not request.key:
        active_jobs[job_id]["status"] = "error"
        active_jobs[job_id]["error"] = "No decryption key(s) provided"
        return

    # Build command
    cmd = [
        "/usr/local/bin/N_m3u8DL-RE",
        request.url,
        "--save-name", request.save_name,
        "--select-video", request.select_video,
        "--select-audio", request.select_audio,
        "--select-subtitle", request.select_subtitle,
        "-mt",
        "-M", f"format={request.format}",
        "--log-level", request.log_level
    ]

    # Add key(s) - handle both single key and multiple keys
    if request.keys:
        # Multiple keys provided - add each with its own --key flag
        for key in request.keys:
            cmd.extend(["--key", key])
    elif request.key:
        # Single key provided (backward compatibility)
        cmd.extend(["--key", request.key])

    # Add binary merge argument if enabled
    if request.binary_merge:
        cmd.append("--binary-merge")

    # Add additional arguments if provided
    if request.additional_args:
        cmd.extend(request.additional_args)

    # Update job status
    active_jobs[job_id]["status"] = "processing"
    active_jobs[job_id]["command"] = " ".join(cmd)

    try:
        # Change to output directory
        os.chdir(STREAM_DIR)

        # Run the process
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        # Check if successful
        if process.returncode == 0:
            output_file = STREAM_DIR / f"{request.save_name}.{request.format}"

            if output_file.exists():
                # Convert MKV to MP4 using ffmpeg
                try:
                    mkv_file = output_file
                    mp4_file = STREAM_DIR / f"{request.save_name}.mp4"

                    ffmpeg_cmd = [
                        "/usr/bin/ffmpeg",
                        "-fflags", "+genpts",
                        "-i", str(mkv_file),
                        "-map", "0:v",  # Map all video streams
                        "-map", "0:a",  # Map all audio streams
                        "-c", "copy",   # Copy streams (no re-encoding)
                        "-movflags", "+faststart",
                        "-max_interleave_delta", "0",
                        "-avoid_negative_ts", "make_zero",
                        "-y",  # Overwrite output file without asking
                        str(mp4_file)
                    ]

                    active_jobs[job_id]["status"] = "converting"

                    # Run ffmpeg conversion
                    ffmpeg_process = await asyncio.create_subprocess_exec(
                        *ffmpeg_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )

                    ffmpeg_stdout, ffmpeg_stderr = await ffmpeg_process.communicate()

                    if ffmpeg_process.returncode == 0 and mp4_file.exists():
                        # Conversion successful, delete original MKV
                        try:
                            mkv_file.unlink()
                            final_file = mp4_file
                            final_filename = mp4_file.name
                        except Exception as e:
                            # If deletion fails, keep MKV and use it as final file
                            print(f"Warning: Failed to delete MKV file: {e}")
                            final_file = mkv_file
                            final_filename = mkv_file.name
                    else:
                        # Conversion failed, keep original MKV
                        final_file = mkv_file
                        final_filename = mkv_file.name
                        active_jobs[job_id]["conversion_error"] = ffmpeg_stderr.decode() if ffmpeg_stderr else "FFmpeg conversion failed"

                    # Update job with final file info
                    active_jobs[job_id]["status"] = "completed"
                    active_jobs[job_id]["filename"] = final_filename
                    active_jobs[job_id]["url"] = f"/stream/{final_filename}"
                    active_jobs[job_id]["completed_at"] = datetime.now().isoformat()
                    active_jobs[job_id]["file_size_mb"] = round(final_file.stat().st_size / (1024 * 1024), 2)
                    active_jobs[job_id]["converted_to_mp4"] = final_filename.endswith('.mp4')

                    # Upload to Google Drive if MP4
                    if final_filename.endswith('.mp4'):
                        active_jobs[job_id]["status"] = "uploading_to_gdrive"
                        
                        gdrive_link = upload_to_google_drive(final_file)
                        if gdrive_link:
                            active_jobs[job_id]["gdrive_link"] = gdrive_link
                            active_jobs[job_id]["status"] = "completed"
                            print(f"✅ Job {job_id}: Google Drive upload completed!")
                        else:
                            active_jobs[job_id]["gdrive_error"] = "Failed to upload to Google Drive"
                            active_jobs[job_id]["status"] = "completed"
                            print(f"❌ Job {job_id}: Google Drive upload failed")

                    # Move to completed jobs
                    completed_jobs[job_id] = active_jobs[job_id]
                    del active_jobs[job_id]

                except Exception as e:
                    # If conversion fails, fall back to original MKV
                    active_jobs[job_id]["status"] = "completed"
                    active_jobs[job_id]["filename"] = output_file.name
                    active_jobs[job_id]["url"] = f"/stream/{output_file.name}"
                    active_jobs[job_id]["completed_at"] = datetime.now().isoformat()
                    active_jobs[job_id]["file_size_mb"] = round(output_file.stat().st_size / (1024 * 1024), 2)
                    active_jobs[job_id]["conversion_error"] = str(e)

                    # Move to completed jobs
                    completed_jobs[job_id] = active_jobs[job_id]
                    del active_jobs[job_id]
            else:
                active_jobs[job_id]["status"] = "error"
                active_jobs[job_id]["error"] = "Output file not found"
                active_jobs[job_id]["stderr"] = stderr.decode() if stderr else ""
        else:
            active_jobs[job_id]["status"] = "error"
            active_jobs[job_id]["error"] = f"Process exited with code {process.returncode}"
            active_jobs[job_id]["stderr"] = stderr.decode() if stderr else ""
            active_jobs[job_id]["stdout"] = stdout.decode() if stdout else ""

    except Exception as e:
        active_jobs[job_id]["status"] = "error"
        active_jobs[job_id]["error"] = str(e)
        active_jobs[job_id]["completed_at"] = datetime.now().isoformat()

@app.post("/process")
async def process_file(request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Trigger N_m3u8DL-RE processing via API.

    Example curl commands:
    
    Single key (backward compatible):
    ```
    curl -X POST "https://your-space.hf.space/process" \
      -H "Content-Type: application/json" \
      -d '{
        "url": "https://example.com/stream.mpd",
        "save_name": "clip_13141002",
        "key": "f01b16c0f7ca5aa0b843645a44b4210a",
        "binary_merge": true
      }'
    ```
    
    Multiple keys (for multi-key DRM content):
    ```
    curl -X POST "https://your-space.hf.space/process" \
      -H "Content-Type: application/json" \
      -d '{
        "url": "https://example.com/stream.mpd",
        "save_name": "clip_13141002",
        "keys": [
          "f01b16c0f7ca5aa0b843645a44b4210a",
          "a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7",
          "b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8"
        ],
        "binary_merge": true
      }'
    ```
    """
    # Validate that at least one key is provided
    if not request.keys and not request.key:
        raise HTTPException(
            status_code=400,
            detail="At least one decryption key must be provided. Use 'key' for single key or 'keys' for multiple keys."
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())

    # Create job entry
    active_jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "request": request.model_dump(),
        "started_at": datetime.now().isoformat(),
        "filename": None,
        "url": None,
        "completed_at": None,
        "error": None
    }

    # Start processing in background
    background_tasks.add_task(run_n_m3u8dl_process, job_id, request)

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Processing started",
        "check_status": f"/jobs/{job_id}",
        "estimated_filename": f"{request.save_name}.{request.format}"
    }

@app.get("/jobs")
async def list_jobs():
    """List all jobs (active and completed)."""
    return {
        "active": list(active_jobs.values()),
        "completed": list(completed_jobs.values())[-20:]  # Last 20 completed jobs
    }

@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a specific job."""

    # Check active jobs
    if job_id in active_jobs:
        return active_jobs[job_id]

    # Check completed jobs
    if job_id in completed_jobs:
        return completed_jobs[job_id]

    raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

@app.get("/files")
async def list_files():
    """List all available processed files (MKV and MP4)."""
    try:
        files = []
        # Look for both MKV and MP4 files
        for file_path in STREAM_DIR.glob("*.mkv"):
            stat = file_path.stat()
            files.append({
                "filename": file_path.name,
                "format": "mkv",
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "stream_url": f"/stream/{file_path.name}",
                "download_url": f"/download/{file_path.name}"
            })

        for file_path in STREAM_DIR.glob("*.mp4"):
            stat = file_path.stat()
            files.append({
                "filename": file_path.name,
                "format": "mp4",
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "stream_url": f"/stream/{file_path.name}",
                "download_url": f"/download/{file_path.name}"
            })

        return {
            "count": len(files),
            "files": sorted(files, key=lambda x: x["modified"], reverse=True)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")


@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download a processed file with proper download headers.
    
    Example:
    ```
    curl -O "https://your-space.hf.space/download/clip_13141002.mp4"
    wget "https://your-space.hf.space/download/clip_13141002.mkv"
    ```
    """
    # Security: prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = STREAM_DIR / filename
    
    # Check if file exists
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found")
    
    # Return file with download headers
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(file_path.stat().st_size)
        }
    )


@app.get("/debug")
async def debug_info():
    """Show detailed system and file information for debugging."""
    import platform
    import sys

    debug_data = {
        "system": {
            "platform": platform.platform(),
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "user": os.environ.get('USER', 'unknown'),
            "home": os.environ.get('HOME', 'unknown')
        },
        "files": {},
        "environment": {}
    }

    # Check all files in current directory
    try:
        files = os.listdir('.')
        debug_data["files"]["directory_listing"] = sorted(files)
        debug_data["files"]["total_count"] = len(files)

        # Check specific file types
        debug_data["files"]["json_files"] = [f for f in files if f.endswith('.json')]
        debug_data["files"]["yaml_files"] = [f for f in files if f.endswith('.yaml')]
        debug_data["files"]["py_files"] = [f for f in files if f.endswith('.py')]

        # Get details for specific files we're looking for
        important_files = ['credentials.json', 'settings.yaml', 'client_secrets.json', 'app.py', 'requirements.txt']
        debug_data["files"]["important_files"] = {}

        for filename in important_files:
            if filename in files:
                try:
                    file_path = Path(filename)
                    stat = file_path.stat()
                    debug_data["files"]["important_files"][filename] = {
                        "exists": True,
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "permissions": oct(stat.st_mode)[-3:]
                    }
                except Exception as e:
                    debug_data["files"]["important_files"][filename] = {
                        "exists": True,
                        "error": str(e)
                    }
            else:
                debug_data["files"]["important_files"][filename] = {
                    "exists": False
                }

    except Exception as e:
        debug_data["files"]["error"] = str(e)

    # Check environment variables
    env_vars = ['SPACE_ID', 'SPACE_NAME', 'SPACE_HOST', 'HF_SPACE', 'HF_TOKEN']
    for var in env_vars:
        debug_data["environment"][var] = os.environ.get(var, 'not_set')

    # Try to check git status if git is available
    try:
        import subprocess
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            debug_data["git"] = {
                "status": "available",
                "changes": result.stdout.strip(),
                "has_changes": len(result.stdout.strip()) > 0
            }
        else:
            debug_data["git"] = {
                "status": "error",
                "error": result.stderr
            }
    except Exception as e:
        debug_data["git"] = {
            "status": "not_available",
            "error": str(e)
        }

    return debug_data

@app.get("/check_gdrive")
async def check_google_drive_credentials():
    """Check if Google Drive credentials are working properly."""
    try:
        # Check if credentials file exists
        print(f"🔍 Current working directory: {os.getcwd()}")

        # List all files in current directory
        try:
            files = os.listdir('.')
            json_files = [f for f in files if f.endswith('.json')]
            yaml_files = [f for f in files if f.endswith('.yaml')]
            py_files = [f for f in files if f.endswith('.py')]

            # Detailed file info for debugging
            file_details = {}
            for filename in files:
                try:
                    file_path = Path(filename)
                    if file_path.exists():
                        stat = file_path.stat()
                        file_details[filename] = {
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                            "permissions": oct(stat.st_mode)[-3:]
                        }
                except Exception as e:
                    file_details[filename] = {"error": str(e)}

        except Exception as e:
            return {
                "error": f"Cannot list directory: {e}",
                "current_directory": os.getcwd(),
                "expected_locations": [str(p) for p in possible_paths]
            }

        credentials_file = None
        possible_paths = [
            Path("credentials.json"),
            Path("/app/credentials.json"),
            Path(os.getcwd()) / "credentials.json"
        ]

        for path in possible_paths:
            if path.exists():
                credentials_file = path
                break

        if not credentials_file:
            # Print debug info to server logs
            print("⚠️  credentials.json not found in any expected location.")
            print("   Please ensure credentials.json is uploaded to the same directory as app.py")
            print("   Expected locations:")
            for path in possible_paths:
                print(f"     - {path}")

            return {
                "status": "error",
                "message": "credentials.json not found",
                "current_directory": os.getcwd(),
                "files_in_directory": files,
                "total_files": len(files),
                "json_files": json_files,
                "yaml_files": yaml_files,
                "py_files": py_files,
                "file_details": file_details,
                "expected_locations": [str(p) for p in possible_paths],
                "debug_info": "Check server logs for detailed file listing",
                "troubleshooting": {
                    "check_git_status": "Run 'git status' to see if files are committed",
                    "check_gitignore": "Ensure credentials.json is not in .gitignore",
                    "force_rebuild": "Try rebuilding the HuggingFace space",
                    "verify_upload": "Go to Files tab and confirm all files are uploaded"
                }
            }

        # Check file size
        file_size = credentials_file.stat().st_size
        if file_size == 0:
            return {
                "status": "error",
                "message": "credentials.json is empty",
                "file_size": file_size
            }

        # Find settings file
        settings_file = None
        settings_paths = ['settings.yaml', '/app/settings.yaml', Path(os.getcwd()) / 'settings.yaml']

        for settings_path in settings_paths:
            if Path(settings_path).exists():
                settings_file = settings_path
                break

        if not settings_file:
            return {
                "status": "error",
                "message": "settings.yaml not found",
                "credentials_found": True,
                "credentials_size": file_size,
                "settings_paths_checked": settings_paths
            }

        # Try to load credentials
        gauth = GoogleAuth(settings_file=str(settings_file))
        gauth.LoadCredentialsFile(str(credentials_file))

        if gauth.credentials is None:
            return {
                "status": "error",
                "message": "No valid credentials loaded",
                "credentials_file": str(credentials_file),
                "settings_file": str(settings_file),
                "file_size": file_size
            }

        # Try to authorize
        try:
            if gauth.access_token_expired:
                gauth.Refresh()
                gauth.SaveCredentialsFile(str(credentials_file))

            gauth.Authorize()

            # Try to create a drive instance (this will test if auth actually works)
            drive = GoogleDrive(gauth)

            # Get user info as a test
            about = drive.GetAbout()
            user_email = about['user']['emailAddress']

            return {
                "status": "success",
                "message": "Google Drive credentials are working!",
                "user_email": user_email,
                "credentials_file": str(credentials_file),
                "settings_file": str(settings_file),
                "file_size": file_size,
                "token_expired": gauth.access_token_expired,
                "current_directory": os.getcwd(),
                "files_in_directory": files
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Authentication failed: {str(e)}",
                "credentials_file": str(credentials_file),
                "settings_file": str(settings_file),
                "file_size": file_size,
                "current_directory": os.getcwd()
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "current_directory": os.getcwd()
        }

@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel an active job (if possible)."""
    if job_id in active_jobs:
        # Note: Actual process cancellation would require tracking the subprocess PID
        active_jobs[job_id]["status"] = "cancelled"
        completed_jobs[job_id] = active_jobs[job_id]
        del active_jobs[job_id]
        return {"message": f"Job {job_id} cancelled"}

    raise HTTPException(status_code=404, detail=f"Job {job_id} not found or already completed")

if __name__ == "__main__":
    print("🎥 N_m3u8DL-RE DRM Processor - Enhanced FastAPI Server")
    print("=" * 60)
    print(f"Stream directory: {STREAM_DIR}")
    print("Server starting on port 7860...")
    print()
    print("📡 API Endpoints:")
    print("  • POST /process           - Trigger file processing via API")
    print("  • GET  /jobs              - List all jobs")
    print("  • GET  /jobs/{job_id}     - Check job status")
    print("  • GET  /files             - List all processed files")
    print("  • GET  /stream/{filename} - Stream/access file (playback)")
    print("  • GET  /download/{filename} - Download file")
    print("  • GET  /health            - Health check")
    print()
    print("🔄 Conversion Info:")
    print("  • MKV files are automatically converted to MP4 after processing")
    print("  • Video and audio streams are copied (no re-encoding) for speed")
    print("  • Subtitle streams are excluded (MP4 compatibility)")
    print("  • Optimized for streaming with faststart flag")
    print("  ⚠️  Note: Subtitles are not included in MP4 output files")
    print()
    print("💡 Example API calls:")
    print()
    print("  Single key:")
    print('    curl -X POST "http://localhost:7860/process" \\')
    print('      -H "Content-Type: application/json" \\')
    print('      -d \'{"url":"https://...", "save_name":"clip", "key":"...", "binary_merge":true}\'')
    print()
    print("  Multiple keys:")
    print('    curl -X POST "http://localhost:7860/process" \\')
    print('      -H "Content-Type: application/json" \\')
    print('      -d \'{"url":"https://...", "save_name":"clip", "keys":["key1","key2","key3"], "binary_merge":true}\'')
    print()

    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="info")