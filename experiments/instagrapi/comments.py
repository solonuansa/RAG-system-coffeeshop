from instagrapi import Client
import json
import time

# import patch_instagrapi
from instagr import InstagramScraper

# Initialize Database Scraper
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

scraper.login_with_session(USERNAME, PASSWORD)

try:
    print(f"\n🔍 Fetching posts from database...")
    posts_list = scraper.get_all_posts()

    if not posts_list:
        print("⚠️ No posts found in database.")
    else:
        print(f"📸 Found {len(posts_list)} posts to process")

    for post in posts_list:
        db_id = post["db_id"]
        post_id = post["post_id"]
        shortcode = post["shortcode"]

        try:
            print(f"\n{'='*70}")
            print(f"📸 Processing post: {shortcode} (ID: {post_id})")

            # Try to fetch current media info for updated stats, but catch errors
            # because instagrapi often fails with Pydantic validation on Reels
            try:
                print(f"🔍 Updating media info for {shortcode}...")
                media_info = scraper.cl.media_info(post_id)

                # Update post in database with latest stats
                post_data = {
                    "post_id": str(media_info.pk),
                    "shortcode": media_info.code,
                    "post_url": f"https://www.instagram.com/p/{media_info.code}/",
                    "username": media_info.user.username,
                    "caption": (
                        media_info.caption_text if media_info.caption_text else ""
                    ),
                    "likes_count": media_info.like_count,
                    "comments_count": media_info.comment_count,
                    "posted_at": media_info.taken_at,
                    "metadata": json.dumps(media_info.dict(), default=str),
                }
                scraper._save_post_to_db(post_data)
                print(f"✅ Post info updated in DB")
            except Exception as e:
                print(
                    f"⚠️  Could not update media info (skipping update): {str(e)[:100]}"
                )

            print(f"📝 Fetching comments for {shortcode}...")
            # We use the post_id (pk) from database directly
            comments = scraper.cl.media_comments(post_id, amount=100)

            comments_data = []
            for c in comments:
                comment_dict = {
                    "comment_id": str(c.pk),
                    "post_id": str(post_id),
                    "username": c.user.username,
                    "text": c.text,
                    "likes": c.like_count,
                    "created_at": c.created_at_utc,
                    "parent_comment_id": None,
                    "metadata": c.model_dump(mode="json"),
                }
                comments_data.append(comment_dict)

            if comments_data:
                try:
                    print(
                        f"💾 Saving {len(comments_data)} comments for post {shortcode} to database..."
                    )
                    # Save comments using the existing db_id as foreign key
                    scraper._save_comments_to_db(db_id, comments_data)
                    print(f"✅ Comments saved successfully for {shortcode}!")
                except Exception as e:
                    print(f"❌ Error saving comments to database: {e}")
            else:
                print(f"⚠️ No comments found for {shortcode}")

            # Sleep between posts to avoid rate limiting
            if post != posts_list[-1]:
                print("\n⏳ Sleeping for 5 seconds before next post...")
                time.sleep(5)

        except Exception as e:
            print(f"❌ Error processing {shortcode}: {e}")
            continue

except Exception as e:
    print(f"❌ Global Error: {e}")
    import traceback

    traceback.print_exc()
finally:
    scraper.close()
