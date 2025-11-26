#!/usr/bin/env python3
"""
Script to verify and fix Google Drive credentials issues
"""

import os
import json
from pathlib import Path
from pydrive2.auth import GoogleAuth

def verify_credentials():
    """Verify credentials are working and provide diagnostics"""
    print("=" * 60)
    print("🔍 Google Drive Credentials Diagnostic")
    print("=" * 60)
    print()

    # Check current directory
    cwd = os.getcwd()
    print(f"📍 Current working directory: {cwd}")
    print()

    # Check all files in current directory
    print("📁 Files in current directory:")
    try:
        all_files = os.listdir('.')
        json_files = [f for f in all_files if f.endswith('.json')]
        yaml_files = [f for f in all_files if f.endswith('.yaml')]

        print(f"   All files: {all_files}")
        print(f"   JSON files: {json_files}")
        print(f"   YAML files: {yaml_files}")
    except Exception as e:
        print(f"   ❌ Error listing files: {e}")
        return False

    print()

    # Check credentials.json
    credentials_paths = [
        "credentials.json",
        "/app/credentials.json",
        os.path.join(cwd, "credentials.json")
    ]

    credentials_file = None
    for path in credentials_paths:
        path_obj = Path(path)
        if path_obj.exists():
            credentials_file = path_obj
            break

    if not credentials_file:
        print("❌ credentials.json not found!")
        print("   Expected locations:")
        for path in credentials_paths:
            print(f"     - {path}")
        print()
        print("🔧 SOLUTION:")
        print("   1. Run: python authenticate_gdrive.py")
        print("   2. Upload the generated credentials.json to HuggingFace")
        return False

    print(f"✅ Found credentials.json: {credentials_file}")
    print(f"   File size: {credentials_file.stat().st_size} bytes")

    # Check if file is valid JSON
    try:
        with open(credentials_file, 'r') as f:
            data = json.load(f)
        print(f"✅ credentials.json is valid JSON")
        print(f"   Keys: {list(data.keys())}")
    except Exception as e:
        print(f"❌ credentials.json is not valid JSON: {e}")
        print("   This suggests the file is corrupted")
        print("🔧 SOLUTION: Regenerate credentials.json")
        return False

    # Check settings.yaml
    settings_paths = ['settings.yaml', '/app/settings.yaml', os.path.join(cwd, 'settings.yaml')]
    settings_file = None

    for path in settings_paths:
        if Path(path).exists():
            settings_file = path
            break

    if not settings_file:
        print("❌ settings.yaml not found!")
        print("   Expected locations:")
        for path in settings_paths:
            print(f"     - {path}")
        return False

    print(f"✅ Found settings.yaml: {settings_file}")

    # Test loading with GoogleAuth
    print()
    print("🔄 Testing GoogleAuth loading...")
    try:
        gauth = GoogleAuth(settings_file=str(settings_file))
        gauth.LoadCredentialsFile(str(credentials_file))

        if gauth.credentials is None:
            print("❌ Failed to load credentials with GoogleAuth")
            print("   The credentials.json file may be corrupted or expired")
            print("🔧 SOLUTION: Regenerate credentials.json")
            return False

        print("✅ Credentials loaded successfully with GoogleAuth!")
        print(f"   Access token expired: {gauth.access_token_expired}")

        if gauth.access_token_expired:
            print("🔄 Refreshing expired token...")
            gauth.Refresh()
            gauth.SaveCredentialsFile(str(credentials_file))
            print("✅ Token refreshed and saved")

        # Test authorization
        print("🔄 Testing authorization...")
        gauth.Authorize()
        print("✅ Authorization successful!")

        return True

    except Exception as e:
        print(f"❌ Error during GoogleAuth test: {e}")
        print("   This usually means the credentials are corrupted")
        print("🔧 SOLUTION: Regenerate credentials.json")
        return False

def main():
    """Main function"""
    success = verify_credentials()

    print()
    if success:
        print("=" * 60)
        print("🎉 CREDENTIALS VERIFICATION PASSED!")
        print("=" * 60)
        print()
        print("✅ Your credentials are working correctly!")
        print("✅ The issue is likely with the HuggingFace deployment")
        print()
        print("🔍 NEXT STEPS:")
        print("   1. Check if all files are uploaded to HuggingFace:")
        print("      - credentials.json")
        print("      - settings.yaml")
        print("      - client_secrets.json")
        print("      - app.py")
        print()
        print("   2. Visit: https://your-space.hf.space/check_gdrive")
        print("      This will show detailed diagnostics")
        print()
        print("   3. If still failing, try regenerating credentials:")
        print("      python authenticate_gdrive.py")
    else:
        print("=" * 60)
        print("💥 CREDENTIALS VERIFICATION FAILED!")
        print("=" * 60)
        print()
        print("🔧 Please fix the issues above and try again")

if __name__ == "__main__":
    main()

