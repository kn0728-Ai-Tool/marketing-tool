# analyzer.py  v2.3
# AI分析ロジック強化版
# 価格帯別プロンプト・ペルソナ・LP提案・CTA生成

import json
import time
from openai import OpenAI


# =====================================
# 価格帯別の訴求ルール定義
# AIへの指示に組み込む「戦略マニュアル」
# =====================================
SEGMENT_RULES = {
    "Budget": {
        "description": "コスパ重視・価格優先のユーザー層",
        "must_include": [
            "具体的な金額・割引率・節約額を必ず入れる",
            "「最安値」「割引」「お得」「節約」などコスパ訴求ワードを使う",
            "数字で価値を示す（例：月額980円、70%OFF）",
            "即決を促すCTAを使う（今すぐ・期間限定）",
        ],
        "must_avoid": [
            "「高級」「プレミアム」「ラグジュアリー」などの高価格帯ワード",
            "抽象的な品質訴求（こだわり・職人など）",
            "価格を曖昧にする表現",
        ],
        "persona": "20〜40代・価格を最重視・比較サイトをよく見る・節約志向",
        "cta_style": "今すぐ無料で試す / 最安値を確認する / 限定割引を受け取る",
    },
    "Standard": {
        "description": "機能・信頼性・コスパバランスを重視するユーザー層",
        "must_include": [
            "信頼性・実績・利用者数などの安心感を示す数字",
            "「人気No.1」「選ばれる理由」「満足度〇〇%」など",
            "機能・スペックの具体的なメリット",
            "バランスの良さを訴求する",
        ],
        "must_avoid": [
            "極端な低価格訴求（Budget層と混同されるため）",
            "過度な高級感（ターゲットに響かない）",
        ],
        "persona": "30〜50代・機能と価格のバランスを重視・口コミや評価を参考にする",
        "cta_style": "詳しく見る / 無料で資料請求 / 人気プランを確認する",
    },
    "Premium": {
        "description": "品質・体験・専門性を重視する高単価志向のユーザー層",
        "must_include": [
            "品質・素材・製法などの「こだわり」を具体的に示す",
            "専門家・プロの監修・受賞歴などの権威性",
            "体験・ライフスタイルの向上を訴求する",
            "顧客サポートの充実を示す",
        ],
        "must_avoid": [
            "「安い」「格安」「割引」など価格訴求ワード",
            "大衆向けの表現（誰でも・簡単すぎる）",
        ],
        "persona": "30〜50代・品質に対して適切な対価を払う・レビューより専門家の意見を重視",
        "cta_style": "今すぐ相談する / 無料カウンセリングを予約 / 限定体験を申し込む",
    },
    "Luxury": {
        "description": "ブランド・希少性・ステータスを最重視する超高単価層",
        "must_include": [
            "希少性・限定感（数量限定・会員限定・招待制）",
            "ブランドのストーリーや歴史・哲学",
            "他では得られない特別な体験・価値",
            "エクスクルーシブな表現（選ばれた・特別な）",
        ],
        "must_avoid": [
            "価格訴求・割引・コスパなどの表現",
            "大量販売を連想させる表現（誰でも・全員に）",
            "安さを示す数字",
        ],
        "persona": "40〜60代・価格より価値を重視・ブランドへの帰属意識が高い・口コミより実績を重視",
        "cta_style": "特別メンバーに申し込む / 限定コレクションを見る / プライベート相談を予約",
    },
}


def get_client(api_key: str) -> OpenAI:
    """OpenAIクライアントを返す"""
    return OpenAI(api_key=api_key)


