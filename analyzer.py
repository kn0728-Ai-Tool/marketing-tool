# analyzer.py  v2.0
# =====================================
# AI分析ロジック 強化版
#
# 変更点：
# - 価格帯ごとに専用プロンプトを用意
# - 広告文に必須ルールを組み込む
# - 感情分析・競合ポジション分析を追加
# - 業種を指定して分析精度を上げる
# =====================================

import json
import time
from openai import OpenAI


# =====================================
# 価格帯ごとの広告文ルール定義
# ここを変えるだけで全体の広告文の傾向が変わる
# =====================================
SEGMENT_RULES = {
    "Budget": {
        "description": "コストパフォーマンスを最重視する価格重視層",
        "must_include": [
            "具体的な数字（価格・割引率・○○%OFF など）を必ず入れる",
            "「最安」「格安」「節約」「お得」「割引」などのコスト訴求ワードを使う",
            "今すぐ行動させる緊急性（「今だけ」「期間限定」など）を入れる",
        ],
        "must_avoid": [
            "高級感・ブランド感を出す表現は避ける",
            "抽象的な品質訴求（「高品質」「上質な」など）は避ける",
        ],
        "tone": "シンプル・直接的・数字重視",
        "example_titles": ["最安値で手に入れる", "今だけ50%OFF", "節約するならここ"],
    },
    "Standard": {
        "description": "コストと品質のバランスを重視する標準層",
        "must_include": [
            "信頼性・実績を示す数字（「利用者数○万人」「満足度○%」など）を入れる",
            "機能・使いやすさ・安心感を訴求する",
            "「選ばれる理由」「多くの方に支持」などの共感訴求を使う",
        ],
        "must_avoid": [
            "極端な最安値訴求は避ける（安っぽく見える）",
            "高すぎるブランド訴求は避ける（届かない印象になる）",
        ],
        "tone": "親しみやすい・安心感・実績重視",
        "example_titles": ["選ばれ続ける理由がある", "安心と品質を両立", "満足度98%の実績"],
    },
    "Premium": {
        "description": "品質・体験・専門性を重視する高品質志向層",
        "must_include": [
            "品質・素材・技術の優位性を具体的に表現する",
            "「プロ」「専門」「こだわり」「本格」などの専門性ワードを使う",
            "購入後の体験・ライフスタイルの変化を想起させる表現を使う",
        ],
        "must_avoid": [
            "価格の安さ・割引訴求は一切避ける",
            "大衆的・汎用的な表現は避ける（特別感が薄れる）",
        ],
        "tone": "洗練・専門的・体験訴求",
        "example_titles": ["本物を知る人が選ぶ", "プロも認める品質", "上質な体験を毎日に"],
    },
    "Luxury": {
        "description": "ブランド・希少性・ステータスを重視する高級志向層",
        "must_include": [
            "希少性・限定性を強調する（「限定」「選ばれた」「唯一」など）",
            "ブランドストーリー・歴史・職人技など感情に訴える表現を使う",
            "ステータス・自己表現・特別な体験を想起させる言葉を使う",
        ],
        "must_avoid": [
            "価格・割引に関する表現は絶対に避ける",
            "大量生産・汎用品を想起させる表現は避ける",
            "数字による訴求（利用者数など）は避ける（希少感が薄れる）",
        ],
        "tone": "格調・物語性・感情訴求・詩的な表現",
        "example_titles": ["選ばれた人だけの体験", "時を超えた本物の価値", "あなただけの物語"],
    },
}


# =====================================
# 検索意図ごとの分析ヒント
# =====================================
INTENT_HINTS = {
    "購買直前":     "ユーザーは今すぐ購入したい状態。CTAを強く・障壁を取り除く訴求が有効。",
    "比較検討段階": "ユーザーは複数の選択肢を比較中。他社との差別化・選ぶ理由を明示するのが有効。",
    "情報収集":     "ユーザーはまだ初期段階。まず興味を持たせ、次のステップへ誘導する訴求が有効。",
    "価格調査":     "ユーザーは価格を比べている。価格の透明性・コスパの明示・特典訴求が有効。",
}


def get_client(api_key: str) -> OpenAI:
    """OpenAIクライアントを返す"""
    return OpenAI(api_key=api_key)


