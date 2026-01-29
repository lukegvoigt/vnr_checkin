#!/usr/bin/env python3
"""
Gmail OAuth Setup Script for VPS (Headless/No Browser)
Run this once to get your refresh token.
"""

import json
import os

def setup_gmail():
    print("Gmail OAuth Setup (Headless Server)")
    print("=" * 50)
    
    creds_file = input("Enter path to your credentials JSON file: ").strip()
    
    if not os.path.exists(creds_file):
        print(f"Error: File not found: {creds_file}")
        return
    
    try:
        print(f"Reading file: {creds_file}")
        with open(creds_file, 'r') as f:
            content = f.read()
            print(f"File size: {len(content)} bytes")
            client_config = json.loads(content)
        
        print(f"Keys found: {list(client_config.keys())}")
        
        if 'installed' in client_config:
            client_id = client_config['installed']['client_id']
            client_secret = client_config['installed']['client_secret']
            print("Using 'installed' credentials")
        elif 'web' in client_config:
            client_id = client_config['web']['client_id']
            client_secret = client_config['web']['client_secret']
            print("Using 'web' credentials")
        else:
            print("Error: Invalid credentials file format")
            return
        
        print(f"Client ID: {client_id[:20]}...")
        
        print("\n" + "=" * 50)
        print("STEP 1: Open this URL in your LOCAL computer's browser:")
        print("=" * 50)
        
        redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
        scope = "https://www.googleapis.com/auth/gmail.send"
        
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&response_type=code&access_type=offline&prompt=consent"
        
        print(f"\n{auth_url}\n")
        
        print("=" * 50)
        print("STEP 2: Sign in and authorize the app")
        print("STEP 3: Copy the authorization code shown")
        print("=" * 50)
        
        auth_code = input("\nPaste the authorization code here: ").strip()
        
        import requests
        response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'code': auth_code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
        )
        
        if response.status_code == 200:
            tokens = response.json()
            refresh_token = tokens.get('refresh_token')
            
            if refresh_token:
                sender_email = input("\nEnter the Gmail address you just authorized: ").strip()
                
                print("\n" + "=" * 50)
                print("SUCCESS! Add these to your .env file:")
                print("=" * 50)
                print(f"\nGOOGLE_CLIENT_ID={client_id}")
                print(f"GOOGLE_CLIENT_SECRET={client_secret}")
                print(f"GOOGLE_REFRESH_TOKEN={refresh_token}")
                print(f"GMAIL_SENDER_EMAIL={sender_email}")
                print("\n" + "=" * 50)
            else:
                print("Error: No refresh token received. Try again with a fresh authorization.")
        else:
            print(f"Error: {response.json()}")
        
    except Exception as e:
        print(f"Error during setup: {e}")

if __name__ == "__main__":
    setup_gmail()
