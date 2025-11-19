#!/usr/bin/env python3
"""
Instagram Carousel Poster - Post 10 Template Images Using Stale Session
Uses session bypass to avoid fresh login and potential security challenges
"""

import json
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

try:
    from instagrapi import Client
    from instagrapi.exceptions import LoginRequired, ClientError
except ImportError:
    print("Missing instagrapi. Install with: pip install instagrapi")
    sys.exit(1)

from session_manager import InstagramSessionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CarouselPoster:
    """Post carousel to Instagram using stale session bypass"""

    def __init__(self, session_file: str = "data/instagram_session.json"):
        """
        Initialize carousel poster

        Args:
            session_file: Path to session JSON file
        """
        self.session_file = session_file
        self.client = None

    def load_session_bypass(self) -> bool:
        """
        Load Instagram session using bypass validation method
        Avoids problematic user_info validation that causes false expiration errors

        Returns:
            True if session loaded successfully, False otherwise
        """
        try:
            logger.info("🔄 Loading Instagram session with smart client...")

            # Initialize session manager
            session_manager = InstagramSessionManager(
                session_file=self.session_file,
                username=os.getenv('INSTAGRAM_USERNAME'),
                password=os.getenv('INSTAGRAM_PASSWORD')
            )

            # Use smart client (loads existing session only, no fresh login)
            self.client = session_manager.get_client_bypass_validation()

            if self.client:
                logger.info("✅ Session loaded successfully!")
                return True
            else:
                logger.error("❌ Failed to authenticate with Instagram")
                logger.error("💡 Check your INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD environment variables")
                return False

        except Exception as e:
            logger.error(f"❌ Error loading session: {e}")
            return False

    def post_carousel(self, image_paths: List[str], caption: str) -> Optional[str]:
        """
        Post carousel to Instagram

        Args:
            image_paths: List of paths to images (max 10)
            caption: Caption text for the post

        Returns:
            Media ID if successful, None otherwise
        """
        try:
            if not self.client:
                logger.error("❌ Client not initialized. Call load_session_bypass() first")
                return None

            if len(image_paths) > 10:
                logger.error("❌ Too many images. Instagram allows max 10 images per carousel")
                return None

            # Validate all images exist
            for img_path in image_paths:
                if not os.path.exists(img_path):
                    logger.error(f"❌ Image not found: {img_path}")
                    return None

            logger.info(f"📤 Posting carousel with {len(image_paths)} images...")
            logger.info(f"📝 Caption: {caption[:100]}...")

            # Post carousel
            media = self.client.album_upload(
                paths=image_paths,
                caption=caption
            )

            media_id = str(media.pk) if hasattr(media, 'pk') else str(media)

            logger.info(f"✅ Carousel posted successfully!")
            logger.info(f"🆔 Media ID: {media_id}")

            return media_id

        except Exception as e:
            logger.error(f"❌ Error posting carousel: {e}")
            return None

def generate_ai_caption() -> str:
    """
    Generate AI-powered caption using OpenRouter API

    Returns:
        Generated caption text
    """
    try:
        import requests

        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            logger.warning("⚠️ No OPENROUTER_API_KEY found, using default caption")
            return get_default_caption()

        logger.info("🤖 Generating AI caption using OpenRouter...")

        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        prompt = """Create an engaging Instagram caption for a crypto market analysis carousel post featuring 10 different templates:
1. Top Cryptocurrencies (ranks 2-24)
2. Extended Cryptocurrencies (ranks 25-48)
3. Top Gainers (+2% or more)
4. Top Losers (-2% or more)
5. Long Call Trading Opportunities
6. Short Call Trading Opportunities
7. Market Overview with Trend Analysis
8. Bitcoin + Macro Intelligence
9. Market Intelligence with AI Filtering

The caption should:
- Be engaging and professional
- Mention it's a comprehensive crypto market snapshot
- Include 3-5 relevant crypto hashtags
- Be under 200 characters
- Include an emoji or two for engagement

Just return the caption text, nothing else."""

        data = {
            "model": "meta-llama/llama-3.1-8b-instruct:free",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            caption = result['choices'][0]['message']['content'].strip()
            logger.info(f"✅ AI caption generated: {caption[:100]}...")
            return caption
        else:
            logger.warning(f"⚠️ AI caption generation failed: {response.status_code}")
            return get_default_caption()

    except Exception as e:
        logger.warning(f"⚠️ Error generating AI caption: {e}")
        return get_default_caption()

def get_default_caption() -> str:
    """Get default caption if AI generation fails"""
    return """📊 Complete Crypto Market Snapshot | 10 Templates

🔝 Top Gainers & Losers
📈 Long/Short Trading Opportunities
💰 Market Overview & Trend Analysis
🪙 Bitcoin Intelligence & Macro Data

#crypto #bitcoin #cryptocurrency #trading #cryptoanalysis"""

def main():
    """Main execution function"""
    logger.info("=" * 60)
    logger.info("🚀 Instagram Carousel Poster - Stale Session Method")
    logger.info("=" * 60)

    # Initialize poster
    poster = CarouselPoster()

    # Load session using bypass validation
    if not poster.load_session_bypass():
        logger.error("❌ Failed to load Instagram session. Exiting.")
        return

    # Prepare image paths (10 templates)
    output_dir = Path("output_images")
    image_paths = [
        str(output_dir / "1_output.jpg"),
        str(output_dir / "2_output.jpg"),
        str(output_dir / "3_1_output.jpg"),
        str(output_dir / "3_2_output.jpg"),
        str(output_dir / "4_output.jpg"),
        str(output_dir / "4_1_output.jpg"),
        str(output_dir / "4_2_output.jpg"),
        str(output_dir / "5_output.jpg"),
        str(output_dir / "6_output.jpg"),
        str(output_dir / "7_output.jpg"),
    ]

    # Verify all images exist
    missing_images = [path for path in image_paths if not os.path.exists(path)]
    if missing_images:
        logger.error(f"❌ Missing images: {missing_images}")
        return

    logger.info(f"✅ All {len(image_paths)} images found")

    # Generate AI caption
    caption = generate_ai_caption()

    # Post carousel
    media_id = poster.post_carousel(image_paths, caption)

    if media_id:
        logger.info("=" * 60)
        logger.info("🎉 SUCCESS! Carousel posted to Instagram")
        logger.info(f"🆔 Media ID: {media_id}")
        logger.info(f"🕒 Posted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
    else:
        logger.error("=" * 60)
        logger.error("❌ FAILED to post carousel")
        logger.error("=" * 60)

if __name__ == "__main__":
    main()
