#!/usr/bin/env python3
"""
Ensure Instagram session exists - create if missing
For GitHub Actions: checks if session file exists, creates if not
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from instagrapi import Client

# Load environment variables
load_dotenv()

def ensure_session():
    """Ensure Instagram session file exists"""
    session_file = Path("data/instagram_session.json")

    # Check if session already exists
    if session_file.exists():
        print("✅ Instagram session file already exists")
        print(f"📁 Location: {session_file}")
        return True

    print("📁 No session file found - creating new session")

    # Get credentials from environment
    username = os.getenv('INSTAGRAM_USERNAME')
    password = os.getenv('INSTAGRAM_PASSWORD')

    if not username or not password:
        print("❌ INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD must be set")
        return False

    try:
        print(f"🔐 Logging in as {username}...")

        # Initialize client
        cl = Client()
        cl.delay_range = [2, 4]

        # Perform login
        success = cl.login(username, password)

        if success:
            print("✅ Login successful!")

            # Get session data
            import tempfile
            import json
            from datetime import datetime

            # Dump settings to temp file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
                cl.dump_settings(tmp.name)
                tmp_path = tmp.name

            # Load session data
            with open(tmp_path, 'r') as f:
                session_data = json.load(f)

            # Remove temp file
            Path(tmp_path).unlink()

            # Add metadata
            now = datetime.now().isoformat()
            comprehensive_session = {
                'session_data': session_data,
                'metadata': {
                    'created_at': now,
                    'last_updated': now,
                    'last_fresh_login': now,
                    'last_validated': now,
                    'login_count': 1,
                    'device_uuids': session_data.get('uuids', {}),
                    'username': cl.username,
                    'session_version': '1.0'
                }
            }

            # Save session with metadata
            session_file.parent.mkdir(parents=True, exist_ok=True)
            with open(session_file, 'w') as f:
                json.dump(comprehensive_session, f, indent=2)
            print(f"✅ Session saved to: {session_file}")

            # Also save to sessions/ backup directory
            backup_session = Path("sessions/instagram_session.json")
            backup_session.parent.mkdir(parents=True, exist_ok=True)
            with open(backup_session, 'w') as f:
                json.dump(comprehensive_session, f, indent=2)
            print(f"✅ Backup session saved to: {backup_session}")

            return True
        else:
            print("❌ Login failed")
            return False

    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return False

if __name__ == "__main__":
    if ensure_session():
        print("\n🎉 Session ready for Instagram posting")
        sys.exit(0)
    else:
        print("\n❌ Failed to ensure session exists")
        sys.exit(1)
