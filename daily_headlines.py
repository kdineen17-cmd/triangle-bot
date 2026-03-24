import requests
import os
from datetime import datetime

# ====================== CONFIG (from GitHub Secrets) ======================
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")
BLOG_ID = os.getenv("BLOG_ID")

# Basic check if secrets are loaded
if not all([NEWSAPI_KEY, GROQ_API_KEY, CLIENT_ID, CLIENT_SECRET, SHOPIFY_STORE, BLOG_ID]):
    print("❌ ERROR: Missing secrets! Check GitHub Secrets.")
    exit(1)

print("Starting Daily Triangle Emporium Headlines Bot...")

# 1. Get Shopify access token
print("Getting Shopify access token...")
token_url = f"https://{SHOPIFY_STORE}/admin/oauth/access_token"
token_data = {
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET
}
token_response = requests.post(token_url, data=token_data)
token_response.raise_for_status()
access_token = token_response.json()["access_token"]
print("✅ Access token obtained")

# 2. Fetch headlines
print("Fetching headlines...")
news_response = requests.get("https://newsapi.org/v2/top-headlines", params={
    "country": "us",
    "category": "business",
    "pageSize": 8,
    "apiKey": NEWSAPI_KEY
})
articles = news_response.json()["articles"][:5]

# 3. Build prompt with Triangle Emporium tone
headlines_text = "\n".join([f"- {a['title']} ({a['source']['name']})" for a in articles])

prompt = f"""
You are the official voice of Triangle Emporium and the Triangle Method.
Tone: motivational but grounded, structured like the Triangle Method (Clarity → Creativity → Accountability), witty with light triangle metaphors, concise, actionable.
Always end with a small reflection question or worksheet nudge.

Today's date is {datetime.now().strftime('%B %d, %Y')}.

Rewrite these 5 headlines into ONE engaging daily blog post titled:
"Daily Triangle Headlines – {datetime.now().strftime('%B %d, %Y')}"

Format:
- Catchy intro paragraph welcoming readers to Triangle Emporium
- Then 5 short sections (one per headline) with the rewritten title as H2
- Each section 2-3 sentences in Triangle tone
- End with a Triangle reflection question + CTA to shop at triangleshirt.com

Headlines:
{headlines_text}
"""

# 4. Call Groq AI
print("Rewriting with AI...")
ai_response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
    json={"model": "llama3-70b-8192", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
).json()

blog_body = ai_response["choices"][0]["message"]["content"]

# 5. Publish to Shopify
print("Publishing to Shopify...")
result = requests.post(
    f"https://{SHOPIFY_STORE}/admin/api/2026-01/blogs/{BLOG_ID}/articles.json",
    headers={"X-Shopify-Access-Token": access_token, "Content-Type": "application/json"},
    json={
        "article": {
            "title": f"Daily Triangle Headlines – {datetime.now().strftime('%B %d, %Y')}",
            "body_html": blog_body,
            "tags": "daily-headlines,ai-news,triangle-method",
            "published": True
        }
    }
)

if result.status_code in (201, 200):
    print("✅ SUCCESS! New blog post published to Triangle Emporium")
else:
    print("❌ Error publishing:", result.status_code, result.text)
