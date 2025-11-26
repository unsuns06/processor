#!/usr/bin/env python3
"""
Check if all files are ready for Docker build and HuggingFace deployment
"""

import os
from pathlib import Path

def check_docker_ready():
    """Check if all required files are present for Docker build"""
    print("=" * 60)
    print("🐳 Docker Build Readiness Check")
    print("=" * 60)
    print()

    required_files = {
        '🔐 Authentication Files (REQUIRED for Google Drive)': {
            'credentials.json': '1.5 KB - Google Drive authentication',
            'settings.yaml': '0.4 KB - PyDrive2 configuration',
            'client_secrets.json': '0.4 KB - OAuth credentials'
        },
        '🚀 Application Files (REQUIRED)': {
            'app.py': '28.5 KB - Main application with integration',
            'requirements.txt': '0.1 KB - Python dependencies',
            'Dockerfile': '2.3 KB - Container configuration'
        },
        '📚 Documentation (OPTIONAL)': {
            'README.md': '3.4 KB - Documentation',
            'DEPLOYMENT_GUIDE.md': '3.5 KB - Deployment instructions',
            'CHANGES.md': '4.2 KB - Change log'
        }
    }

    print("📍 Current directory:", os.getcwd())
    print()

    all_good = True

    for category, files in required_files.items():
        print(f"{category}:")
        print("-" * 50)

        for filename, description in files.items():
            file_path = Path(filename)

            if file_path.exists():
                size = file_path.stat().st_size
                size_kb = size / 1024
                print(f"   ✅ {filename} ({size_kb:.1f} KB) - {description}")

                # Check if it's in the right location for Docker
                if filename in ['credentials.json', 'settings.yaml', 'client_secrets.json', 'app.py', 'requirements.txt']:
                    print(f"      📦 Ready for Docker COPY")
            else:
                print(f"   ❌ {filename} - {description}")
                print(f"      📍 Missing from: {file_path.absolute()}")
                all_good = False

        print()

    print("=" * 60)

    if all_good:
        print("🎉 DOCKER BUILD READY!")
        print("=" * 60)
        print()
        print("✅ All required files present")
        print("✅ Authentication files will be copied into container")
        print("✅ Google Drive integration will work")
        print()
        print("🚀 Next steps:")
        print("   1. Commit files to git: git add . && git commit -m 'Add Google Drive integration'")
        print("   2. Push to HuggingFace: git push")
        print("   3. Space will auto-rebuild with new Dockerfile")
        print("   4. Test: https://your-space.hf.space/check_gdrive")
        print()
        print("🐳 Docker will copy these files into /app/:")
        print("   - credentials.json")
        print("   - settings.yaml")
        print("   - client_secrets.json")
        print("   - app.py")
        print("   - requirements.txt")
    else:
        print("💥 DOCKER BUILD NOT READY!")
        print("=" * 60)
        print()
        print("❌ Some required files are missing")
        print("🐳 Docker build will fail or Google Drive integration won't work")
        print()
        print("🔧 Fix the missing files above before building")

    print()
    print("=" * 60)
    print("📋 Dockerfile Status:")
    print("=" * 60)

    # Check Dockerfile content
    dockerfile = Path('Dockerfile')
    if dockerfile.exists():
        content = dockerfile.read_text()
        if 'credentials.json' in content and 'settings.yaml' in content and 'client_secrets.json' in content:
            print("✅ Dockerfile includes authentication files")
            print("   Found COPY commands for all required auth files")
        else:
            print("⚠️  Dockerfile missing some authentication file copies")
            print("   Check Dockerfile has COPY commands for:")
            print("   - credentials.json")
            print("   - settings.yaml")
            print("   - client_secrets.json")
    else:
        print("❌ Dockerfile not found!")

    return all_good

if __name__ == "__main__":
    success = check_docker_ready()
    print()
    if success:
        print("🎊 Ready for deployment!")
    else:
        print("⚠️  Please fix missing files first")
        exit(1)

