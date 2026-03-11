-- ============================================
-- Schema Database untuk Instagram Research Dataset
-- Database: PostgreSQL
-- ============================================

-- 1. Tabel Posts (Informasi Postingan)
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    post_id VARCHAR(50) UNIQUE NOT NULL,        -- Instagram post ID
    shortcode VARCHAR(20) UNIQUE NOT NULL,      -- Shortcode dari URL (CNBg--UguoF)
    post_url TEXT NOT NULL,
    username VARCHAR(100) NOT NULL,             -- Username pemilik post
    caption TEXT,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    posted_at TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Metadata tambahan dalam JSON
    metadata JSONB,                             -- Untuk data tambahan yang fleksibel

    -- Index untuk pencarian cepat
    CONSTRAINT unique_post_shortcode UNIQUE(shortcode)
);

-- 2. Tabel Comments (Komentar dari Postingan)
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    comment_id VARCHAR(50) UNIQUE NOT NULL,     -- Instagram comment ID
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,

    -- Data komentar
    username VARCHAR(100) NOT NULL,             -- Username pemberi komentar
    comment_text TEXT NOT NULL,
    likes_count INTEGER DEFAULT 0,

    -- Timestamp
    created_at TIMESTAMP,                       -- Waktu komentar dibuat di Instagram
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Parent comment untuk replies (nested comments)
    parent_comment_id VARCHAR(50),              -- NULL jika top-level comment

    -- Metadata tambahan
    metadata JSONB,

    -- Index untuk pencarian
    CONSTRAINT unique_comment_id UNIQUE(comment_id)
);

-- 3. Tabel Users (Optional - untuk tracking user profiles)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    bio TEXT,
    followers_count INTEGER,
    following_count INTEGER,
    posts_count INTEGER,
    is_verified BOOLEAN DEFAULT FALSE,
    profile_pic_url TEXT,

    -- Timestamp
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Metadata
    metadata JSONB
);

-- 4. Tabel Hashtags (Optional - untuk analisis hashtag)
CREATE TABLE hashtags (
    id SERIAL PRIMARY KEY,
    hashtag VARCHAR(100) UNIQUE NOT NULL,
    total_count INTEGER DEFAULT 1,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Junction Table: Post-Hashtag relationship
CREATE TABLE post_hashtags (
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    hashtag_id INTEGER REFERENCES hashtags(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, hashtag_id)
);

-- ============================================
-- INDEXES untuk Performance
-- ============================================

-- Index untuk posts
CREATE INDEX idx_posts_username ON posts(username);
CREATE INDEX idx_posts_scraped_at ON posts(scraped_at);
CREATE INDEX idx_posts_posted_at ON posts(posted_at);
CREATE INDEX idx_posts_metadata ON posts USING GIN(metadata);  -- GIN index untuk JSONB

-- Index untuk comments
CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_comments_username ON comments(username);
CREATE INDEX idx_comments_created_at ON comments(created_at);
CREATE INDEX idx_comments_parent_id ON comments(parent_comment_id);
CREATE INDEX idx_comments_text_search ON comments USING GIN(to_tsvector('english', comment_text));  -- Full-text search

-- Index untuk users
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_followers ON users(followers_count);

-- ============================================
-- VIEWS untuk Analisis Cepat
-- ============================================

-- View: Post dengan jumlah komentar actual
CREATE VIEW post_statistics AS
SELECT
    p.id,
    p.shortcode,
    p.username,
    p.caption,
    p.likes_count,
    COUNT(DISTINCT c.id) as actual_comments_count,
    p.posted_at,
    p.scraped_at
FROM posts p
LEFT JOIN comments c ON p.id = c.post_id
GROUP BY p.id;

-- View: Top commenters
CREATE VIEW top_commenters AS
SELECT
    username,
    COUNT(*) as comment_count,
    MIN(created_at) as first_comment,
    MAX(created_at) as last_comment
FROM comments
GROUP BY username
ORDER BY comment_count DESC;

-- View: Comments per day
CREATE VIEW comments_per_day AS
SELECT
    DATE(created_at) as date,
    COUNT(*) as total_comments,
    COUNT(DISTINCT username) as unique_users
FROM comments
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- ============================================
-- FUNCTIONS untuk Data Cleaning
-- ============================================

-- Function: Clean duplicate comments
CREATE OR REPLACE FUNCTION remove_duplicate_comments()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    WITH duplicates AS (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY comment_id
                   ORDER BY scraped_at DESC
               ) as rn
        FROM comments
    )
    DELETE FROM comments
    WHERE id IN (SELECT id FROM duplicates WHERE rn > 1);

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- SAMPLE QUERIES untuk Analisis
-- ============================================

