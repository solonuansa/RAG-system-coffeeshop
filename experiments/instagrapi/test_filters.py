from instagr import InstagramScraper

# Initialize scraper
scraper = InstagramScraper(
    db_host="localhost",
    db_name="insta_kuliner",
    db_user="postgres",
    db_password="solosolo29",
    headless=True,
)

print(f"\n--- Testing get_all_users filters ---")

# 1. All users
all_users = scraper.get_all_users()
print(f"All users: {all_users}")

# 2. Verified only (Backward compatibility)
# Although we changed the hardcoded filter, we can still pass it
verified_users = scraper.get_all_users(is_verified=True)
print(f"Verified users: {verified_users}")

# 3. Not Verified
not_verified = scraper.get_all_users(is_verified=False)
print(f"Not Verified users: {not_verified}")

# 4. Followers > 0
with_followers = scraper.get_all_users(followers_count__gt=0)
print(f"Users with followers > 0: {with_followers}")

# 5. Followers > 500.000
massive_followers = scraper.get_all_users(followers_count__gt=500000)
print(f"Users with followers > 500k: {massive_followers}")

# 6. Bio is NULL (testing is_null)
null_bio = scraper.get_all_users(bio__is_null=True)
print(f"Users with NULL bio: {null_bio}")

# 7. Bio is NOT NULL
not_null_bio = scraper.get_all_users(bio__is_null=False)
print(f"Users with NOT NULL bio: {not_null_bio}")

# 8. Combined filters (Verified and Followers > 100k)
combined = scraper.get_all_users(is_verified=True, followers_count__gt=100000)
print(f"Verified users with followers > 100k: {combined}")

scraper.close()
