# trend_analyzer.py
# =====================================
# トレンド分析モジュール
# ジャンル・カテゴリ×キーワードの
# 購買意欲スコアを時系列で蓄積・分析する
# =====================================

import json
from openai import OpenAI


def analyze_trend_keywords(
    client: OpenAI,
    genre: str,
    keywords: list,
) -> dict:
    """
    ジャンルとキーワードリストを受け取り、
    各キーワードの購買意欲スコア・検索意図・トレンド傾向を返す。
    """
    kw_list_str = "\n".join([f"- {kw}" for kw in keywords])

    prompt = f"""
あなたはデジタルマーケティングの専門家です。
以下のジャンルとキーワード群を分析し、JSONのみで回答してください。
前置き・説明・```は不要です。

ジャンル: {genre}
キーワード一覧:
{kw_list_str}

以下のJSON形式で出力してください。

{{
  "genre": "{genre}",
  "genre_summary": "このジャンル全体のトレンドを2文で説明",
  "genre_trend": "上昇 / 横ばい / 下降 のどれか1つ",
  "genre_avg_score": ジャンル全体の平均購買意欲スコア（1〜10の整数）,
  "keywords": [
    {{
      "keyword": "キーワード名",
      "purchase_score": 購買意欲スコア（1〜10の整数）,
      "search_intent": "比較検討段階 / 購買直前 / 情報収集 / 価格調査 のどれか1つ",
      "price_segment": "Budget / Standard / Premium / Luxury のどれか1つ",
      "trend": "上昇 / 横ばい / 下降 のどれか1つ",
      "trend_reason": "トレンドの理由を20文字以内で"
    }}
  ],
  "top_keyword": "最も購買意欲が高いキーワード名",
  "rising_keyword": "最も上昇トレンドにあるキーワード名",
  "ai_insight": "このジャンルで今すぐ取るべきマーケティングアクションを50文字以内で"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "あなたはデジタルマーケティングの専門家です。"
                    "市場トレンドの分析と購買意欲スコアリングが専門です。"
                    "出力はJSONのみ。前置きや説明は一切不要です。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=1500,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
