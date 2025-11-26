#!/usr/bin/env python3
"""
Quick script to regenerate Google Drive credentials
Run this locally, then upload credentials.json to HuggingFace
"""

from pydrive2.auth import GoogleAuth

print("🔐 Regenerating Google Drive credentials...")
print()

# Authenticate (opens browser)
gauth = GoogleAuth(settings_file='settings.yaml')
gauth.LocalWebserverAuth()

# Save credentials
gauth.SaveCredentialsFile("credentials.json")

print()
print("✅ Success! credentials.json has been regenerated.")
print(f"📄 File size: {__import__('pathlib').Path('credentials.json').stat().st_size} bytes")
print()
print("📤 Upload this file to your HuggingFace space:")
print("   - credentials.json (just generated)")
print()
print("🔍 Test it works: python verify_and_fix_credentials.py")
print("🌐 Test on server: https://your-space.hf.space/check_gdrive")

