# market_trend.py
# =====================================
# 日本市場のトレンドデータ取得モジュール
# Google Trends（pytrends）＋ Google News RSS を使用
# 完全無料・APIキー不要
# =====================================

import time
import datetime
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET
from urllib.request import urlopen
from urllib.parse import quote
import pandas as pd
from pytrends.request import TrendReq

# 日本時間（JST）
JST = ZoneInfo("Asia/Tokyo")


# =====================================
# Google Trends データ取得
# =====================================
def get_google_trends(
    keywords: list,
    timeframe: str = "today 3-m",   # 直近3ヶ月
    geo: str = "JP",                 # 日本
) -> dict:
    """
    Google Trendsから検索ボリューム推移を取得する。

    timeframe の例:
      "today 1-m"  : 直近1ヶ月
      "today 3-m"  : 直近3ヶ月（デフォルト）
      "today 12-m" : 直近12ヶ月
      "today 5-y"  : 直近5年

    戻り値:
      {
        "trend_df":        pd.DataFrame（日付×キーワードの検索ボリューム）,
        "related_queries": dict（キーワードごとの関連クエリ）,
        "interest_by_region": pd.DataFrame（都道府県別の人気度）,
      }
    """
    # 最大5キーワードまで（Google Trendsの制限）
    keywords = keywords[:5]

    pytrends = TrendReq(hl="ja-JP", tz=540)   # tz=540 は日本時間（JST）

    # リクエスト（レート制限対策で少し待つ）
    time.sleep(1)
    pytrends.build_payload(
        keywords,
        cat=0,
        timeframe=timeframe,
        geo=geo,
        gprop="",
    )

    # 時系列データ取得
    trend_df = pytrends.interest_over_time()
    if not trend_df.empty and "isPartial" in trend_df.columns:
        trend_df = trend_df.drop(columns=["isPartial"])

    # 関連クエリ取得
    time.sleep(1)
    try:
        related = pytrends.related_queries()
        related_queries = {}
        for kw in keywords:
            if kw in related and related[kw]["top"] is not None:
                related_queries[kw] = related[kw]["top"].head(5).to_dict("records")
            else:
                related_queries[kw] = []
    except Exception:
        related_queries = {kw: [] for kw in keywords}

    # 地域別データ取得（都道府県別）
    time.sleep(1)
    try:
        region_df = pytrends.interest_by_region(resolution="REGION", inc_low_vol=True, inc_geo_code=False)
        region_df = region_df[region_df.sum(axis=1) > 0]
    except Exception:
        region_df = pd.DataFrame()

    return {
        "trend_df":           trend_df,
        "related_queries":    related_queries,
        "interest_by_region": region_df,
    }


def get_trend_summary(trend_df: pd.DataFrame, keyword: str) -> dict:
    """
    1つのキーワードのトレンドデータから
    最新値・最大値・最小値・変化率・トレンド方向を計算して返す。
    """
    if trend_df.empty or keyword not in trend_df.columns:
        return {}

    series = trend_df[keyword].dropna()
    if len(series) < 2:
        return {}

    # 直近半分と前半分の平均を比較してトレンド判定
    mid    = len(series) // 2
    recent = series.iloc[mid:].mean()
    older  = series.iloc[:mid].mean()

    # older が 0 または極めて小さい場合は recent の変化量で判定
    if older > 0:
        change = (recent - older) / older * 100
    elif recent > 0:
        change = 100.0  # 0 → 正の値 なら上昇扱い
    else:
        change = 0.0

    if change >= 10:
        trend = "上昇"
    elif change <= -10:
        trend = "下降"
    else:
        trend = "横ばい"

    # peak_date: 全値が同じ場合は最後の日付を使う
    try:
        peak_date = str(series.idxmax().date())
    except Exception:
        peak_date = str(series.index[-1].date())

    return {
        "keyword":    keyword,
        "latest":     int(series.iloc[-1]),
        "max":        int(series.max()),
        "min":        int(series.min()),
        "avg":        round(float(series.mean()), 1),
        "change_pct": round(float(change), 1),
        "trend":      trend,
        "peak_date":  peak_date,
    }


# =====================================
# Google News RSS でニュース取得
# =====================================
def get_google_news(keyword: str, max_items: int = 5) -> list:
    """
    Google News RSS からキーワード関連の最新ニュースを取得する。
    戻り値: [{"title": ..., "link": ..., "pubDate": ...}, ...]
    """
    encoded = quote(keyword)
    url     = (
        f"https://news.google.com/rss/search"
        f"?q={encoded}&hl=ja&gl=JP&ceid=JP:ja"
    )

    try:
        with urlopen(url, timeout=10) as response:
            xml_data = response.read()

        root  = ET.fromstring(xml_data)
        items = root.findall(".//item")

        news_list = []
        for item in items[:max_items]:
            title   = item.findtext("title", "")
            link    = item.findtext("link", "")
            pubdate = item.findtext("pubDate", "")

            # タイトルから不要な「- メディア名」を除去
            if " - " in title:
                title = title.rsplit(" - ", 1)[0].strip()

            news_list.append({
                "title":   title,
                "link":    link,
                "pubDate": pubdate,
            })

        return news_list

    except Exception:
        return []


# =====================================
# まとめて取得するメイン関数
# =====================================
def fetch_market_trends(
    keywords: list,
    timeframe: str = "today 3-m",
) -> dict:
    """
    Google Trends + Google News を一括取得して返す。

    戻り値:
    {
        "trend_df":        pd.DataFrame,
        "summaries":       list[dict],      # キーワードごとのサマリー
        "related_queries": dict,
        "region_df":       pd.DataFrame,
        "news":            dict,            # キーワード→ニュースリスト
        "fetched_at":      str,             # 取得日時（日本時間）
    }
    """
    result = {
        "trend_df":        pd.DataFrame(),
        "summaries":       [],
        "related_queries": {},
        "region_df":       pd.DataFrame(),
        "news":            {},
        "fetched_at":      datetime.datetime.now(JST).strftime("%Y-%m-%d %H:%M (JST)"),
    }

    # Google Trends 取得
    try:
        trends = get_google_trends(keywords, timeframe=timeframe)
        trend_df_got = trends["trend_df"]

        result["trend_df"]        = trend_df_got
        result["related_queries"] = trends["related_queries"]
        result["region_df"]       = trends["interest_by_region"]

        # キーワードごとのサマリーを計算
        # trend_df が空でないことを確認してからサマリー生成
        if not trend_df_got.empty:
            for kw in keywords:
                # カラム名の前後空白の違いに対応
                matched_col = None
                for col in trend_df_got.columns:
                    if col.strip() == kw.strip():
                        matched_col = col
                        break
                if matched_col:
                    summary = get_trend_summary(trend_df_got, matched_col)
                    if summary:
                        summary["keyword"] = kw  # 元のキーワード名で上書き
                        result["summaries"].append(summary)
        else:
            result["error_trends"] = "Google Trends からデータを取得できませんでした（空のデータフレーム）"

    except Exception as e:
        result["error_trends"] = str(e)

    # Google News 取得（キーワードごと）
    for kw in keywords[:3]:    # 最大3キーワードのニュースを取得
        time.sleep(0.5)
        result["news"][kw] = get_google_news(kw, max_items=4)

    return result
