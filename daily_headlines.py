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
articles = news_response.json()["articles"][:6]

# 2. Build prompt with your Triangle tone
headlines_text = "\n".join([f"- {a['title']} ({a['source']['name']})" for a in articles])

prompt = f"""
You are the official voice of Triangle Emporium and the Triangle Method.
Tone: motivational but grounded, structured like the Triangle Method (Clarity → Creativity → Accountability), witty with light triangle metaphors, concise, actionable.
Always end with a small reflection question or worksheet nudge.

Today's date is {datetime.now().strftime('%B %d, %Y')}.

Create a clean, well-formatted daily post with these 6 headlines.

Format exactly like this:

**Daily Triangle Headlines – {datetime.now().strftime('%B %d, %Y')}**

[Short welcoming intro paragraph]

### Headline 1
[Rewritten story in Triangle tone - 2-4 sentences]

### Headline 2
[Rewritten story...]

... (do all 6)

At the very end add:
---
What Triangle are you focusing on today? Clarity, Creativity, or Accountability?
Shop the latest at triangleshirt.com
"""

# 3. Generate content with Groq
print("Rewriting with AI...")
ai_response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
    json={"model": "llama3-70b-8192", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
).json()

content = ai_response["choices"][0]["message"]["content"]

# 4. Update Google Doc
print("Updating Google Doc...")
credentials_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
credentials = service_account.Credentials.from_service_account_info(credentials_info, scopes=['https://www.googleapis.com/auth/documents'])
service = build('docs', 'v1', credentials=credentials)

# Clear the document and insert new content
requests_list = [
    {'deleteContentRange': {'range': {'startIndex': 1, 'endIndex': 999999}}},
    {'insertText': {'location': {'index': 1}, 'text': content}}
]

service.documents().batchUpdate(documentId=GOOGLE_DOC_ID, body={'requests': requests_list}).execute()

print("✅ Google Doc updated successfully")

# 5. Print summary for email
print("\n" + "="*50)
print("DAILY TRIANGLE HEADLINES READY")
print("="*50)
print(content)
print("\nGoogle Doc: https://docs.google.com/document/d/" + GOOGLE_DOC_ID)
