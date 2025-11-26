#!/usr/bin/env python3
"""
Simple Google Drive authentication to generate credentials.json
"""

from pydrive2.auth import GoogleAuth

print("🔐 Authenticating with Google Drive...")
print()

# Initialize GoogleAuth
gauth = GoogleAuth(settings_file='settings.yaml')

# Authenticate (will open browser)
print("🌐 Opening browser for authentication...")
gauth.LocalWebserverAuth()

# Save credentials using PyDrive2's method
gauth.SaveCredentialsFile("credentials.json")

print()
print("✅ Success! credentials.json has been created.")
print()
print("📤 Upload these files to your HuggingFace space:")
print("   - credentials.json")
print("   - settings.yaml")
print("   - client_secrets.json")

