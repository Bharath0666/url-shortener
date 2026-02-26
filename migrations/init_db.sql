-- =============================================================
-- URL Shortener Database Schema
-- =============================================================

CREATE DATABASE IF NOT EXISTS url_shortener
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE url_shortener;

-- ----- URLs table -----
CREATE TABLE IF NOT EXISTS urls (
    id          BIGINT          AUTO_INCREMENT PRIMARY KEY,
    short_code  VARCHAR(10)     NOT NULL,
    original_url TEXT           NOT NULL,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at  DATETIME        NULL,
    is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
    click_count BIGINT          NOT NULL DEFAULT 0,

    UNIQUE INDEX idx_short_code (short_code),
    INDEX idx_created_at (created_at),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----- Click analytics / logs table -----
CREATE TABLE IF NOT EXISTS click_logs (
    id          BIGINT          AUTO_INCREMENT PRIMARY KEY,
    url_id      BIGINT          NOT NULL,
    ip_address  VARCHAR(45)     NOT NULL,          -- supports IPv6
    user_agent  TEXT            NULL,
    referer     TEXT            NULL,
    clicked_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_url_id (url_id),
    INDEX idx_clicked_at (clicked_at),

    CONSTRAINT fk_click_url
        FOREIGN KEY (url_id) REFERENCES urls(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
