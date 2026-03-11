from instagrapi import Client
from datetime import datetime
import os
import json
import time
from instagrapi.exceptions import ClientError, PleaseWaitFewMinutes
from sqlalchemy import text

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


def unix_to_datetime(unix_timestamp):
    """Konversi Unix timestamp ke datetime string untuk PostgreSQL"""
    if unix_timestamp:
        return datetime.fromtimestamp(unix_timestamp).strftime("%Y-%m-%d %H:%M:%S")
    return None


def get_existing_posts(scraper, username):
    """Query shortcode post yang sudah ada di database untuk user tertentu"""
    try:
        result = scraper.db_session.execute(
            text("SELECT shortcode FROM posts WHERE username = :username"),
            {"username": username}
        ).fetchall()
        return set(row[0] for row in result if row[0])
    except Exception as e:
        print(f"⚠️ Error fetching existing posts: {e}")
        return set()


def fetch_medias_with_pagination(scraper, user_id, amount=600):
    """
    Fetch media dengan pagination untuk mendapatkan post lebih banyak
    - Menggunakan next_max_id cursor untuk pagination
    - Sort berdasarkan tanggal (terbaru dulu)
    - Rate limiting 4 detik per request
    """
    all_medias = []
    end_cursor = None
    request_count = 0
    
    print(f"📥 Mengambil hingga {amount} post dengan pagination...")
    
    while len(all_medias) < amount:
        try:
            print(f"  📄 Request #{request_count + 1}...", end=" ")
            
            # Build request params
            params = {}
            if end_cursor:
                params["max_id"] = end_cursor
            
            result = scraper.cl.private_request(f"feed/user/{user_id}/", params=params)
            
            items = result.get("items", [])
            if not items:
                print(f"✓ (tidak ada post lagi)")
                break
            
            print(f"✓ Ditemukan {len(items)} post")
            
            for idx, item in enumerate(items):
                if len(all_medias) >= amount:
                    break
                    
                media_pk = item.get("pk") or item.get("id")
                media_type = item.get("media_type")
                media_data = {
                    "pk": media_pk,
                    "id": item.get("id"),
                    "code": item.get("code"),
                    "taken_at": unix_to_datetime(item.get("taken_at")),
                    "taken_at_unix": item.get("taken_at"),  # ← Untuk sorting
                    "media_type": media_type,
                    "product_type": item.get("product_type"),
                    "caption_text": (
                        item.get("caption", {}).get("text", "")
                        if item.get("caption")
                        else ""
                    ),
                    "like_count": item.get("like_count", 0),
                    "comment_count": item.get("comment_count", 0),
                    "play_count": item.get("play_count", 0),
                    "user": {
                        "pk": item.get("user", {}).get("pk"),
                        "username": item.get("user", {}).get("username"),
                        "full_name": item.get("user", {}).get("full_name"),
                    },
                }
                all_medias.append(media_data)
            
            # Get next cursor untuk pagination
            end_cursor = result.get("next_max_id")
            if not end_cursor:
                print(f"  ℹ️ Tidak ada halaman berikutnya")
                break
            
            request_count += 1
            
            # Rate limiting: tunggu 4 detik sebelum request berikutnya
            if len(all_medias) < amount:
                print("  ⏳ Tunggu 4 detik sebelum request berikutnya...")
                time.sleep(4)
                
        except Exception as e:
            print(f"\n  ❌ Error mengambil feed: {e}")
            break
    
    # SORT BERDASARKAN TANGGAL (TERBARU DULU)
    all_medias.sort(key=lambda x: x.get("taken_at_unix", 0), reverse=True)
    
    print(f"✅ Total berhasil fetch: {len(all_medias)} post")
    return all_medias


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
            print(f"📸 Fetching media info for @{target_username}...")
            user_id = scraper.cl.user_id_from_username(target_username)
            print(f"👤 User ID: {user_id}")

            # ← UBAH: gunakan pagination dengan amount
            medias = fetch_medias_with_pagination(scraper, user_id, amount=600)
            
            if not medias:
                print(f"⚠️ Tidak ada post untuk @{target_username}")
                continue
            
            print(f"✅ Berhasil fetch {len(medias)} media")
            print("-" * 70)

            # ← TAMBAH: Cek post yang sudah ada di database
            print(f"🔍 Checking for duplicates...")
            existing_posts = get_existing_posts(scraper, target_username)
            print(f"   Ditemukan {len(existing_posts)} post yang sudah ada di database")

            output_data = []
            for media in medias:
                if isinstance(media, dict):
                    output_data.append(media)
                else:
                    output_data.append(
                        {
                            "pk": media.pk,
                            "code": media.code,
                            "media_type": media.media_type,
                            "product_type": media.product_type,
                            "caption": media.caption_text,
                            "like_count": media.like_count,
                            "comment_count": media.comment_count,
                            "taken_at": media.taken_at,
                        }
                    )

            if output_data:
                try:
                    # ← FILTER: Hanya simpan post yang baru
                    new_posts = [
                        item for item in output_data 
                        if item.get("code") not in existing_posts
                    ]
                    
                    skipped_count = len(output_data) - len(new_posts)
                    
                    print(f"\n💾 Processing {len(new_posts)} new posts (skip {skipped_count} duplicates)")
                    
                    saved_count = 0
                    for idx, item in enumerate(new_posts, 1):
                        post_data = {
                            "post_id": str(item.get("pk")),
                            "shortcode": item.get("code"),
                            "post_url": f"https://www.instagram.com/p/{item.get('code')}/",
                            "username": target_username,
                            "caption": item.get("caption")
                            or item.get("caption_text")
                            or "",
                            "likes_count": item.get("like_count", 0),
                            "comments_count": item.get("comment_count", 0),
                            "posted_at": item.get("taken_at"),
                            "metadata": json.dumps(
                                {
                                    "media_type": item.get("media_type"),
                                    "product_type": item.get("product_type"),
                                },
                                default=str,
                            ),
                        }
                        try:
                            scraper._save_post_to_db(post_data)
                            saved_count += 1
                            print(f"   [{idx}/{len(new_posts)}] ✓ {item.get('code')}")
                        except Exception as e:
                            print(f"   ⚠️ Failed to save post {item.get('code')}: {e}")
                    
                    print(f"\n✅ Summary: {saved_count} posts baru, {skipped_count} duplikat")
                    
                except Exception as e:
                    print(f"❌ Error saving to database for @{target_username}: {e}")
            else:
                print("⚠️ Tidak ada data untuk disimpan")

            if target_username != usernames[-1]:
                print(f"\n⏳ Sleeping for 10 seconds before next user...")
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