-- Query 1: Total komentar per post
-- SELECT p.shortcode, p.caption, COUNT(c.id) as total_comments
-- FROM posts p
-- LEFT JOIN comments c ON p.id = c.post_id
-- GROUP BY p.id
-- ORDER BY total_comments DESC;

-- Query 2: Mencari komentar dengan kata kunci (Full-text search)
-- SELECT username, comment_text, created_at
-- FROM comments
-- WHERE to_tsvector('english', comment_text) @@ to_tsquery('english', 'amazing & beautiful');

-- Query 3: Analisis sentiment sederhana (positive words)
-- SELECT
--     COUNT(*) as positive_comments,
--     COUNT(*) * 100.0 / (SELECT COUNT(*) FROM comments) as percentage
-- FROM comments
-- WHERE comment_text ~* '\y(love|amazing|beautiful|great|awesome)\y';

-- Query 4: Waktu paling aktif untuk komentar
-- SELECT
--     EXTRACT(HOUR FROM created_at) as hour,
--     COUNT(*) as comment_count
-- FROM comments
-- GROUP BY hour
-- ORDER BY hour;

-- ============================================
-- MAINTENANCE
-- ============================================

-- Archive old data (optional)
-- CREATE TABLE comments_archive (LIKE comments INCLUDING ALL);
-- INSERT INTO comments_archive SELECT * FROM comments WHERE created_at < NOW() - INTERVAL '6 months';
-- DELETE FROM comments WHERE created_at < NOW() - INTERVAL '6 months';


-- ============================================
-- Instagram Account Management Schema
-- Database: PostgreSQL
-- Purpose: Track scraping accounts, bans, usage, and rotation
-- ============================================

-- 1. Tabel Instagram Accounts
CREATE TABLE instagram_accounts (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_encrypted TEXT NOT NULL,          -- Store encrypted password
    email VARCHAR(255),
    phone VARCHAR(50),

    -- Account Status
    status VARCHAR(20) DEFAULT 'active',       -- active, banned, suspended, rate_limited, inactive
    is_active BOOLEAN DEFAULT TRUE,
    is_banned BOOLEAN DEFAULT FALSE,

    -- Ban Information
    ban_reason TEXT,                           -- Alasan di-ban (jika ada)
    banned_at TIMESTAMP,                       -- Kapan di-ban
    ban_count INTEGER DEFAULT 0,               -- Jumlah kali di-ban
    last_ban_type VARCHAR(50),                 -- temporary, permanent, challenge_required

    -- Rate Limiting
    is_rate_limited BOOLEAN DEFAULT FALSE,
    rate_limited_at TIMESTAMP,
    rate_limit_expires_at TIMESTAMP,           -- Kapan rate limit selesai
    rate_limit_count INTEGER DEFAULT 0,        -- Berapa kali kena rate limit

    -- Usage Statistics
    total_requests INTEGER DEFAULT 0,          -- Total requests yang dibuat
    successful_requests INTEGER DEFAULT 0,     -- Requests yang sukses
    failed_requests INTEGER DEFAULT 0,         -- Requests yang gagal
    last_used_at TIMESTAMP,                    -- Terakhir digunakan
    last_success_at TIMESTAMP,                 -- Terakhir sukses scraping
    last_error_at TIMESTAMP,                   -- Terakhir error
    last_error_message TEXT,                   -- Error message terakhir

    -- Scraping Statistics (Daily)
    posts_scraped_today INTEGER DEFAULT 0,
    comments_scraped_today INTEGER DEFAULT 0,
    last_daily_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Account Health Score (0-100)
    health_score INTEGER DEFAULT 100,          -- Score kesehatan akun
    trust_level VARCHAR(20) DEFAULT 'new',     -- new, trusted, veteran, risky, untrusted

    -- Account Creation Info
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Account Age & Reliability
    account_age_days INTEGER,                  -- Umur akun Instagram (hari)
    follower_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE,
    is_business BOOLEAN DEFAULT FALSE,

    -- Session Management
    session_file TEXT,                         -- Path ke session file
    session_expires_at TIMESTAMP,

    -- Proxy Information (optional)
    proxy_host VARCHAR(255),
    proxy_port INTEGER,
    proxy_username VARCHAR(100),
    proxy_type VARCHAR(20),                    -- http, socks5, residential

    -- Notes
    notes TEXT,
    tags TEXT[],                               -- Array untuk categorization

    -- Metadata
    metadata JSONB DEFAULT '{}'::JSONB
);

