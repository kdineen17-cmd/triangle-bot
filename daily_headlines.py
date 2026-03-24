import requests
from datetime import datetime

# ====================== CONFIG ======================
NEWSAPI_KEY = "YOUR_NEWSAPI_KEY_HERE"
GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE"
SHOPIFY_STORE = "triangleshirt.myshopify.com"
CLIENT_ID = "YOUR_CLIENT_ID_HERE"
CLIENT_SECRET = "YOUR_CLIENT_SECRET_HERE"
BLOG_ID = 123456789   # ← CHANGE TO YOUR REAL BLOG ID
# ===================================================

print("Starting Daily Triangle Headlines Bot...")

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

# 3. Build prompt with your Triangle tone
headlines_text = "\n".join([f"- {a['title']} ({a['source']['name']})" for a in articles])

prompt = f"""
You are the official voice of Triangle Emporium and the Triangle Method.
Tone: motivational but grounded, structured like the Triangle Method (Clarity → Creativity → Accountability), witty with light triangle metaphors, concise, actionable.
Always end with a small reflection question or worksheet nudge.

Today's date is {datetime.now().strftime('%B %d, %Y')}.

Rewrite these 5 headlines into ONE engaging daily blog post titled: "Daily Triangle Headlines – {datetime.now().strftime('%B %d, %Y')}"

Format:
- Catchy intro paragraph
- Then 5 short sections (one per headline) with the rewritten title as H2
- Each section 2-3 sentences
- End with a Triangle reflection question + CTA to shop triangleshirt.com

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
    print("✅ SUCCESS! New blog post published to triangleshirt.com")
else:
    print("❌ Error:", result.status_code, result.text)
