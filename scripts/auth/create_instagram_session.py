#!/usr/bin/env python3
"""
Instagram Session Creator
Manual tool for creating initial Instagram session when automated login fails
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from instagrapi import Client

# Load environment variables
load_dotenv()

def create_session_manually():
    """Create Instagram session manually with guided process"""
    print("🔐 Instagram Session Creator")
    print("=" * 50)

    username = os.getenv('INSTAGRAM_USERNAME')
    password = os.getenv('INSTAGRAM_PASSWORD')

    if not username or not password:
        print("❌ Instagram credentials not found in environment variables")
        return False

    print(f"👤 Username: {username}")
    print(f"🔒 Password: {'*' * len(password) if password else 'Not set'}")

    # Ask for confirmation
    response = input("\n🤔 Do you want to proceed with manual session creation? (y/N): ")
    if response.lower() != 'y':
        print("❌ Session creation cancelled")
        return False

    try:
        print("\n🔄 Creating Instagram session...")
        print("💡 This may trigger Instagram security checks")
        print("💡 Be ready to handle 2FA or verification codes")

        # Initialize client
        cl = Client()

        # Add delay for more natural behavior
        cl.delay_range = [2, 4]

        print("\n🔄 Attempting login...")
        success = cl.login(username, password)

        if success:
            print("✅ Login successful!")

            # Save session with metadata wrapper
            session_file = Path("data/instagram_session.json")
            session_file.parent.mkdir(parents=True, exist_ok=True)

            # First dump to temp file
            temp_file = session_file.with_suffix('.tmp')
            cl.dump_settings(str(temp_file))

            # Load raw session data
            with open(temp_file, 'r') as f:
                raw_session_data = json.load(f)

            # Wrap with metadata for session_manager compatibility
            wrapped_session = {
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'last_validated': datetime.now().isoformat(),
                    'last_fresh_login': datetime.now().isoformat(),
                    'username': username,
                    'login_count': 1,
                    'device_uuids': raw_session_data.get('uuids', {})
                },
                'session_data': raw_session_data
            }

            # Save wrapped session to primary location
            with open(session_file, 'w') as f:
                json.dump(wrapped_session, f, indent=2)

            print(f"✅ Session saved to: {session_file}")

            # Also save backup to sessions/ directory
            backup_dir = Path("sessions")
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_file = backup_dir / "instagram_session.json"

            with open(backup_file, 'w') as f:
                json.dump(wrapped_session, f, indent=2)

            print(f"✅ Session backup saved to: {backup_file}")

            # Clean up temp file
            temp_file.unlink()

            # Test the session
            print("\n🔍 Testing session...")
            user_info = cl.user_info_by_username(cl.username)
            print(f"✅ Session test successful - User ID: {user_info.pk}")

            print("\n🎉 Session creation completed successfully!")
            print("💡 Future runs will use this session instead of username/password")
            print("💡 Session will last up to 365 days")

            return True

        else:
            print("❌ Login failed")
            return False

    except Exception as e:
        print(f"❌ Error creating session: {e}")

        # Check for specific error types
        error_str = str(e).lower()

        if "two-factor" in error_str or "2fa" in error_str:
            print("\n💡 This account has Two-Factor Authentication enabled")
            print("💡 You'll need to disable 2FA temporarily or use app-specific password")
        elif "checkpoint" in error_str:
            print("\n💡 Instagram security checkpoint triggered")
            print("💡 Try logging in manually via Instagram app/website first")
        elif "400" in error_str:
            print("\n💡 Bad request - possibly incorrect credentials or rate limiting")
            print("💡 Wait a few hours and try again")
        elif "login" in error_str:
            print("\n💡 Login failed - check credentials and account status")

        return False

def check_existing_session():
    """Check if a session already exists and is valid"""
    session_file = Path("data/instagram_session.json")

    if not session_file.exists():
        print("📁 No existing session found")
        return False

    try:
        print("📁 Existing session found, testing...")

        # Load session data
        with open(session_file, 'r') as f:
            session_data = json.load(f)

        cl = Client()

        # Handle both wrapped and unwrapped formats
        if 'session_data' in session_data:
            # New format with metadata wrapper
            temp_file = session_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(session_data['session_data'], f)
            cl.load_settings(str(temp_file))
            temp_file.unlink()

            # Get username from metadata
            username = session_data.get('metadata', {}).get('username', cl.username)
            print(f"📅 Session created: {session_data.get('metadata', {}).get('created_at', 'Unknown')}")
        else:
            # Legacy format - direct session data
            cl.load_settings(str(session_file))
            username = cl.username

        # Test session (bypass user_info call if user_id exists)
        if hasattr(cl, 'user_id') and cl.user_id:
            print(f"✅ Existing session is valid!")
            print(f"👤 Authenticated as: {username}")
            print(f"🆔 User ID: {cl.user_id}")
            return True
        else:
            print("❌ Existing session is invalid (no user_id)")
            return False

    except Exception as e:
        print(f"❌ Error testing existing session: {e}")
        return False

def main():
    """Main function"""
    print("🔐 Instagram Session Management Tool")
    print("=" * 50)

    # First check if we already have a valid session
    if check_existing_session():
        print("\n✅ You already have a valid session!")
        print("💡 No action needed - your Instagram automation is ready")
        return 0

    print("\n" + "=" * 50)
    print("💡 Creating new session...")

    if create_session_manually():
        print("\n🎉 Session setup complete!")
        print("💡 You can now run Instagram automation scripts")
        return 0
    else:
        print("\n❌ Session creation failed")
        print("💡 Possible solutions:")
        print("   • Check your Instagram credentials")
        print("   • Disable Two-Factor Authentication temporarily")
        print("   • Log into Instagram manually first")
        print("   • Wait a few hours if rate limited")
        print("   • Use a different IP address")
        return 1

if __name__ == "__main__":
    exit(main())