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

# 1. Fetch real headlines
print("Fetching headlines...")
news_response = requests.get("https://newsapi.org/v2/top-headlines", params={
    "country": "us",
    "category": "business",        # You can change to "technology", "general", etc.
    "pageSize": 10,
    "apiKey": NEWSAPI_KEY
})
if news_response.status_code != 200:
    print("❌ NewsAPI Error:", news_response.text)
    exit(1)

articles = news_response.json()["articles"][:6]

# 2. Improved prompt - forces real headlines + Triangle tone
headlines_text = "\n".join([f"Original: {a['title']} - {a['description'] or ''} (Source: {a['source']['name']})" for a in articles])

prompt = f"""
You are the official voice of Triangle Emporium.

Task: Rewrite these 6 real news headlines into engaging daily content using the Triangle Method tone.

Rules:
- Stay very close to the original facts and meaning. Do not invent details.
- Use the Triangle Method structure: Clarity → Creativity → Accountability where natural.
- Add light triangle metaphors only when they fit naturally.
- Make it motivational but grounded and actionable.
- Keep each section concise (2-4 sentences max).

Today's date is {datetime.now().strftime('%B %d, %Y')}.

Here are the real headlines:

{headlines_text}

Format the output exactly like this:

**Daily Triangle Headlines – {datetime.now().strftime('%B %d, %Y')}**

[One short, powerful intro sentence welcoming readers to Triangle Emporium]

### [Rewritten Headline 1]
[2-4 sentences in Triangle tone]

### [Rewritten Headline 2]
[2-4 sentences...]

... do all 6

---
What are you focusing on today?
Shop the latest tools for building better systems at triangleshirt.com
"""

# 3. Call Groq
print("Rewriting with AI...")
groq_response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
    json={
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.65,
        "max_tokens": 2200
    }
)

if groq_response.status_code != 200:
    print("❌ Groq Error:", groq_response.text)
    exit(1)

content = groq_response.json()["choices"][0]["message"]["content"]

# 4. Update Google Doc (safe version)
print("Updating Google Doc...")
credentials_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
credentials = service_account.Credentials.from_service_account_info(credentials_info, scopes=['https://www.googleapis.com/auth/documents'])
service = build('docs', 'v1', credentials=credentials)

doc = service.documents().get(documentId=GOOGLE_DOC_ID).execute()
current_length = doc.get('body', {}).get('content', [{}])[-1].get('endIndex', 1)

requests_list = [
    {'deleteContentRange': {'range': {'startIndex': 1, 'endIndex': max(current_length - 1, 1)}}},
    {'insertText': {'location': {'index': 1}, 'text': content}}
]

service.documents().batchUpdate(documentId=GOOGLE_DOC_ID, body={'requests': requests_list}).execute()

print("✅ Google Doc updated successfully!")
print(f"📄 Link: https://docs.google.com/document/d/{GOOGLE_DOC_ID}/edit")
