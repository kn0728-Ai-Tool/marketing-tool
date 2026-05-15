# csv_analyzer.py
# =====================================
# CSV分析モジュール
# どんな列構成のCSVでも自動判定し
# AIがトレンド・改善点を抽出する
# =====================================

import json
import pandas as pd
from openai import OpenAI


# =====================================
# マーケティング指標の列名候補
# 日本語・英語どちらでも対応する
# =====================================
COLUMN_PATTERNS = {
    "keyword": [
        "キーワード", "keyword", "検索語句", "search term",
        "search query", "クエリ", "query",
    ],
    "clicks": [
        "クリック数", "clicks", "クリック", "click",
    ],
    "impressions": [
        "インプレッション", "impressions", "表示回数", "impr",
    ],
    "ctr": [
        "ctr", "クリック率", "click through rate",
    ],
    "cpc": [
        "平均cpc", "cpc", "avg cpc", "平均クリック単価", "クリック単価",
    ],
    "cost": [
        "費用", "cost", "コスト", "spend", "消化金額",
    ],
    "conversions": [
        "コンバージョン", "conversions", "cv", "成約数", "購入数",
    ],
    "cvr": [
        "cvr", "コンバージョン率", "conversion rate", "転換率",
    ],
    "cpa": [
        "cpa", "コンバージョン単価", "cost per conversion",
    ],
    "roas": [
        "roas", "広告費用対効果",
    ],
    "revenue": [
        "収益", "revenue", "売上", "売上高",
    ],
    "quality_score": [
        "品質スコア", "quality score", "qs",
    ],
    "position": [
        "掲載順位", "position", "avg position", "平均掲載順位",
    ],
}


def detect_columns(df: pd.DataFrame) -> dict:
    """
    DataFrameの列名を走査し、
    マーケティング指標に対応する列名を自動検出して辞書で返す。
    例: {"keyword": "キーワード", "clicks": "クリック数", ...}
    """
    detected = {}
    cols_lower = {c: c.lower().strip() for c in df.columns}

    for metric, candidates in COLUMN_PATTERNS.items():
        for col, col_lower in cols_lower.items():
            if any(c.lower() in col_lower or col_lower in c.lower() for c in candidates):
                detected[metric] = col
                break

    return detected


