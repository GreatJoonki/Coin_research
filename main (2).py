
import os
import json
import html
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# 환경 변수
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

def fetch_news(query="하남 교산", display=5):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {
        "query": query,
        "display": display,
        "sort": "date"
    }
    response = requests.get(url, headers=headers, params=params)
    response.encoding = 'utf-8'
    return response.json().get('items', [])

def clean_text(text):
    return html.unescape(BeautifulSoup(text, "html.parser").get_text())

def upload_to_notion(article_links):
    notion_url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    content = "\n".join([f"{title}\n{link}" for title, link in article_links])

    data = {
        "parent": { "database_id": DATABASE_ID },
        "properties": {
            "Date": {
                "title": [{"text": {"content": datetime.now().strftime("%Y-%m-%d")}}]
            },
            "Article Links": {
                "rich_text": [{"text": {"content": content}}]
            }
        }
    }

    response = requests.post(notion_url, headers=headers, data=json.dumps(data))
    print(response.status_code)
    print(response.json())

def main():
    articles = fetch_news()
    article_links = [(clean_text(a['title']), a['link']) for a in articles]
    upload_to_notion(article_links)

if __name__ == "__main__":
    main()
