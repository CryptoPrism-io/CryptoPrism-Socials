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
    """Ensure Instagram session file exists with proper format"""
    import json
    from datetime import datetime

    session_file = Path("data/instagram_session.json")

    # Check if session already exists
    if session_file.exists():
        print("✅ Instagram session file already exists")
        print(f"📁 Location: {session_file}")

        # Validate session format and fix if needed
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)

            # Check if it has metadata wrapper
            if 'metadata' not in session_data or 'session_data' not in session_data:
                print("⚠️  Session file has OLD FORMAT (missing metadata wrapper)")
                print("🔄 OLD sessions may not work - deleting and creating fresh session...")

                # Delete old format session - it's likely invalid
                session_file.unlink()

                # Also delete backup if exists
                backup_session = Path("sessions/instagram_session.json")
                if backup_session.exists():
                    backup_session.unlink()

                print("✅ Old session deleted - will create fresh session")
                # Fall through to create new session

            else:
                print("✅ Session format is correct (has metadata wrapper)")

                # Check session age - if too old, recreate
                created_at = session_data.get('metadata', {}).get('created_at')
                if created_at:
                    try:
                        created_time = datetime.fromisoformat(created_at)
                        age_days = (datetime.now() - created_time).days

                        if age_days > 30:
                            print(f"⚠️  Session is {age_days} days old (too old)")
                            print("🔄 Deleting and creating fresh session...")
                            session_file.unlink()
                            if backup_session.exists():
                                backup_session.unlink()
                            # Fall through to create new session
                        else:
                            print(f"✅ Session age: {age_days} days (acceptable)")
                            return True
                    except Exception as e:
                        print(f"⚠️  Could not parse session age: {e}")
                        return True
                else:
                    return True

        except Exception as e:
            print(f"⚠️  Could not validate session: {e}")
            print("🔄 Deleting potentially corrupted session...")
            session_file.unlink()
            # Fall through to create new session

    print("📁 No valid session found - creating new session")

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
