"""
API Endpoint Test Script - tests all 5 REST endpoints.
"""

import requests
import time
import json

BASE = "http://127.0.0.1:5000"

def sep(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ---- 1. POST /api/shorten ----
sep("1. POST /api/shorten  (Create short URL)")
r = requests.post(f"{BASE}/api/shorten", json={"url": "https://www.google.com"})
print(f"Status: {r.status_code}")
data = r.json()
print(json.dumps(data, indent=2))
short_code = data["data"]["short_code"]
short_url  = data["data"]["short_url"]
print(f"=> short_code = {short_code}")
assert r.status_code == 201, f"Expected 201, got {r.status_code}"
print("[PASS]")

# ---- Test validation (bad URL) ----
sep("1b. POST /api/shorten  (Invalid URL - expect 400)")
r2 = requests.post(f"{BASE}/api/shorten", json={"url": "not-a-url"})
print(f"Status: {r2.status_code}")
print(json.dumps(r2.json(), indent=2))
assert r2.status_code == 400, f"Expected 400, got {r2.status_code}"
print("[PASS]")

# ---- 2. GET /api/url/<code> ----
sep("2. GET /api/url/<code>  (Get URL metadata)")
r3 = requests.get(f"{BASE}/api/url/{short_code}")
print(f"Status: {r3.status_code}")
print(json.dumps(r3.json(), indent=2))
assert r3.status_code == 200, f"Expected 200, got {r3.status_code}"
print("[PASS]")

# ---- 3. GET /<code>  (Redirect - expect 302) ----
sep("3. GET /<code>  (Redirect to original URL)")
r4 = requests.get(f"{BASE}/{short_code}", allow_redirects=False)
print(f"Status: {r4.status_code}")
print(f"Location: {r4.headers.get('Location')}")
assert r4.status_code == 302, f"Expected 302, got {r4.status_code}"
assert r4.headers.get("Location") == "https://www.google.com"
print("[PASS]")

# ---- 3b. Redirect again to test Redis cache hit ----
sep("3b. GET /<code>  (Second redirect - should be CACHE HIT)")
start = time.perf_counter_ns()
r5 = requests.get(f"{BASE}/{short_code}", allow_redirects=False)
elapsed = (time.perf_counter_ns() - start) / 1_000_000
print(f"Status: {r5.status_code}")
print(f"Location: {r5.headers.get('Location')}")
print(f"Latency: {elapsed:.2f} ms")
assert r5.status_code == 302
print("[PASS]")

# ---- 4. GET /api/analytics/<code> ----
sep("4. GET /api/analytics/<code>  (Click analytics)")
r6 = requests.get(f"{BASE}/api/analytics/{short_code}")
print(f"Status: {r6.status_code}")
print(json.dumps(r6.json(), indent=2))
assert r6.status_code == 200
total_clicks = r6.json()["data"]["total_clicks"]
print(f"=> total_clicks = {total_clicks}")
assert total_clicks >= 2, f"Expected >= 2 clicks, got {total_clicks}"
print("[PASS]")

# ---- 5. DELETE /api/url/<code> ----
sep("5. DELETE /api/url/<code>  (Soft-delete)")
r7 = requests.delete(f"{BASE}/api/url/{short_code}")
print(f"Status: {r7.status_code}")
assert r7.status_code == 204, f"Expected 204, got {r7.status_code}"
print("[PASS]")

# ---- 5b. Confirm deletion ----
sep("5b. GET /api/url/<code>  (After delete - expect 404)")
r8 = requests.get(f"{BASE}/api/url/{short_code}")
print(f"Status: {r8.status_code}")
assert r8.status_code == 404, f"Expected 404, got {r8.status_code}"
print("[PASS]")

# ---- Summary ----
sep("ALL TESTS PASSED")
print("  1. POST /api/shorten         -> 201  [PASS]")
print("  1b. POST (invalid)           -> 400  [PASS]")
print("  2. GET /api/url/<code>       -> 200  [PASS]")
print("  3. GET /<code> (redirect)    -> 302  [PASS]")
print("  3b. GET /<code> (cache hit)  -> 302  [PASS]")
print("  4. GET /api/analytics/<code> -> 200  [PASS]")
print("  5. DELETE /api/url/<code>    -> 204  [PASS]")
print("  5b. GET after delete         -> 404  [PASS]")
