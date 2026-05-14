# analyzer.py
# AI分析ロジック

import json
import time
from openai import OpenAI


def get_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def analyze_keyword_structured(client: OpenAI, keyword: str) -> dict:
    prompt = f"""
あなたはGoogle広告のプロフェッショナルです。
以下のキーワードを分析し、必ずJSON形式のみで回答してください。
説明文や前置きは不要です。JSONだけ出力してください。

【キーワード】: {keyword}

{{
  "keyword": "{keyword}",
  "search_intent": "比較検討段階 / 購買直前 / 情報収集 / 価格調査 のどれか1つ",
  "intent_reason": "理由を25文字以内で",
  "price_segment": "Budget / Standard / Premium / Luxury のどれか1つ",
  "segment_reason": "理由を25文字以内で",
  "purchase_score": 購買意欲スコア1〜10の整数,
  "ad_copies": [
    {{
      "title": "広告タイトル（15文字以内）",
      "description": "広告説明文（45文字以内）"
    }},
    {{
      "title": "広告タイトル（15文字以内）",
      "description": "広告説明文（45文字以内）"
    }},
    {{
      "title": "広告タイトル（15文字以内）",
      "description": "広告説明文（45文字以内）"
    }}
  ],
  "advice": "最重要アドバイスを40文字以内で1つ"
}}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def analyze_keywords_batch(client: OpenAI, keywords: list) -> list:
    results = []
    for kw in keywords:
        try:
            data = analyze_keyword_structured(client, kw)
            results.append(data)
        except Exception as e:
            results.append({"keyword": kw, "error": str(e)})
        time.sleep(0.5)
    return results