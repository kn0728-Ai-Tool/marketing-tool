"""
trend_analyzer.py - 拡張版
追加機能:
  - predict_trend()        : 線形回帰によるトレンド予測
  - generate_heatmap_data(): 曜日×時間帯ヒートマップ用データ生成
  - analyze_by_age_group() : OpenAI API による年代別傾向分析
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from openai import OpenAI
import json
import re


# ──────────────────────────────────────────────
# 1. トレンド予測（線形回帰 + 信頼区間）
# ──────────────────────────────────────────────

def predict_trend(
    dates: list[str],
    values: list[float],
    forecast_weeks: int = 12,
) -> dict:
    """
    過去の Google Trends データから線形回帰で将来を予測する。

    Parameters
    ----------
    dates         : ISO 形式の日付文字列リスト（例: ["2024-01-01", ...]）
    values        : 対応する検索インデックス値リスト（0-100）
    forecast_weeks: 予測する週数（デフォルト 12 週）

    Returns
    -------
    {
      "historical": {"dates": [...], "values": [...]},
      "forecast":   {"dates": [...], "values": [...],
                     "upper": [...], "lower": [...]},
      "trend":      "increasing" | "decreasing" | "stable",
      "slope":      float,       # 週あたりの変化量
      "r_squared":  float,
    }
    """
    if len(dates) < 4:
        return {"error": "予測には最低4週分のデータが必要です"}

    # 数値インデックスに変換
    x = np.arange(len(values), dtype=float)
    y = np.array(values, dtype=float)

    # 線形回帰
    coeffs = np.polyfit(x, y, 1)
    slope, intercept = coeffs
    y_pred = np.polyval(coeffs, x)

    # R²
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0.0

    # 残差標準偏差（信頼区間用）
    residual_std = np.std(y - y_pred)

    # 将来日付の生成
    last_date = datetime.strptime(dates[-1], "%Y-%m-%d")
    future_dates = [
        (last_date + timedelta(weeks=i + 1)).strftime("%Y-%m-%d")
        for i in range(forecast_weeks)
    ]
    future_x = np.arange(len(x), len(x) + forecast_weeks, dtype=float)
    future_y = np.polyval(coeffs, future_x)

    # 値を 0-100 にクリップ
    future_y_clipped = np.clip(future_y, 0, 100).tolist()
    upper = np.clip(future_y + 1.96 * residual_std, 0, 100).tolist()
    lower = np.clip(future_y - 1.96 * residual_std, 0, 100).tolist()

    # トレンド判定
    if slope > 0.3:
        trend = "increasing"
    elif slope < -0.3:
        trend = "decreasing"
    else:
        trend = "stable"

    return {
        "historical": {"dates": dates, "values": values},
        "forecast": {
            "dates": future_dates,
            "values": future_y_clipped,
            "upper": upper,
            "lower": lower,
        },
        "trend": trend,
        "slope": round(float(slope), 4),
        "r_squared": round(float(r2), 4),
    }


# ──────────────────────────────────────────────
# 2. ヒートマップ用データ生成
# ──────────────────────────────────────────────

def generate_heatmap_data(
    keyword: str,
    trends_weekly: list[float] | None = None,
) -> dict:
    """
    曜日 × 時間帯のヒートマップ用データを生成する。
    Google Trends は時間帯別データを直接提供しないため、
    週次データのパターンと一般的な検索行動モデルを組み合わせて推定する。

    Parameters
    ----------
    keyword       : 対象キーワード
    trends_weekly : 直近の週次トレンド値（0-100）。渡すと振れ幅の補正に使用。

    Returns
    -------
    {
      "days"  : ["月","火","水","木","金","土","日"],
      "hours" : [0, 1, ..., 23],
      "matrix": [[float, ...], ...],   # shape: (7, 24)
      "note"  : str,
    }
    """
    days = ["月", "火", "水", "木", "金", "土", "日"]
    hours = list(range(24))

    # 時間帯別ベースライン（一般的な検索行動）
    hour_base = np.array([
        5, 3, 2, 2, 3, 8, 20, 40, 60, 70, 72, 70,
        65, 68, 70, 72, 75, 78, 80, 75, 65, 50, 35, 18,
    ], dtype=float)

    # 曜日別係数（平日 vs 週末）
    day_coeff = np.array([1.0, 1.0, 1.0, 1.0, 1.1, 1.2, 1.1])

    # 週次データがある場合はスケール補正
    if trends_weekly and len(trends_weekly) >= 4:
        recent_avg = np.mean(trends_weekly[-4:])
        scale = recent_avg / 70.0  # 基準値 70 に対する比率
    else:
        scale = 1.0

    # マトリクス生成（day × hour）
    matrix = []
    rng = np.random.default_rng(abs(hash(keyword)) % (2**32))
    for d_idx in range(7):
        row = []
        for h_idx in range(24):
            val = hour_base[h_idx] * day_coeff[d_idx] * scale
            # ±10% のランダムノイズ
            noise = rng.uniform(0.9, 1.1)
            val = float(np.clip(val * noise, 0, 100))
            row.append(round(val, 1))
        matrix.append(row)

    return {
        "days": days,
        "hours": hours,
        "matrix": matrix,
        "note": "※ 時間帯データは週次トレンドと一般的な検索行動モデルから推定した値です。",
    }


# ──────────────────────────────────────────────
# 3. 年代別 AI 分析
# ──────────────────────────────────────────────

def analyze_by_age_group(
    keyword: str,
    age_groups: list[dict],
    api_key: str,
    trend_context: str = "",
) -> dict:
    """
    OpenAI API を使い、指定した年代グループごとに
    キーワードへの関心度・購買行動・効果的な訴求ポイントを分析する。

    Parameters
    ----------
    keyword    : 分析対象キーワード
    age_groups : [{"label": "10代", "min": 10, "max": 19}, ...]
    api_key    : OpenAI API キー
    trend_context: 直近のトレンド傾向テキスト（任意）

    Returns
    -------
    {
      "keyword": str,
      "age_groups": [
        {
          "label"       : "10代",
          "interest"    : int (0-100),
          "purchase_rate": int (0-100),
          "appeal_points": [str, ...],
          "risks"       : [str, ...],
          "channels"    : [str, ...],
          "summary"     : str,
        },
        ...
      ],
      "overall_insight": str,
    }
    """
    client = OpenAI(api_key=api_key)

    age_labels = [g["label"] for g in age_groups]
    age_list_str = "・".join(age_labels)

    trend_section = f"\n現在のトレンド傾向: {trend_context}" if trend_context else ""

    prompt = f"""
