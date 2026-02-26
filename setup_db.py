#!/usr/bin/env python3
"""
Database setup script — creates the url_shortener database and tables.
Run this once before starting the app.
"""

import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "url_shortener")


def setup_database():
    """Create the database if it doesn't exist, then create tables."""
    # Connect without specifying a database
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        charset="utf8mb4",
    )

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cursor.execute(f"USE `{MYSQL_DATABASE}`")

            cursor.execute("""
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS click_logs (
                    id          BIGINT          AUTO_INCREMENT PRIMARY KEY,
                    url_id      BIGINT          NOT NULL,
                    ip_address  VARCHAR(45)     NOT NULL,
                    user_agent  TEXT            NULL,
                    referer     TEXT            NULL,
                    clicked_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_url_id (url_id),
                    INDEX idx_clicked_at (clicked_at),
                    CONSTRAINT fk_click_url
                        FOREIGN KEY (url_id) REFERENCES urls(id)
                        ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

        conn.commit()
        print(f"[OK] Database '{MYSQL_DATABASE}' and tables created successfully!")
        print(f"    Host: {MYSQL_HOST}:{MYSQL_PORT}")
        print(f"    User: {MYSQL_USER}")

    except pymysql.err.OperationalError as e:
        print(f"[ERROR] MySQL connection failed: {e}")
        print(f"    Check your MYSQL_* settings in .env")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    setup_database()
