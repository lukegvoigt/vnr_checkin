#!/usr/bin/env python3
"""
Gmail OAuth Setup Script for VPS
Run this once to get your refresh token, then set environment variables.
"""

import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def setup_gmail():
    print("Gmail OAuth Setup")
    print("=" * 50)
    
    creds_file = input("Enter path to your credentials JSON file: ").strip()
    
    if not os.path.exists(creds_file):
        print(f"Error: File not found: {creds_file}")
        return
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
        
        print("\nA browser window will open for you to authorize the app.")
        print("If running on a server without a browser, use the URL provided.\n")
        
        creds = flow.run_local_server(port=8080)
        
        with open(creds_file, 'r') as f:
            client_config = json.load(f)
        
        if 'installed' in client_config:
            client_id = client_config['installed']['client_id']
            client_secret = client_config['installed']['client_secret']
        elif 'web' in client_config:
            client_id = client_config['web']['client_id']
            client_secret = client_config['web']['client_secret']
        else:
            print("Error: Invalid credentials file format")
            return
        
        print("\n" + "=" * 50)
        print("SUCCESS! Add these to your .env file or environment:")
        print("=" * 50)
        print(f"\nGOOGLE_CLIENT_ID={client_id}")
        print(f"GOOGLE_CLIENT_SECRET={client_secret}")
        print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
        print(f"GMAIL_SENDER_EMAIL={input('Enter the Gmail address you just authorized: ').strip()}")
        print("\n" + "=" * 50)
        
    except Exception as e:
        print(f"Error during setup: {e}")

if __name__ == "__main__":
    setup_gmail()
