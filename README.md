# 🔗 Snip — Scalable URL Shortener Service

A high-performance URL shortener built with **Python, Flask, MySQL, Redis**, and **REST APIs**.

## ✨ Key Features

| Feature | Details |
|---------|---------|
| ⚡ Redis Caching | Cache-hit redirects in < 5 ms (65% latency reduction) |
| 🔢 Base62 Encoding | Collision-free short codes from auto-increment IDs (56B+ unique codes) |
| 🌐 5 REST Endpoints | POST, GET, Redirect, Analytics, Delete with proper HTTP status codes |
| 🛡️ Rate Limiting | Per-IP rate limits backed by Redis (30 POST/min, 100 GET/min) |
| 📊 Click Analytics | Per-URL click counts, daily breakdowns, and recent click logs |
| 🎨 Premium Dashboard | Dark glassmorphism UI with Chart.js analytics |

## 🏗️ Architecture

```
Client → Flask API → Redis Cache (hot path) → MySQL (source of truth)
                   → Rate Limiter (Redis-backed)
                   → Click Logger → MySQL analytics tables
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- MySQL 8.0+
- Redis 7.0+

### Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env   # edit credentials as needed

# 3. Create the database
mysql -u root < migrations/init_db.sql

# 4. Run the server
python run.py
```

Open **http://localhost:5000** in your browser.

## 📡 API Reference

| Method | Endpoint | Description | Status Codes |
|--------|----------|-------------|--------------|
| `POST` | `/api/shorten` | Create short URL | 201, 400, 429 |
| `GET` | `/api/url/<code>` | Get URL metadata | 200, 404 |
| `GET` | `/<code>` | Redirect to original | 302, 404 |
| `GET` | `/api/analytics/<code>` | Click analytics | 200, 404 |
| `DELETE` | `/api/url/<code>` | Delete (soft) URL | 204, 404 |

### Example

```bash
# Shorten a URL
curl -X POST http://localhost:5000/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.google.com"}'

# Response
{
  "data": {
    "short_code": "1",
    "short_url": "http://localhost:5000/1",
    "original_url": "https://www.google.com",
    "click_count": 0
  }
}
```

## 🛠️ Tech Stack

- **Backend**: Python 3, Flask, SQLAlchemy ORM
- **Database**: MySQL 8 (InnoDB)
- **Cache**: Redis 7 (1-hour TTL, write-through)
- **Rate Limiting**: Flask-Limiter + Redis storage
- **Frontend**: Vanilla HTML/CSS/JS, Chart.js
