"""
Instagram Comment Scraper dengan Playwright dan PostgreSQL
Author: Research Tool
Version: 2.0

Dependencies:
    pip install playwright psycopg2-binary
    playwright install chromium
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import func
import json
from models import Base, User, Post, Comment, InstagramAccount
import time
import random
from datetime import datetime
from typing import List, Dict, Optional
import re
import os
import base64
from instagrapi import Client


class InstagramScraper:
    """
    Class untuk scraping komentar Instagram dengan Playwright
    dan menyimpan ke PostgreSQL database
    """

    def __init__(
        self,
        db_host: str = "localhost",
        db_name: str = "insta_kuliner",
        db_user: str = "postgres",
        db_password: str = "solosolo29",
        db_port: int = 5432,
        headless: bool = False,
    ):
        """
        Initialize Instagram Scraper

        Args:
            db_host: PostgreSQL host
            db_name: Database name
            db_user: Database user
            db_password: Database password
            db_port: Database port
            headless: Run browser in headless mode
        """
        # Create connection string
        # Assuming typical postgres user/pass/host/db structure
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

        # Ensure tables exist
        Base.metadata.create_all(self.engine)

        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False
        self.session_file = "session.json"
        self.cl = Client()

    def get_session(self):
        """Get a new database session"""
        return self.Session()

    def _init_browser(self):
        """Initialize Playwright browser"""
        if self.browser is None:
            playwright = sync_playwright().start()

            # Try to launch browser with error handling
            try:
                self.browser = playwright.chromium.launch(headless=self.headless)
            except Exception as e:
                print(f"\n⚠️ Failed to launch Chromium: {e}")
                print("\n💡 Trying to use system Chrome instead...")

                # Try to find system Chrome/Chromium
                import platform

                system = platform.system()

                chrome_paths = {
                    "Darwin": [  # macOS
                        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                        "/Applications/Chromium.app/Contents/MacOS/Chromium",
                    ],
                    "Linux": [
                        "/usr/bin/google-chrome",
                        "/usr/bin/chromium-browser",
                        "/usr/bin/chromium",
                    ],
                    "Windows": [
                        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                    ],
                }

                chrome_path = None
                for path in chrome_paths.get(system, []):
                    import os

                    if os.path.exists(path):
                        chrome_path = path
                        break

                if chrome_path:
                    print(f"✅ Found Chrome at: {chrome_path}")
                    self.browser = playwright.chromium.launch(
                        executable_path=chrome_path, headless=self.headless
                    )
                else:
                    raise Exception(
                        "Chromium not found! Please run: playwright install chromium"
                    )

            context = self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            self.page = context.new_page()

    def login(self, username: str, password: str) -> bool:
        """
        Login to Instagram

        Args:
            username: Instagram username
            password: Instagram password

        Returns:
            bool: True if login successful
        """
        try:
            self._init_browser()
            print("🔐 Logging in to Instagram...")

            self.page.goto("https://www.instagram.com/accounts/login/")
            self.page.wait_for_load_state("domcontentloaded")
            time.sleep(random.uniform(2, 3))

            # Fill credentials
            self.page.fill('input[name="username"]', username)
            time.sleep(random.uniform(0.5, 1))
            self.page.fill('input[name="password"]', password)
            time.sleep(random.uniform(0.5, 1))
            self.page.click('button[type="submit"]')

            # Wait for redirect
            self.page.wait_for_load_state("networkidle")
            time.sleep(3)

            # Skip popups
            try:
                self.page.click('button:has-text("Not Now")', timeout=5000)
                time.sleep(1)
            except:
                pass

            try:
                self.page.click('button:has-text("Not Now")', timeout=5000)
                time.sleep(1)
            except:
                pass

            self.is_logged_in = True
            print("✅ Login successful!")
            return True

        except Exception as e:
            print(f"❌ Login failed: {str(e)}")
            return False

    def _extract_shortcode(self, post_url: str) -> str:
        """Extract shortcode from Instagram post URL"""
        match = re.search(r"/p/([A-Za-z0-9_-]+)", post_url)
        if match:
            return match.group(1)
        raise ValueError(f"Invalid Instagram post URL: {post_url}")

    def save_user(self, user_data: Dict) -> int:
        """
        Save or update user in database
        """
        session = self.get_session()
        try:
            stmt = insert(User).values(
                username=user_data["username"],
                full_name=user_data.get("full_name"),
                bio=user_data.get("biography"),
                followers_count=user_data.get("follower_count"),
                following_count=user_data.get("following_count"),
                posts_count=user_data.get("media_count"),
                is_verified=user_data.get("is_verified", False),
                profile_pic_url=user_data.get("profile_pic_url"),
                external_url=user_data.get("external_url"),
                is_private=user_data.get("is_private"),
                metadata_json=(
                    json.loads(user_data.get("metadata", "{}"))
                    if isinstance(user_data.get("metadata"), str)
                    else user_data.get("metadata", {})
                ),
            )

            # Upsert logic
            stmt = stmt.on_conflict_do_update(
                index_elements=["username"],
                set_={
                    "full_name": stmt.excluded.full_name,
                    "bio": stmt.excluded.bio,
                    "followers_count": stmt.excluded.followers_count,
                    "following_count": stmt.excluded.following_count,
                    "posts_count": stmt.excluded.posts_count,
                    "is_verified": stmt.excluded.is_verified,
                    "profile_pic_url": stmt.excluded.profile_pic_url,
                    "last_updated_at": func.now(),
                },
            )

            result = session.execute(stmt)
            session.commit()

            # Get the user ID
            user = session.query(User).filter_by(username=user_data["username"]).first()
            return user.id if user else None

        except Exception as e:
            session.rollback()
            print(f"❌ Error saving user: {str(e)}")
            raise
        finally:
            session.close()

    def _save_post_to_db(self, post_data: Dict) -> int:
        """
        Save post information to database

        Returns:
            int: database id of the post
        """
        session = self.get_session()
        try:
            # Prepare data
            stmt = insert(Post).values(
                post_id=post_data["post_id"],
                shortcode=post_data["shortcode"],
                post_url=post_data["post_url"],
                username=post_data["username"],
                caption=post_data["caption"],
                likes_count=post_data["likes_count"],
                comments_count=post_data["comments_count"],
                posted_at=post_data["posted_at"],
                metadata_json=(
                    json.loads(post_data.get("metadata", "{}"))
                    if isinstance(post_data.get("metadata"), str)
                    else {}
                ),
            )

            # Upsert logic
            stmt = stmt.on_conflict_do_update(
                index_elements=["shortcode"],
                set_={
                    "likes_count": stmt.excluded.likes_count,
                    "comments_count": stmt.excluded.comments_count,
                    "scraped_at": func.now(),
                },
            )

            session.execute(stmt)
            session.commit()

            # Get the post ID (database PK)
            post = (
                session.query(Post).filter_by(shortcode=post_data["shortcode"]).first()
            )
            return post.id

        except Exception as e:
            session.rollback()
            print(f"❌ Error saving post: {str(e)}")
            raise
        finally:
            session.close()

    def _save_comments_to_db(self, post_db_id: int, comments: List[Dict]):
        """Save comments to database"""
        if not comments:
            return

        session = self.get_session()
        try:
            saved_count = 0

            # Process comments in chunks or one by one
            for comment in comments:
                stmt = insert(Comment).values(
                    comment_id=comment.get(
                        "comment_id", f"temp_{hash(comment['text'])}"
                    ),
                    post_id=post_db_id,
                    username=comment["username"],
                    comment_text=comment["text"],
                    likes_count=comment.get("likes", 0),
                    created_at=comment.get("created_at"),
                    parent_comment_id=comment.get("parent_comment_id"),
                    metadata_json=comment.get("metadata", {}),
                )

                # Upsert - do nothing on conflict for comments currently
                stmt = stmt.on_conflict_do_nothing(index_elements=["comment_id"])

                result = session.execute(stmt)
                if result.rowcount > 0:
                    saved_count += 1

            session.commit()
            print(f"💾 Saved {saved_count} new comments to database")

        except Exception as e:
            session.rollback()
            print(f"❌ Error saving comments: {str(e)}")
            raise
        finally:
            session.close()

    def scrape_comments(
        self, post_url: str, max_comments: int = 50, save_to_db: bool = True
    ) -> List[Dict]:
        """
        Scrape comments from Instagram post

        Args:
            post_url: Instagram post URL
            max_comments: Maximum number of comments to scrape
            save_to_db: Save results to database

        Returns:
            List of comment dictionaries
        """
        if not self.is_logged_in:
            raise Exception("Please login first using .login() method")

        try:
            shortcode = self._extract_shortcode(post_url)
            print(f"\n📸 Scraping post: {shortcode}")
            print(f"🎯 Target: {max_comments} comments")

            # Navigate to post with increased timeout
            print("🌐 Loading post...")
            self.page.goto(post_url, timeout=60000)  # 60 second timeout
            self.page.wait_for_load_state("domcontentloaded", timeout=60000)
            time.sleep(random.uniform(3, 5))

            # Take screenshot for debugging
            self.page.screenshot(path=f"debug_{shortcode}.png")
            print(f"📷 Debug screenshot saved: debug_{shortcode}.png")

            # Extract post metadata
            post_data = self._extract_post_metadata(post_url, shortcode)

            # Try multiple strategies to access comments
            print("🔍 Looking for comments section...")

            # Strategy 1: Click "View all comments"
            try:
                view_all_buttons = [
                    'button:has-text("View all")',
                    'a:has-text("View all")',
                    'span:has-text("View all")',
                ]

                for selector in view_all_buttons:
                    try:
                        self.page.click(selector, timeout=5000)
                        print("✅ Clicked 'View all comments'")
                        time.sleep(3)
                        break
                    except:
                        continue
            except:
                print("ℹ️ No 'View all' button found, continuing...")

            # Strategy 2: Try to click on comments section
            try:
                # Click on comment icon or section to expand
                comment_sections = [
                    'svg[aria-label*="Comment"]',
                    'span:has-text("comments")',
                ]

                for selector in comment_sections:
                    try:
                        self.page.click(selector, timeout=3000)
                        time.sleep(2)
                        break
                    except:
                        continue
            except:
                pass

            # Scroll and collect comments
            comments = []
            last_count = 0
            scroll_attempts = 0
            max_scroll_attempts = 30  # Increased attempts
            no_progress_count = 0

            print("📝 Collecting comments...")

            while (
                len(comments) < max_comments and scroll_attempts < max_scroll_attempts
            ):
                # Extract comments from page
                new_comments = self._extract_comments_from_page()

                # Add new unique comments
                for comment in new_comments:
                    # Check if comment already exists
                    is_duplicate = any(
                        c["text"] == comment["text"]
                        and c["username"] == comment["username"]
                        for c in comments
                    )

                    if not is_duplicate and len(comments) < max_comments:
                        comments.append(comment)

                current_count = len(comments)
                print(f"   Collected: {current_count}/{max_comments}", end="\r")

                # Check progress
                if current_count == last_count:
                    no_progress_count += 1

                    # If no progress after 5 attempts, try different scroll
                    if no_progress_count >= 5:
                        print(
                            "\n⚠️ No new comments found, trying different scroll method..."
                        )

                        # Try scrolling the comments container specifically
                        self.page.evaluate(
                            """
                            const containers = document.querySelectorAll('div[style*="overflow"]');
                            containers.forEach(c => c.scrollTop = c.scrollHeight);
                        """
                        )
                        time.sleep(2)
                        no_progress_count = 0

                    scroll_attempts += 1
                else:
                    no_progress_count = 0
                    scroll_attempts = 0
                    last_count = current_count

                # Multiple scroll strategies
                try:
                    # Scroll main window
                    self.page.evaluate("window.scrollBy(0, 500)")
                    time.sleep(1)

                    # Scroll to bottom
                    self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(random.uniform(1, 2))
                except:
                    pass

                # Stop if we haven't found any comments after many attempts
                if scroll_attempts > 10 and len(comments) == 0:
                    print("\n⚠️ Cannot find comments on this post")
                    print("   Possible reasons:")
                    print("   - Post has comments disabled")
                    print("   - Post is private or deleted")
                    print("   - Instagram structure changed")
                    break

            print(f"\n✅ Collected {len(comments)} comments")

            if len(comments) == 0:
                print("\n⚠️ No comments collected!")
                print("   Check debug screenshot: debug_{}.png".format(shortcode))

            # Save to database
            if save_to_db and len(comments) > 0:
                print("💾 Saving to database...")
                post_id = self._save_post_to_db(post_data)
                self._save_comments_to_db(post_id, comments)
                print("✅ Data saved successfully!")

            return comments

        except Exception as e:
            print(f"\n❌ Error scraping comments: {str(e)}")
            self.page.screenshot(path=f"error_{shortcode}.png")
            print(f"📷 Error screenshot saved: error_{shortcode}.png")
            raise

    def _extract_post_metadata(self, post_url: str, shortcode: str) -> Dict:
        """Extract post metadata from page"""
        try:
            # Try to extract caption
            caption = ""
            try:
                caption_elem = self.page.query_selector("h1")
                if caption_elem:
                    caption = caption_elem.inner_text()
            except:
                pass

            # Try to extract username
            username = ""
            try:
                username_elem = self.page.query_selector("header a")
                if username_elem:
                    username = username_elem.inner_text()
            except:
                pass

            return {
                "post_id": shortcode,
                "shortcode": shortcode,
                "post_url": post_url,
                "username": username,
                "caption": caption,
                "likes_count": 0,
                "comments_count": 0,
                "posted_at": None,
                "metadata": json.dumps({}),
            }
        except Exception as e:
            print(f"⚠️ Warning: Could not extract full post metadata: {e}")
            return {
                "post_id": shortcode,
                "shortcode": shortcode,
                "post_url": post_url,
                "username": "unknown",
                "caption": "",
                "likes_count": 0,
                "comments_count": 0,
                "posted_at": None,
                "metadata": json.dumps({}),
            }

    def _extract_comments_from_page(self) -> List[Dict]:
        """Extract comments visible on current page"""
        comments = []

        try:
            # Multiple selector strategies for Instagram comments
            selectors = [
                "ul ul li",  # Nested list items (common structure)
                "article ul li div span",  # Span containing text
                'div[role="button"] span',  # Spans with role button
            ]

            comment_elements = []
            for selector in selectors:
                try:
                    elements = self.page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        comment_elements = elements
                        break
                except:
                    continue

            if not comment_elements:
                # Fallback: Try to get all text content
                print("⚠️ Using fallback text extraction method")
                return []

            for elem in comment_elements:
                try:
                    # Get full text
                    full_text = elem.inner_text().strip()

                    # Skip if too short or empty
                    if not full_text or len(full_text) < 2:
                        continue

                    # Try to extract username (usually first word or link)
                    username = "Unknown"
                    try:
                        link = elem.query_selector("a")
                        if link:
                            username = link.inner_text().strip()
                    except:
                        # Try to get first word as username
                        words = full_text.split()
                        if words:
                            username = words[0]

                    # Remove username from text
                    comment_text = full_text
                    if comment_text.startswith(username):
                        comment_text = comment_text[len(username) :].strip()

                    # Skip if it's just username or very short
                    if not comment_text or len(comment_text) < 2:
                        continue

                    # Skip navigation/UI elements
                    skip_phrases = [
                        "View all",
                        "Reply",
                        "Translate",
                        "See translation",
                        "likes",
                        "Load more",
                        "Show more",
                    ]
                    if any(
                        phrase.lower() in comment_text.lower()
                        for phrase in skip_phrases
                    ):
                        continue

                    comment = {
                        "username": username,
                        "text": comment_text,
                        "likes": 0,
                        "created_at": datetime.now(),
                        "parent_comment_id": None,
                        "metadata": {},
                    }

                    # Avoid duplicates
                    if not any(
                        c["text"] == comment_text and c["username"] == username
                        for c in comments
                    ):
                        comments.append(comment)

                except Exception as e:
                    continue

        except Exception as e:
            print(f"⚠️ Warning extracting comments: {e}")

        return comments

    def get_user_posts(
        self, username: str, max_posts: int = 12, scroll_attempts: int = 10
    ) -> List[str]:
        """
        Get list of post URLs from a user's profile

        Args:
            username: Instagram username (without @)
            max_posts: Maximum number of posts to collect
            scroll_attempts: Maximum scroll attempts to load more posts

        Returns:
            List of post URLs
        """
        if not self.is_logged_in:
            raise Exception("Please login first using .login() method")

        try:
            profile_url = f"https://www.instagram.com/{username}/"
            print(f"\n👤 Fetching posts from @{username}")
            print(f"🎯 Target: {max_posts} posts")

            self.page.goto(profile_url)
            self.page.wait_for_load_state("networkidle")
            time.sleep(random.uniform(2, 3))

            # Check if profile exists
            if "Sorry, this page isn't available" in self.page.content():
                raise Exception(f"Profile @{username} not found or is private")

            post_urls = []
            last_count = 0
            attempts = 0

            print("📸 Collecting post URLs...")

            while len(post_urls) < max_posts and attempts < scroll_attempts:
                # Find all post links
                post_links = self.page.query_selector_all('article a[href*="/p/"]')

                # Extract URLs
                for link in post_links:
                    href = link.get_attribute("href")
                    if href and "/p/" in href:
                        full_url = (
                            f"https://www.instagram.com{href}"
                            if not href.startswith("http")
                            else href
                        )
                        if full_url not in post_urls and len(post_urls) < max_posts:
                            post_urls.append(full_url)

                current_count = len(post_urls)
                print(f"   Found: {current_count}/{max_posts}", end="\r")

                # Check if we need more scrolling
                if current_count == last_count:
                    attempts += 1
                else:
                    attempts = 0
                    last_count = current_count

                # Scroll down
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(random.uniform(2, 3))

            print(f"\n✅ Found {len(post_urls)} posts from @{username}")
            return post_urls[:max_posts]

        except Exception as e:
            print(f"\n❌ Error getting posts from @{username}: {str(e)}")
            raise

    def scrape_user_posts(
        self,
        username: str,
        max_posts: int = 12,
        max_comments_per_post: int = 50,
        delay_between_posts: tuple = (10, 20),
    ) -> Dict[str, List[Dict]]:
        """
        Scrape all posts from a specific user

        Args:
            username: Instagram username (without @)
            max_posts: Maximum number of posts to scrape
            max_comments_per_post: Max comments per post
            delay_between_posts: Random delay range between posts (min, max) in seconds

        Returns:
            Dictionary mapping post URLs to comments
        """
        print(f"\n{'='*60}")
        print(f"🎯 Starting scraping for @{username}")
        print(f"{'='*60}")

        # Get all post URLs from user
        post_urls = self.get_user_posts(username, max_posts)

        if not post_urls:
            print(f"⚠️ No posts found for @{username}")
            return {}

        # Scrape each post
        return self.scrape_multiple_posts(
            post_urls, max_comments_per_post, delay_between_posts
        )

    def scrape_multiple_posts(
        self,
        post_urls: List[str],
        max_comments_per_post: int = 50,
        delay_between_posts: tuple = (10, 20),
    ) -> Dict[str, List[Dict]]:
        """
        Scrape multiple posts

        Args:
            post_urls: List of Instagram post URLs
            max_comments_per_post: Max comments per post
            delay_between_posts: Random delay range between posts (min, max) in seconds

        Returns:
            Dictionary mapping post URLs to comments
        """
        results = {}

        for i, post_url in enumerate(post_urls, 1):
            print(f"\n{'='*60}")
            print(f"📊 Progress: {i}/{len(post_urls)}")
            print(f"{'='*60}")

            try:
                comments = self.scrape_comments(post_url, max_comments_per_post)
                results[post_url] = comments

                # Delay between posts (except last one)
                if i < len(post_urls):
                    delay = random.uniform(*delay_between_posts)
                    print(f"⏳ Waiting {delay:.1f}s before next post...")
                    time.sleep(delay)

            except Exception as e:
                print(f"❌ Failed to scrape {post_url}: {e}")
                results[post_url] = []

        print(f"\n{'='*60}")
        print(f"✅ Completed scraping {len(post_urls)} posts")
        print(f"{'='*60}")

        return results

    def get_statistics(self) -> Dict:
        """Get statistics from database using SQLAlchemy"""
        session = self.get_session()
        try:
            stats = {}

            # Total posts
            stats["total_posts"] = session.query(func.count(Post.id)).scalar()

            # Total comments
            stats["total_comments"] = session.query(func.count(Comment.id)).scalar()

            # Unique users (commenters)
            stats["unique_commenters"] = session.query(
                func.count(Comment.username.distinct())
            ).scalar()

            # Top commenters
            top_commenters_query = (
                session.query(
                    Comment.username, func.count(Comment.id).label("comment_count")
                )
                .group_by(Comment.username)
                .order_by(func.count(Comment.id).desc())
                .limit(5)
                .all()
            )

            stats["top_commenters"] = [
                {"username": row[0], "comment_count": row[1]}
                for row in top_commenters_query
            ]

            return stats
        except Exception as e:
            print(f"❌ Error getting statistics: {str(e)}")
            return {}
        finally:
            session.close()

    def get_all_users(self, **filters) -> List[str]:
        """
        Get usernames from users table with flexible filtering.

        Supported filters:
        - field=value: Exact match (e.g., is_verified=True)
        - field__gt=value: Greater than (e.g., followers_count__gt=1000)
        - field__lt=value: Less than (e.g., followers_count__lt=100)
        - field__is_null=True/False: Null check (e.g., bio__is_null=False)
        """
        session = self.get_session()
        try:
            query = session.query(User.username)

            for key, value in filters.items():
                if "__" in key:
                    field, op = key.rsplit("__", 1)
                    if not hasattr(User, field):
                        print(f"⚠️ Warning: User model has no attribute '{field}'")
                        continue
                    col = getattr(User, field)
                    if op == "gt":
                        query = query.filter(col > value)
                    elif op == "lt":
                        query = query.filter(col < value)
                    elif op == "is_null":
                        if value:
                            query = query.filter(col == None)
                        else:
                            query = query.filter(col != None)
                else:
                    if not hasattr(User, key):
                        print(f"⚠️ Warning: User model has no attribute '{key}'")
                        continue
                    query = query.filter(getattr(User, key) == value)

            users = query.all()
            return [user.username for user in users]
        except Exception as e:
            print(f"❌ Error getting users: {str(e)}")
            return []
        finally:
            session.close()

    def get_all_post_shortcodes(self) -> List[str]:
        """Get all post shortcodes from posts table"""
        session = self.get_session()
        try:
            posts = session.query(Post.shortcode).all()
            return [post.shortcode for post in posts]
        except Exception as e:
            print(f"❌ Error getting post shortcodes: {str(e)}")
            return []
        finally:
            session.close()

    def get_all_posts(self) -> List[Dict]:
        """Get all post details from posts table"""
        session = self.get_session()
        try:
            posts = session.query(Post.id, Post.post_id, Post.shortcode).all()
            return [
                {"db_id": p.id, "post_id": p.post_id, "shortcode": p.shortcode}
                for p in posts
            ]
        except Exception as e:
            print(f"❌ Error getting posts: {str(e)}")
            return []
        finally:
            session.close()

    def login_with_session(
        self, username: Optional[str] = None, password: Optional[str] = None
    ):
        """Login using session file if available, otherwise login and save session"""
        # Determine credentials - either passed or from instance if we add them later
        # For now, let's assume they are either passed or we use placeholders
        # But to fix the user's current logic, they need to be passed or accessible.

        if not username or not password:
            print("⚠️ Username and Password are required for login.")
            return

        if os.path.exists(self.session_file):
            print("🔄 Load session dari file...")
            try:
                self.cl.load_settings(self.session_file)
                self.cl.login(username, password)
                self.cl.get_timeline_feed()
                print("✅ Login menggunakan session")
                self.is_logged_in = True
                return
            except Exception as e:
                print("⚠️ Session invalid, login ulang...", e)

        print("🔐 Login pertama kali...")
        try:
            self.cl.login(username, password)
            self.cl.dump_settings(self.session_file)
            print("💾 Session disimpan")
            self.is_logged_in = True
        except Exception as e:
            print(f"❌ Login gagal: {e}")
            self.is_logged_in = False

    def _encrypt_password(self, password: str) -> str:
        """
        Simple password encryption
        PRODUCTION: Gunakan cryptography.fernet atau library crypto lainnya!
        """
        encoded = base64.b64encode(password.encode()).decode()
        return encoded

    def _decrypt_password(self, encrypted_password: str) -> str:
        """
        Simple password decryption
        """
        decoded = base64.b64decode(encrypted_password.encode()).decode()
        return decoded

    def get_account(self, username: str) -> Optional[Dict]:
        """Fetch account details from database"""
        session = self.get_session()
        try:
            account = (
                session.query(InstagramAccount).filter_by(username=username).first()
            )
            if account:
                return {
                    "username": account.username,
                    "password": self._decrypt_password(account.password_encrypted),
                    "status": account.status,
                }
            return None
        except Exception as e:
            print(f"❌ Error getting account {username}: {e}")
            return None
        finally:
            session.close()

    def get_available_accounts(self) -> List[Dict]:
        """Fetch all active accounts from database"""
        session = self.get_session()
        try:
            accounts = (
                session.query(InstagramAccount)
                .filter_by(is_active=True, is_banned=False)
                .all()
            )
            return [
                {
                    "username": acc.username,
                    "password": self._decrypt_password(acc.password_encrypted),
                }
                for acc in accounts
            ]
        except Exception as e:
            print(f"❌ Error getting available accounts: {e}")
            return []
        finally:
            session.close()

    def add_account(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
    ) -> int:
        """
        Add Instagram account to database

        Args:
            username: Instagram username
            password: Instagram password
            email: Email address
            phone: Phone number
            tags: Tags untuk categorization
            notes: Additional notes

        Returns:
            account_id jika sukses, None jika gagal
        """
        session = self.get_session()

        try:
            encrypted_password = self._encrypt_password(password)

            stmt = insert(InstagramAccount).values(
                username=username,
                password_encrypted=encrypted_password,
                email=email,
                phone=phone,
                tags=tags,
                notes=notes,
                is_verified=False,
                metadata_json={},
            )

            stmt = stmt.on_conflict_do_update(
                index_elements=["username"],
                set_={
                    "password_encrypted": stmt.excluded.password_encrypted,
                    "email": stmt.excluded.email,
                    "phone": stmt.excluded.phone,
                    "tags": stmt.excluded.tags,
                    "notes": stmt.excluded.notes,
                    "updated_at": func.now(),
                },
            )

            result = session.execute(stmt)
            session.commit()

            print(f"✅ Account @{username} added successfully!")
            print(f"   Tags: {', '.join(tags) if tags else 'None'}")
            print(f"   Notes: {notes or 'None'}")

        except Exception as e:
            session.rollback()
            print(f"❌ Error adding account: {e}")
            raise
        finally:
            session.close()

    def close(self):
        """Close browser"""
        if self.browser:
            self.browser.close()
            self.browser = None
            self.page = None
            self.is_logged_in = False
            print("👋 Browser closed")


# ============================================
# EXAMPLE USAGE
# ============================================

if __name__ == "__main__":

    # Initialize scraper
    scraper = InstagramScraper(
        db_host="localhost",
        db_name="magang",
        db_user="postgres",
        db_password="postgres",
        headless=False,  # Set True untuk production
    )

    try:
        # Login
        # scraper.login(username="", password="")

        # ============================================
        # OPTION 1: Scrape single post
        # ============================================
        # print("\n[OPTION 1] Scraping single post...")
        # comments = scraper.scrape_comments(
        #     post_url="https://www.instagram.com/p/DTJ9PALkYND/",
        #     max_comments=50,
        #     save_to_db=True,
        # )

        # print(f"\n📊 Sample comments:")
        # for i, comment in enumerate(comments[:5], 1):
        #     print(f"{i}. @{comment['username']}: {comment['text'][:80]}...")

        # ============================================
        # OPTION 2: Scrape multiple specific posts
        # ============================================
        # print("\n[OPTION 2] Scraping multiple posts...")
        # post_urls = [
        #     "https://www.instagram.com/p/POST1/",
        #     "https://www.instagram.com/p/POST2/",
        # ]
        # results = scraper.scrape_multiple_posts(
        #     post_urls,
        #     max_comments_per_post=30,
        #     delay_between_posts=(15, 25)
        # )

        # ============================================
        # OPTION 3: Scrape ALL posts from a user
        # ============================================
        # print("\n[OPTION 3] Scraping all posts from user...")
        # results = scraper.scrape_user_posts(
        #     username="cristiano",           # Username tanpa @
        #     max_posts=20,                   # Jumlah post yang mau di-scrape
        #     max_comments_per_post=100,      # Max komentar per post
        #     delay_between_posts=(20, 40)    # Delay antar post (detik)
        # )
        #
        # # Summary
        # total_comments = sum(len(comments) for comments in results.values())
        # print(f"\n📊 Summary:")
        # print(f"   Total Posts Scraped: {len(results)}")
        # print(f"   Total Comments Collected: {total_comments}")

        # ============================================
        # Get statistics from database
        # ============================================
        stats = scraper.get_statistics()
        print(f"\n📈 Database Statistics:")
        print(f"   Total Posts: {stats['total_posts']}")
        print(f"   Total Comments: {stats['total_comments']}")
        print(f"   Unique Commenters: {stats['unique_commenters']}")
        print(f"\n🏆 Top Commenters:")
        for user in stats["top_commenters"]:
            print(f"   @{user['username']}: {user['comment_count']} comments")

    except Exception as e:
        print(f"\n❌ Error: {e}")

    finally:
        # Always close browser
        scraper.close()
