from instagrapi import Client
from datetime import datetime
import os
import json
import time
from instagrapi.exceptions import ClientError, PleaseWaitFewMinutes

# import patch_instagrapi
from instagr import InstagramScraper


# Initialize scraper
scraper = InstagramScraper(
    db_host="localhost",
    db_name="insta_kuliner",
    db_user="postgres",
    db_password="solosolo29",
    headless=True,
)

# Fetch credentials from database
account_data = scraper.get_account("trispsoo")
if not account_data:
    print("❌ Error: Account 'trispsoo' not found in database!")
    exit(1)

USERNAME = account_data["username"]
PASSWORD = account_data["password"]

# Login
scraper.login_with_session(USERNAME, PASSWORD)


try:
    print(f"\n🔍 Fetching users from database...")
    usernames = scraper.get_all_users()

    if not usernames:
        print("⚠️ No users found in database.")
    else:
        print(f"👥 Found {len(usernames)} users: {', '.join(usernames)}")

    for target_username in usernames:
        try:
            print(f"\n{'='*70}")
            print(f"📸 Fetching info for @{target_username}...")
            user_id = scraper.cl.user_id_from_username(target_username)
            print(f"User ID: {user_id}")

            user_info = scraper.cl.user_info(user_id)
            # Use mode="json" to handle HttpUrl and other Pydantic types
            user_dict = user_info.model_dump(mode="json")

            print(f"✅ Berhasil fetch info for @{target_username}")
            print("-" * 70)

            # Map to expected structure in scraper.save_user
            # We add 'metadata' key specifically since scraper expects it
            user_data_for_db = {
                "username": target_username,
                "full_name": user_dict.get("full_name"),
                "biography": user_dict.get("biography"),
                "follower_count": user_dict.get("follower_count"),
                "following_count": user_dict.get("following_count"),
                "media_count": user_dict.get("media_count"),
                "is_verified": user_dict.get("is_verified"),
                "profile_pic_url": str(user_dict.get("profile_pic_url")),
                "external_url": (
                    str(user_dict.get("external_url"))
                    if user_dict.get("external_url")
                    else None
                ),
                "is_private": user_dict.get("is_private"),
                "metadata": user_dict,  # Pass the whole dict as metadata
            }

            try:
                # scraper.save_user expects a DICT, not a list
                scraper.save_user(user_data_for_db)
                print(f"✅ @{target_username} saved successfully to database!")
            except Exception as e:
                print(f"❌ Error saving to database for @{target_username}: {e}")

            if target_username != usernames[-1]:
                print("\n⏳ Sleeping for 10 seconds before next user...")
                time.sleep(10)

        except Exception as e:
            print(f"❌ Error scraping @{target_username}: {e}")
            import traceback

            traceback.print_exc()
            continue

except PleaseWaitFewMinutes as e:
    print(f"⏳ Rate limit! Tunggu beberapa menit: {e}")
except ClientError as e:
    print(f"❌ Client error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
finally:
    scraper.close()