あなたはマーケティングデータアナリストです。
以下のキーワードについて、指定された年代別に詳細な分析を行ってください。{trend_section}

キーワード: 「{keyword}」
分析対象の年代: {age_list_str}

各年代について、以下の情報を JSON 形式で返してください。
JSON 以外のテキストは一切出力しないでください。

{{
  "age_groups": [
    {{
      "label": "年代ラベル（例: 10代）",
      "interest": 0〜100の整数（その年代のキーワードへの関心度）,
      "purchase_rate": 0〜100の整数（購買・利用意向の高さ）,
      "appeal_points": ["効果的な訴求ポイント1", "訴求ポイント2", "訴求ポイント3"],
      "risks": ["この年代へのアプローチリスク1", "リスク2"],
      "channels": ["効果的な接触チャネル1", "チャネル2", "チャネル3"],
      "summary": "この年代の特徴を2〜3文で要約"
    }}
  ],
  "overall_insight": "全年代を横断した総合的なインサイトを3〜4文で記述"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content.strip()

    # JSON 抽出（```json ... ``` ブロックが含まれる場合に対応）
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not json_match:
        return {"error": "AIからの応答をパースできませんでした", "raw": raw}

    try:
        parsed = json.loads(json_match.group())
        parsed["keyword"] = keyword
        return parsed
    except json.JSONDecodeError as e:
        return {"error": f"JSONパースエラー: {e}", "raw": raw}


# ──────────────────────────────────────────────
# 4. ユーティリティ：年代グループのデフォルト生成
# ──────────────────────────────────────────────

def build_age_groups(
    ranges: list[tuple[int, int]],
    labels: list[str] | None = None,
) -> list[dict]:
    """
    年代グループ定義を生成するヘルパー。

    Parameters
    ----------
    ranges : [(min, max), ...]  例: [(10,19),(20,29),(30,39)]
    labels : 任意のラベルリスト。None の場合は "10代" 形式で自動生成。

    Returns
    -------
    [{"label": "10代", "min": 10, "max": 19}, ...]
    """
    groups = []
    for i, (mn, mx) in enumerate(ranges):
        if labels and i < len(labels):
            label = labels[i]
        else:
            label = f"{mn}代" if mx - mn < 20 else f"{mn}〜{mx}代"
        groups.append({"label": label, "min": mn, "max": mx})
    return groups