def analyze_keyword_structured(client: OpenAI, keyword: str) -> dict:
    """
    キーワード1件をAI分析する（強化版）
    価格帯判定 → 価格帯別の専用プロンプトで広告文・ペルソナ・LP提案・CTAを生成
    """

    # ---- Step 1: まず価格帯と基本情報を判定 ----
    step1_prompt = f"""
あなたはGoogle広告のプロフェッショナルです。
以下のキーワードを分析し、必ずJSON形式のみで回答してください。

【キーワード】: {keyword}

{{
  "keyword": "{keyword}",
  "search_intent": "比較検討段階 / 購買直前 / 情報収集 / 価格調査 のどれか1つ",
  "intent_reason": "理由を25文字以内で",
  "price_segment": "Budget / Standard / Premium / Luxury のどれか1つ",
  "segment_reason": "理由を25文字以内で",
  "purchase_score": 購買意欲スコア1〜10の整数
}}
"""

    step1_res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": step1_prompt}],
        temperature=0.3,  # 判定は低温度で安定させる
    )
    step1_raw = _extract_json(step1_res.choices[0].message.content)
    base_data = json.loads(step1_raw)

    # 価格帯に対応するルールを取得
    segment = base_data.get("price_segment", "Standard")
    rules   = SEGMENT_RULES.get(segment, SEGMENT_RULES["Standard"])

    # ---- Step 2: 価格帯別の専用プロンプトで詳細生成 ----
    must_include = "\n".join([f"  - {r}" for r in rules["must_include"]])
    must_avoid   = "\n".join([f"  - {r}" for r in rules["must_avoid"]])

    step2_prompt = f"""
あなたはGoogle広告の専門コピーライターです。
以下の条件に厳密に従って広告コンテンツを生成してください。

【キーワード】: {keyword}
【ターゲット層】: {segment}（{rules['description']}）
【ターゲットペルソナ】: {rules['persona']}

【必ず含めること】:
{must_include}

【絶対に避けること】:
{must_avoid}

以下のJSON形式のみで回答してください。説明文や前置きは不要です。

{{
  "ad_copies": [
    {{
      "title": "広告タイトル（15文字以内・{segment}層向け）",
      "description": "広告説明文（45文字以内・{segment}層の訴求ルールに従う）",
      "appeal_point": "この広告文の主な訴求ポイントを10文字以内で"
    }},
    {{
      "title": "広告タイトル（15文字以内・角度を変えた別訴求）",
      "description": "広告説明文（45文字以内）",
      "appeal_point": "この広告文の主な訴求ポイントを10文字以内で"
    }},
    {{
      "title": "広告タイトル（15文字以内・感情に訴える訴求）",
      "description": "広告説明文（45文字以内）",
      "appeal_point": "この広告文の主な訴求ポイントを10文字以内で"
    }}
  ],
  "persona": {{
    "age": "想定年齢層（例：30〜40代）",
    "mindset": "購買時の心理状態を30文字以内で",
    "pain_point": "最大の悩み・課題を30文字以内で",
    "trigger": "購買の決め手になる要素を30文字以内で"
  }},
  "cta_suggestions": [
    "{rules['cta_style'].split('/')[0].strip()}",
    "{rules['cta_style'].split('/')[1].strip() if '/' in rules['cta_style'] else rules['cta_style']}",
    "キーワードに合わせたオリジナルCTAを1つ"
  ],
  "lp_suggestions": [
    "LP改善提案1: ファーストビューに入れるべき要素を具体的に30文字以内で",
    "LP改善提案2: {segment}層が離脱しないコンテンツ構成を30文字以内で",
    "LP改善提案3: CVRを上げるために最も重要な要素を30文字以内で"
  ],
  "advice": "このキーワードで最も重要な広告改善ポイントを40文字以内で",
  "competition_note": "この市場の競合状況と差別化ポイントを40文字以内で"
}}
"""

    step2_res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": step2_prompt}],
        temperature=0.7,
    )
    step2_raw    = _extract_json(step2_res.choices[0].message.content)
    detail_data  = json.loads(step2_raw)

    # Step1 と Step2 の結果をマージ
    return {**base_data, **detail_data}


def analyze_keywords_batch(client: OpenAI, keywords: list) -> list:
    """複数キーワードをまとめて分析"""
    results = []
    for kw in keywords:
        try:
            data = analyze_keyword_structured(client, kw)
            results.append(data)
        except Exception as e:
            results.append({"keyword": kw, "error": str(e)})
        time.sleep(0.8)  # 2ステップAPIコールのため少し長めに待つ
    return results


def _extract_json(raw: str) -> str:
    """
    AIの返答からJSONだけを取り出す。
```json〜``` で囲まれていても対応。