def build_analysis_prompt(keyword: str, industry: str = "") -> str:
    """
    キーワードと業種から分析プロンプトを生成する。
    まず検索意図と価格帯を推定し、その結果に合わせた
    専用ルールで広告文を生成する2段階構造。
    """

    # 業種の補足情報
    industry_context = f"業種・ジャンル: {industry}\n" if industry else ""

    # 各価格帯のルールをプロンプトに組み込む
    segment_rules_text = ""
    for seg, rules in SEGMENT_RULES.items():
        must_include = "\n".join([f"    - {r}" for r in rules["must_include"]])
        must_avoid   = "\n".join([f"    - {r}" for r in rules["must_avoid"]])
        examples     = "・".join(rules["example_titles"])
        segment_rules_text += f"""
  【{seg}層 ({rules['description']})】
    トーン: {rules['tone']}
    必須要素:
{must_include}
    避けること:
{must_avoid}
    タイトル例: {examples}
"""

    prompt = f"""
あなたはGoogle広告のエキスパートです。
以下のキーワードを深く分析し、価格帯層に最適化された広告文を生成してください。

{industry_context}【分析キーワード】: {keyword}

## 価格帯別 広告文ルール
{segment_rules_text}

## 検索意図ごとの訴求ヒント
- 購買直前    : {INTENT_HINTS['購買直前']}
- 比較検討段階: {INTENT_HINTS['比較検討段階']}
- 情報収集    : {INTENT_HINTS['情報収集']}
- 価格調査    : {INTENT_HINTS['価格調査']}

## 出力形式
必ずJSON形式のみで回答してください。説明文・前置き・```は不要です。

{{
  "keyword": "{keyword}",
  "search_intent": "比較検討段階 / 購買直前 / 情報収集 / 価格調査 のどれか1つ",
  "intent_reason": "理由を30文字以内で",
  "price_segment": "Budget / Standard / Premium / Luxury のどれか1つ",
  "segment_reason": "理由を30文字以内で",
  "purchase_score": 購買意欲スコア1〜10の整数,
  "emotion": "このキーワードで検索するユーザーの感情を20文字以内で（例: 節約したい・焦り・憧れ）",
  "competitor_position": "競合との差別化ポイントを30文字以内で",
  "ad_copies": [
    {{
      "title": "このキーワードの価格帯層ルールに従ったタイトル（15文字以内）",
      "description": "このキーワードの価格帯層ルールに従った説明文（45文字以内）",
      "appeal_point": "この広告文の最大の訴求ポイントを15文字以内で"
    }},
    {{
      "title": "別アプローチのタイトル（15文字以内）",
      "description": "別アプローチの説明文（45文字以内）",
      "appeal_point": "この広告文の最大の訴求ポイントを15文字以内で"
    }},
    {{
      "title": "3つ目のアプローチのタイトル（15文字以内）",
      "description": "3つ目のアプローチの説明文（45文字以内）",
      "appeal_point": "この広告文の最大の訴求ポイントを15文字以内で"
    }}
  ],
  "advice": "このキーワードで最も重要な広告改善ポイントを40文字以内で",
  "lp_advice": "ランディングページで特に重視すべき点を40文字以内で",
  "cta_suggestion": "最適なCTAボタンのテキストを10文字以内で（例: 今すぐ無料で試す）"
}}
"""
    return prompt


def analyze_keyword_structured(
    client: OpenAI,
    keyword: str,
    industry: str = "",
) -> dict:
    """
    キーワード1件をAI分析してdictで返す。
    industryを指定すると業種に合わせた分析になる。
    """
    prompt = build_analysis_prompt(keyword, industry)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "あなたはGoogle広告の第一人者です。"
                    "価格帯別マーケティング戦略と検索意図分析の専門家として、"
                    "実務で即使える広告文を生成してください。"
                    "出力は必ずJSONのみ。前置きや説明は一切不要です。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.75,   # 創造性を少し上げる
        max_tokens=1200,    # 出力項目が増えたので余裕を持たせる
    )

    raw = response.choices[0].message.content.strip()

    # ```json〜``` で囲まれていても対応
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


def analyze_keywords_batch(
    client: OpenAI,
    keywords: list,
    industry: str = "",
) -> list:
    """
    キーワードリストをまとめて分析してリストで返す。
    """
    results = []
    for kw in keywords:
        try:
            data = analyze_keyword_structured(client, kw, industry)
            results.append(data)
        except Exception as e:
            results.append({"keyword": kw, "error": str(e)})
        time.sleep(0.5)
    return results
