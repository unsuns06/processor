#!/usr/bin/env python3
"""
Check which files are ready for HuggingFace upload
"""

import os
from pathlib import Path

def check_upload_status():
    """Check status of files needed for HuggingFace upload"""
    print("=" * 60)
    print("📤 HuggingFace Upload Status Check")
    print("=" * 60)
    print()

    required_files = {
        '🔐 Authentication Files (CRITICAL)': {
            'credentials.json': '1.5 KB - Generated locally via authenticate_gdrive.py',
            'settings.yaml': '0.4 KB - PyDrive2 configuration',
            'client_secrets.json': '0.4 KB - OAuth credentials'
        },
        '🚀 Application Files (REQUIRED)': {
            'app.py': '28.5 KB - Main app with Google Drive + Real-Debrid integration',
            'requirements.txt': '0.1 KB - Python dependencies',
            'Dockerfile': '2.3 KB - Container configuration'
        },
        '📚 Documentation (OPTIONAL)': {
            'README.md': '3.4 KB - Updated documentation',
            'DEPLOYMENT_GUIDE.md': '3.5 KB - This deployment guide',
            'CHANGES.md': '4.2 KB - Change log',
            'QUICK_FIX.md': '2.5 KB - Troubleshooting guide'
        }
    }

    print("📍 Current directory:", os.getcwd())
    print()

    all_good = True

    for category, files in required_files.items():
        print(f"{category}:")
        print("-" * 40)

        for filename, description in files.items():
            file_path = Path(filename)

            if file_path.exists():
                size = file_path.stat().st_size
                size_kb = size / 1024
                print(f"   ✅ {filename} ({size_kb:.1f} KB) - {description}")
            else:
                print(f"   ❌ {filename} - {description}")
                print(f"      File not found at: {file_path.absolute()}")
                all_good = False

        print()

    print("=" * 60)
    if all_good:
        print("🎉 ALL FILES READY FOR UPLOAD!")
        print("=" * 60)
        print()
        print("📤 Upload these files to HuggingFace:")
        print("   1. Go to your HuggingFace space")
        print("   2. Click 'Files' tab")
        print("   3. Upload ALL files listed above")
        print("   4. Ensure they're in the root directory (same level as app.py)")
        print()
        print("🔍 After upload, verify at: https://your-space.hf.space/check_gdrive")
    else:
        print("💥 SOME FILES MISSING!")
        print("=" * 60)
        print()
        print("❌ Please ensure all required files exist before uploading")
        print()
        print("🔧 Missing credentials.json? Run: python authenticate_gdrive.py")
        print("🔧 Missing settings.yaml? Check if it exists in current directory")
        print("🔧 Missing client_secrets.json? Check if it exists in current directory")

    return all_good

if __name__ == "__main__":
    check_upload_status()