def clean_numeric(series: pd.Series) -> pd.Series:
    """
    数値列の前処理。
    「%」「¥」「,」などを除去して float に変換する。
    """
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("¥", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace(" ", "", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )


def prepare_dataframe(df: pd.DataFrame, col_map: dict) -> pd.DataFrame:
    """
    検出した列だけを抽出し、数値列をクリーニングして返す。
    """
    numeric_metrics = [
        "clicks", "impressions", "ctr", "cpc", "cost",
        "conversions", "cvr", "cpa", "roas", "revenue",
        "quality_score", "position",
    ]

    result = pd.DataFrame()

    # キーワード列
    if "keyword" in col_map:
        result["キーワード"] = df[col_map["keyword"]].astype(str).str.strip()

    # 数値列
    for metric in numeric_metrics:
        if metric in col_map:
            label = col_map[metric]
            result[label] = clean_numeric(df[col_map[metric]])

    return result


def build_summary_for_ai(df: pd.DataFrame, col_map: dict, max_rows: int = 30) -> str:
    """
    AIに渡すためのCSVサマリーテキストを生成する。
    行数が多い場合は上位・下位各15件に絞る。
    """
    lines = []

    # 全体統計
    lines.append("## CSVデータの概要")
    lines.append(f"- 総行数: {len(df)}行")
    lines.append(f"- 列構成: {', '.join(df.columns.tolist())}")
    lines.append("")

    # 数値列の基本統計
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        lines.append("## 数値列の基本統計")
        for col in numeric_cols:
            s = df[col].dropna()
            if len(s) > 0:
                lines.append(
                    f"- {col}: 平均={s.mean():.2f}, 最大={s.max():.2f}, "
                    f"最小={s.min():.2f}, 合計={s.sum():.2f}"
                )
        lines.append("")

    # データサンプル（上位・下位）
    lines.append("## データサンプル")
    if len(df) > max_rows:
        sample = pd.concat([df.head(max_rows // 2), df.tail(max_rows // 2)])
        lines.append(f"（全{len(df)}行から上位・下位各{max_rows // 2}行を抜粋）")
    else:
        sample = df

    lines.append(sample.to_string(index=False, max_cols=10))

    return "\n".join(lines)


def analyze_csv_with_ai(
    client: OpenAI,
    df: pd.DataFrame,
    col_map: dict,
    industry: str = "",
    custom_question: str = "",
) -> dict:
    """
    CSVデータをAIに渡してトレンド・改善点を分析させる。
    戻り値: {
        "summary":       全体サマリー（文章）,
        "trends":        トレンド分析（リスト）,
        "issues":        課題・問題点（リスト）,
        "improvements":  改善提案（リスト）,
        "top_keywords":  注目キーワード（リスト）,
        "targeting":     ターゲティング提案（リスト）,
        "next_actions":  次のアクション（リスト）,
    }
    """
    data_summary = build_summary_for_ai(df, col_map)
    industry_ctx = f"業種・ジャンル: {industry}\n" if industry else ""
    custom_ctx   = f"特に知りたいこと: {custom_question}\n" if custom_question else ""

    prompt = f"""
あなたはGoogle広告・デジタルマーケティングの第一人者です。
以下のCSVデータを分析し、マーケティング改善に役立つ洞察を提供してください。

{industry_ctx}{custom_ctx}
{data_summary}

以下の形式でJSONのみ出力してください。前置き・説明・```は不要です。

{{
  "summary": "このデータ全体の状況を3〜4文で簡潔にまとめた総評",

  "trends": [
    "トレンド・傾向を具体的な数値を交えて記述（例: CTRが高いキーワード群はXXXの傾向がある）",
    "トレンド2",
    "トレンド3"
  ],

  "issues": [
    "課題・問題点を具体的に記述（例: CPAがXX円を超えているキーワードが○件ある）",
    "課題2",
    "課題3"
  ],

  "improvements": [
    "改善提案を具体的なアクションとして記述（例: CTRが低いXXXキーワードは広告文を○○に変更すべき）",
    "改善提案2",
    "改善提案3",
    "改善提案4",
    "改善提案5"
  ],

  "top_keywords": [
    {{
      "keyword": "注目すべきキーワード名",
      "reason":  "注目する理由（数値根拠を含む）",
      "action":  "このキーワードに対する推奨アクション"
    }}
  ],

  "targeting": [
    "ターゲティング最適化の提案（例: 夜間帯の入札を強化すべき層はXXX）",
    "ターゲティング提案2",
    "ターゲティング提案3"
  ],

  "next_actions": [
    "今すぐやるべきアクション（優先度順）",
    "次のアクション2",
    "次のアクション3",
    "次のアクション4"
  ]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "あなたはGoogle広告・デジタルマーケティングの専門家です。"
                    "データに基づいた具体的で実践的な分析・改善提案を行ってください。"
                    "出力はJSONのみ。前置きや説明は一切不要です。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def get_top_bottom_keywords(
    df: pd.DataFrame,
    col_map: dict,
    metric: str = "ctr",
    top_n: int = 5,
) -> tuple:
    """
    指定した指標でキーワードを上位・下位に分けて返す。
    戻り値: (top_df, bottom_df)
    """
    if metric not in col_map or "keyword" not in col_map:
        return pd.DataFrame(), pd.DataFrame()

    col   = col_map[metric]
    kw    = col_map["keyword"]
    valid = df[[kw, col]].dropna().copy()
    valid[col] = clean_numeric(valid[col])
    valid = valid.sort_values(col, ascending=False)

    return valid.head(top_n), valid.tail(top_n)
