
# 필요한 라이브러리 설치
try:
    from transformers import pipeline
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "transformers"])
    from transformers import pipeline

import requests
import json
from datetime import datetime
import os
import logging

# API 키 설정 (GitHub Secrets에서 불러오기)
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

# 뉴스 검색
query = "코인 OR 비트코인 OR 알트코인 OR 스테이블코인 OR bitcoin OR 이더리움 OR btc OR 암호화폐 OR 밈코인"
naver_url = "https://openapi.naver.com/v1/search/news.json"
headers = {
    "X-Naver-Client-Id": NAVER_CLIENT_ID,
    "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
}
params = {
    "query": query,
    "display": 10,
    "sort": "date"
}
response = requests.get(naver_url, headers=headers, params=params)
articles = response.json().get('items', [])

# 요약 
summarizer = pipeline("summarization")

news_data = []
for article in articles:
    try:
        content = f"{article['title']} {article['description']}"
        summary = summarizer(content, max_length=60, min_length=30, do_sample=False)[0]['summary_text']
        news_data.append({
            "title": article['title'],
            "link": article['link'],
            "pubDate": article['pubDate'],
            "summary": summary
        })
    except Exception as e:
        logger.error(f"요약 실패: {e}, article: {article}")


# Notion 업로드
notion_url = "https://api.notion.com/v1/pages"
notion_headers = {
    "Authorization": f"Bearer {NOTION_API_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

for item in news_data:
    notion_data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Date": {"date": {"start": item['pubDate']}}, # 날짜 형식 변경
            "Title": {"title": [{"text": {"content": item['title']}}]},
            "Article Summary": {"rich_text": [{"text": {"content": item['summary']}}]},
            "Source URL": {"url": item['link']}
        }
    }

logger.debug(f"NOTION_API_TOKEN: {NOTION_API_TOKEN}")
logger.debug(f"DATABASE_ID: {DATABASE_ID}")

notion_response = requests.post(notion_url, headers=notion_headers, data=json.dumps(data))
print(notion_response.status_code)
print(notion_response.json())
print(f"Notion 업로드 결과 (title: {item['title']}): {notion_response.status_code}, {notion_response.json()}")
