
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
query = "굿보이 박보검"
naver_url = "https://openapi.naver.com/v1/search/news.json"
headers = {
    "X-Naver-Client-Id": NAVER_CLIENT_ID,
    "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
}
params = {
    "query": query,
    "display": 5,
    "sort": "date"
}
response = requests.get(naver_url, headers=headers, params=params)
articles = response.json().get('items', [])

# 요약 및 감성 분석
summarizer = pipeline("summarization")
sentiment_analyzer = pipeline("sentiment-analysis")

summaries = []
sentiments = []
for article in articles:
    content = f"{article['title']} {article['description']}"
    summary = summarizer(content, max_length=60, min_length=30, do_sample=False)[0]['summary_text']
    sentiment = sentiment_analyzer(summary)[0]
    summaries.append(summary)
    sentiments.append(sentiment)

# 감성 통계
total = len(sentiments)
if total > 0:
    positive = sum(1 for s in sentiments if s['label'] == 'POSITIVE')
    negative = sum(1 for s in sentiments if s['label'] == 'NEGATIVE')
    viewer_sentiment = {
        "positive": f"{positive / total * 100:.1f}%",
        "negative": f"{negative / total * 100:.1f}%",
        "neutral": "N/A",
        "keywords": ["#굿보이", "#박보검"]
    }
else:
    viewer_sentiment = {
        "positive": "0%",
        "negative": "0%",
        "neutral": "100%",
        "keywords": ["#굿보이", "#박보검"]
    }

# 회차 요약
episode_summary = [
    "윤동주(박보검)는 첫 출근 날부터 범죄 현장을 마주하고, 복싱 본능으로 범인을 제압한다.",
    "지한나(김소현)는 냉철한 판단력으로 사건의 단서를 포착하며 첫 호흡을 맞춘다.",
    "팀원들은 어색하지만 각자의 방식으로 사건 해결에 기여하며 팀워크의 시작을 보여준다."
]

# Notion 업로드
notion_url = "https://api.notion.com/v1/pages"
notion_headers = {
    "Authorization": f"Bearer {NOTION_API_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

data = {
    "parent": { "database_id": DATABASE_ID },
    "properties": {
        "Date": {
            "title": [{"text": {"content": datetime.now().strftime("%Y-%m-%d")}}]
        },
        "Viewership Rating": {
            "rich_text": [{"text": {"content": "N/A"}}]
        },
        "Article Summary": {
            "rich_text": [{"text": {"content": "\n".join(summaries)}}]
        },
        "Viewer Sentiment": {
            "rich_text": [{"text": {"content": f"Positive: {viewer_sentiment['positive']}, Negative: {viewer_sentiment['negative']}, Neutral: {viewer_sentiment['neutral']}, Keywords: {', '.join(viewer_sentiment['keywords'])}"}}]
        },
        "Episode Summary": {
            "rich_text": [{"text": {"content": "\n".join(episode_summary)}}]
        }
    }
}

logger.debug(f"NOTION_API_TOKEN: {NOTION_API_TOKEN}")
logger.debug(f"DATABASE_ID: {DATABASE_ID}")

notion_response = requests.post(notion_url, headers=notion_headers, data=json.dumps(data))
print(notion_response.status_code)
print(notion_response.json())