-- 2. Tabel Account Usage Log (History penggunaan)
CREATE TABLE account_usage_logs (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES instagram_accounts(id) ON DELETE CASCADE,

    -- Activity Info
    action_type VARCHAR(50) NOT NULL,          -- login, scrape_posts, scrape_comments, get_user_info
    target_username VARCHAR(100),              -- Username yang di-scrape

    -- Result
    status VARCHAR(20) NOT NULL,               -- success, failed, rate_limited, banned
    error_message TEXT,
    error_type VARCHAR(50),                    -- rate_limit, login_failed, checkpoint, etc

    -- Metrics
    items_scraped INTEGER DEFAULT 0,           -- Jumlah items yang berhasil di-scrape
    duration_seconds INTEGER,                  -- Durasi operasi

    -- Timestamp
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,

    -- Metadata
    metadata JSONB DEFAULT '{}'::JSONB
);

-- 3. Tabel Account Health History
CREATE TABLE account_health_history (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES instagram_accounts(id) ON DELETE CASCADE,

    health_score INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,

    -- Reason for score change
    reason TEXT,
    score_change INTEGER,                      -- +10, -20, etc

    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tabel Account Rotation Queue
CREATE TABLE account_rotation_queue (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES instagram_accounts(id) ON DELETE CASCADE,

    priority INTEGER DEFAULT 0,                -- Higher = higher priority
    last_rotated_at TIMESTAMP,
    next_available_at TIMESTAMP,               -- Kapan bisa digunakan lagi

    is_in_cooldown BOOLEAN DEFAULT FALSE,
    cooldown_until TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(account_id)
);

-- ============================================
-- INDEXES untuk Performance
-- ============================================

-- Indexes untuk instagram_accounts
CREATE INDEX idx_accounts_status ON instagram_accounts(status);
CREATE INDEX idx_accounts_is_active ON instagram_accounts(is_active);
CREATE INDEX idx_accounts_is_banned ON instagram_accounts(is_banned);
CREATE INDEX idx_accounts_health_score ON instagram_accounts(health_score);
CREATE INDEX idx_accounts_last_used ON instagram_accounts(last_used_at);
CREATE INDEX idx_accounts_trust_level ON instagram_accounts(trust_level);
CREATE INDEX idx_accounts_tags ON instagram_accounts USING GIN(tags);

-- Indexes untuk usage logs
CREATE INDEX idx_usage_logs_account_id ON account_usage_logs(account_id);
CREATE INDEX idx_usage_logs_action_type ON account_usage_logs(action_type);
CREATE INDEX idx_usage_logs_status ON account_usage_logs(status);
CREATE INDEX idx_usage_logs_started_at ON account_usage_logs(started_at);

-- Indexes untuk health history
CREATE INDEX idx_health_history_account_id ON account_health_history(account_id);
CREATE INDEX idx_health_history_recorded_at ON account_health_history(recorded_at);

-- Indexes untuk rotation queue
CREATE INDEX idx_rotation_queue_priority ON account_rotation_queue(priority DESC);
CREATE INDEX idx_rotation_queue_next_available ON account_rotation_queue(next_available_at);

-- ============================================
-- VIEWS untuk Query Cepat
-- ============================================

-- View: Active accounts yang bisa digunakan
CREATE VIEW available_accounts AS
SELECT
    id,
    username,
    status,
    health_score,
    trust_level,
    last_used_at,
    posts_scraped_today,
    comments_scraped_today
FROM instagram_accounts
WHERE is_active = TRUE
  AND is_banned = FALSE
  AND is_rate_limited = FALSE
  AND status = 'active'
  AND health_score > 30
ORDER BY
    health_score DESC,
    last_used_at ASC NULLS FIRST;

-- View: Banned accounts
CREATE VIEW banned_accounts AS
SELECT
    id,
    username,
    ban_reason,
    banned_at,
    ban_count,
    last_ban_type,
    health_score
FROM instagram_accounts
WHERE is_banned = TRUE
ORDER BY banned_at DESC;

-- View: Account performance statistics
CREATE VIEW account_performance AS
SELECT
    a.id,
    a.username,
    a.status,
    a.health_score,
    a.total_requests,
    a.successful_requests,
    a.failed_requests,
    CASE
        WHEN a.total_requests > 0
        THEN ROUND((a.successful_requests::NUMERIC / a.total_requests * 100), 2)
        ELSE 0
    END as success_rate,
    a.posts_scraped_today,
    a.comments_scraped_today,
    a.last_used_at,
    COUNT(l.id) as total_logs,
    COUNT(CASE WHEN l.status = 'success' THEN 1 END) as successful_operations
FROM instagram_accounts a
LEFT JOIN account_usage_logs l ON a.id = l.account_id
GROUP BY a.id, a.username, a.status, a.health_score, a.total_requests,
         a.successful_requests, a.failed_requests, a.posts_scraped_today,
         a.comments_scraped_today, a.last_used_at;

-- View: Accounts needing attention
CREATE VIEW accounts_needing_attention AS
SELECT
    id,
    username,
    status,
    health_score,
    CASE
        WHEN is_banned THEN 'Banned'
        WHEN is_rate_limited THEN 'Rate Limited'
        WHEN health_score < 30 THEN 'Low Health'
        WHEN status = 'suspended' THEN 'Suspended'
        WHEN last_used_at < NOW() - INTERVAL '7 days' THEN 'Inactive'
        ELSE 'Unknown'
    END as attention_reason,
    last_used_at,
    last_error_message
FROM instagram_accounts
WHERE is_banned = TRUE
   OR is_rate_limited = TRUE
   OR health_score < 30
   OR status IN ('suspended', 'rate_limited')
   OR (last_used_at < NOW() - INTERVAL '7 days' AND is_active = TRUE)
ORDER BY health_score ASC;

-- ============================================
-- FUNCTIONS
-- ============================================

-- Function: Update health score
CREATE OR REPLACE FUNCTION update_account_health_score(
    p_account_id INTEGER,
    p_score_change INTEGER,
    p_reason TEXT
)
RETURNS VOID AS $$
DECLARE
    v_current_score INTEGER;
    v_new_score INTEGER;
BEGIN
    -- Get current score
    SELECT health_score INTO v_current_score
    FROM instagram_accounts
    WHERE id = p_account_id;

    -- Calculate new score (min 0, max 100)
    v_new_score := GREATEST(0, LEAST(100, v_current_score + p_score_change));

    -- Update account
    UPDATE instagram_accounts
    SET health_score = v_new_score,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_account_id;

    -- Log to history
    INSERT INTO account_health_history (account_id, health_score, status, reason, score_change)
    SELECT id, v_new_score, status, p_reason, p_score_change
    FROM instagram_accounts
    WHERE id = p_account_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Mark account as banned
CREATE OR REPLACE FUNCTION mark_account_banned(
    p_account_id INTEGER,
    p_ban_reason TEXT,
    p_ban_type VARCHAR(50) DEFAULT 'temporary'
)
RETURNS VOID AS $$
BEGIN
    UPDATE instagram_accounts
    SET is_banned = TRUE,
        is_active = FALSE,
        status = 'banned',
        ban_reason = p_ban_reason,
        banned_at = CURRENT_TIMESTAMP,
        ban_count = ban_count + 1,
        last_ban_type = p_ban_type,
        health_score = 0,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_account_id;

    -- Log to history
    INSERT INTO account_health_history (account_id, health_score, status, reason, score_change)
    VALUES (p_account_id, 0, 'banned', p_ban_reason, -100);
END;
$$ LANGUAGE plpgsql;

-- Function: Reset daily counters
CREATE OR REPLACE FUNCTION reset_daily_counters()
RETURNS VOID AS $$
BEGIN
    UPDATE instagram_accounts
    SET posts_scraped_today = 0,
        comments_scraped_today = 0,
        last_daily_reset = CURRENT_TIMESTAMP
    WHERE last_daily_reset < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

-- Function: Get best available account
CREATE OR REPLACE FUNCTION get_best_available_account()
RETURNS TABLE (
    account_id INTEGER,
    username VARCHAR(100),
    health_score INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT id, instagram_accounts.username, instagram_accounts.health_score
    FROM instagram_accounts
    WHERE is_active = TRUE
      AND is_banned = FALSE
      AND is_rate_limited = FALSE
      AND status = 'active'
      AND health_score > 30
    ORDER BY
        health_score DESC,
        posts_scraped_today ASC,
        last_used_at ASC NULLS FIRST
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- TRIGGERS
-- ============================================

-- Trigger: Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_accounts_updated_at
    BEFORE UPDATE ON instagram_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- SAMPLE DATA (untuk testing)
-- ============================================

-- Insert sample accounts (JANGAN GUNAKAN PASSWORD REAL!)
-- INSERT INTO instagram_accounts (username, password_encrypted, status, health_score, trust_level)
-- VALUES
--     ('scraper_account_01', 'ENCRYPTED_PASSWORD_HERE', 'active', 95, 'trusted'),
--     ('scraper_account_02', 'ENCRYPTED_PASSWORD_HERE', 'active', 88, 'trusted'),
--     ('scraper_account_03', 'ENCRYPTED_PASSWORD_HERE', 'banned', 0, 'untrusted');

-- ============================================
-- SAMPLE QUERIES
-- ============================================

-- Query 1: Lihat semua akun yang available
-- SELECT * FROM available_accounts;

-- Query 2: Lihat akun dengan performa terbaik
-- SELECT * FROM account_performance
-- WHERE success_rate > 80
-- ORDER BY success_rate DESC, total_requests DESC;

-- Query 3: Lihat akun yang perlu perhatian
-- SELECT * FROM accounts_needing_attention;

-- Query 4: Get best account untuk scraping
-- SELECT * FROM get_best_available_account();

-- Query 5: Update health score
-- SELECT update_account_health_score(1, -10, 'Rate limited');

-- Query 6: Mark account sebagai banned
-- SELECT mark_account_banned(3, 'Too many requests', 'permanent');

-- Query 7: Reset daily counters (jalankan setiap hari)
-- SELECT reset_daily_counters();

-- Query 8: Statistik usage per hari
-- SELECT
--     DATE(started_at) as date,
--     COUNT(*) as total_operations,
--     COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
--     COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
-- FROM account_usage_logs
-- GROUP BY DATE(started_at)
-- ORDER BY date DESC;
