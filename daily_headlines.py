import requests
import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ====================== CONFIG ======================
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID")

print("Starting Daily Triangle Emporium Headlines Bot...")

# 1. Fetch headlines
print("Fetching headlines...")
news_response = requests.get("https://newsapi.org/v2/top-headlines", params={
    "country": "us",
    "category": "business",
    "pageSize": 8,
    "apiKey": NEWSAPI_KEY
})
if news_response.status_code != 200:
    print("❌ NewsAPI Error:", news_response.text)
    exit(1)

articles = news_response.json()["articles"][:6]

# 2. Build prompt
headlines_text = "\n".join([f"- {a['title']} ({a['source']['name']})" for a in articles])

prompt = f"""
You are the official voice of Triangle Emporium and the Triangle Method.
Tone: motivational but grounded, structured like the Triangle Method (Clarity → Creativity → Accountability), witty with light triangle metaphors, concise, actionable.
Always end with a small reflection question or worksheet nudge.

Today's date is {datetime.now().strftime('%B %d, %Y')}.

Create a clean, well-formatted daily post with these 6 headlines.

Format exactly like this:

**Daily Triangle Headlines – {datetime.now().strftime('%B %d, %Y')}**

[Short welcoming intro paragraph for Triangle Emporium readers]

### Headline 1
[Rewritten 2-4 sentences in Triangle tone]

### Headline 2
[Rewritten...]

... continue for all 6

At the very end add:
---
What Triangle are you focusing on today? Clarity, Creativity, or Accountability?
Shop the latest at triangleshirt.com
"""

# 3. Generate content with Groq (using current model)
print("Rewriting with AI...")
groq_response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "llama-3.3-70b-versatile",   # ← Updated working model
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000
    }
)

print("Groq Status Code:", groq_response.status_code)

if groq_response.status_code != 200:
    print("❌ Groq API Error:", groq_response.text)
    exit(1)

ai_response = groq_response.json()
content = ai_response["choices"][0]["message"]["content"]

# 4. Update Google Doc
print("Updating Google Doc...")
credentials_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
credentials = service_account.Credentials.from_service_account_info(
    credentials_info, 
    scopes=['https://www.googleapis.com/auth/documents']
)
service = build('docs', 'v1', credentials=credentials)

requests_list = [
    {'deleteContentRange': {'range': {'startIndex': 1, 'endIndex': 999999}}},
    {'insertText': {'location': {'index': 1}, 'text': content}}
]

service.documents().batchUpdate(documentId=GOOGLE_DOC_ID, body={'requests': requests_list}).execute()

print("✅ Google Doc updated successfully!")
print(f"\n📄 View your Daily Triangle Headlines here:")
print(f"https://docs.google.com/document/d/{GOOGLE_DOC_ID}/edit")
