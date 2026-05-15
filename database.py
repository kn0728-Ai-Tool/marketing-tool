# database.py
# =====================================
# SQLite データベース操作モジュール
# 分析結果の保存・取得・削除を担当
# =====================================

import sqlite3
import json
import datetime
from pathlib import Path

# DBファイルの保存場所
# Streamlit Cloud では /tmp に書き込む（再起動でリセットされる点に注意）
DB_PATH = Path("/tmp/keyword_analysis.db")


def get_connection() -> sqlite3.Connection:
    """
    DBへの接続を返す。
    row_factory を設定することで、結果を辞書形式で取得できる。
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # カラム名でアクセス可能にする
    return conn


def init_db() -> None:
    """
    DBとテーブルを初期化する。
    アプリ起動時に毎回呼ぶ。テーブルがなければ作成する。
    """
    conn = get_connection()
    cur  = conn.cursor()

    # 分析セッションテーブル
    # 1回の「分析開始」ボタン押下を1セッションとして記録する
    cur.execute("""
        CREATE TABLE IF NOT EXISTS analysis_sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at  TEXT    NOT NULL,
            kw_count    INTEGER NOT NULL,
            memo        TEXT    DEFAULT ''
        )
    """)

    # キーワード分析結果テーブル
    # セッションに紐づく個々のキーワード結果を保存する
    cur.execute("""
        CREATE TABLE IF NOT EXISTS keyword_results (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      INTEGER NOT NULL,
            created_at      TEXT    NOT NULL,
            keyword         TEXT    NOT NULL,
            search_intent   TEXT,
            intent_reason   TEXT,
            price_segment   TEXT,
            segment_reason  TEXT,
            purchase_score  INTEGER,
            advice          TEXT,
            ad_copies_json  TEXT,
            FOREIGN KEY (session_id) REFERENCES analysis_sessions(id)
        )
    """)

    conn.commit()
    conn.close()


def save_session(results: list, memo: str = "") -> int:
    """
    1回の分析セッションをDBに保存する。
    戻り値: 保存したセッションID
    """
    now  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cur  = conn.cursor()

    # セッションを保存
    cur.execute("""
        INSERT INTO analysis_sessions (created_at, kw_count, memo)
        VALUES (?, ?, ?)
    """, (now, len(results), memo))

    session_id = cur.lastrowid  # 保存したセッションのIDを取得

    # 各キーワードの結果を保存
    for r in results:
        if "error" in r:
            continue  # エラーのキーワードはスキップ

        cur.execute("""
            INSERT INTO keyword_results (
                session_id, created_at, keyword,
                search_intent, intent_reason,
                price_segment, segment_reason,
                purchase_score, advice, ad_copies_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            now,
            r.get("keyword", ""),
            r.get("search_intent", ""),
            r.get("intent_reason", ""),
            r.get("price_segment", ""),
            r.get("segment_reason", ""),
            r.get("purchase_score", 0),
            r.get("advice", ""),
            json.dumps(r.get("ad_copies", []), ensure_ascii=False),
        ))

    conn.commit()
    conn.close()
    return session_id


def get_all_sessions() -> list:
    """
    全セッションを新しい順で返す。
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT * FROM analysis_sessions
        ORDER BY id DESC
    """)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def get_session_results(session_id: int) -> list:
    """
    指定セッションのキーワード結果を返す。
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT * FROM keyword_results
        WHERE session_id = ?
        ORDER BY id ASC
    """, (session_id,))
    rows = cur.fetchall()
    conn.close()

    # ad_copies_json を元のリストに戻す
    results = []
    for row in rows:
        r = dict(row)
        try:
            r["ad_copies"] = json.loads(r.get("ad_copies_json", "[]"))
        except Exception:
            r["ad_copies"] = []
        results.append(r)

    return results


def get_keyword_history(keyword: str) -> list:
    """
    特定のキーワードの分析履歴を時系列で返す。
    推移の確認に使う。
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT
            kr.*,
            s.created_at AS session_date
        FROM keyword_results kr
        JOIN analysis_sessions s ON kr.session_id = s.id
        WHERE kr.keyword LIKE ?
        ORDER BY kr.id ASC
    """, (f"%{keyword}%",))
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def get_all_keywords() -> list:
    """
    保存済みの全キーワード一覧（重複なし）を返す。
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT DISTINCT keyword FROM keyword_results
        ORDER BY keyword ASC
    """)
    rows = [row["keyword"] for row in cur.fetchall()]
    conn.close()
    return rows


def delete_session(session_id: int) -> None:
    """
    指定セッションとその結果を削除する。
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("DELETE FROM keyword_results    WHERE session_id = ?", (session_id,))
    cur.execute("DELETE FROM analysis_sessions WHERE id = ?",         (session_id,))
    conn.commit()
    conn.close()


def get_segment_stats() -> dict:
    """
    全履歴での価格帯別の平均購買意欲スコアを返す。
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT
            price_segment,
            COUNT(*)        AS count,
            AVG(purchase_score) AS avg_score
        FROM keyword_results
        GROUP BY price_segment
    """)
    rows = {row["price_segment"]: dict(row) for row in cur.fetchall()}
    conn.close()
    return rows
    
# =====================================
# トレンド分析用テーブルの追加
# =====================================

def init_trend_db() -> None:
    """
    トレンド分析用のテーブルを初期化する。
    アプリ起動時に init_db() と一緒に呼ぶ。
    """
    conn = get_connection()
    cur  = conn.cursor()

    # ジャンルごとのトレンドセッションテーブル
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trend_sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at  TEXT    NOT NULL,
            genre       TEXT    NOT NULL,
            kw_count    INTEGER NOT NULL,
            avg_score   REAL,
            genre_trend TEXT,
            ai_insight  TEXT
        )
    """)

    # キーワードごとのトレンド結果テーブル
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trend_keywords (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      INTEGER NOT NULL,
            created_at      TEXT    NOT NULL,
            genre           TEXT    NOT NULL,
            keyword         TEXT    NOT NULL,
            purchase_score  INTEGER,
            search_intent   TEXT,
            price_segment   TEXT,
            trend           TEXT,
            trend_reason    TEXT,
            FOREIGN KEY (session_id) REFERENCES trend_sessions(id)
        )
    """)

    conn.commit()
    conn.close()


def save_trend_session(genre: str, result: dict) -> int:
    """
    トレンド分析結果をDBに保存する。
    戻り値: 保存したセッションID
    """
    now  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        INSERT INTO trend_sessions
            (created_at, genre, kw_count, avg_score, genre_trend, ai_insight)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        now,
        genre,
        len(result.get("keywords", [])),
        result.get("genre_avg_score", 0),
        result.get("genre_trend", ""),
        result.get("ai_insight", ""),
    ))
    session_id = cur.lastrowid

    for kw in result.get("keywords", []):
        cur.execute("""
            INSERT INTO trend_keywords
                (session_id, created_at, genre, keyword,
                 purchase_score, search_intent, price_segment,
                 trend, trend_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, now, genre,
            kw.get("keyword", ""),
            kw.get("purchase_score", 0),
            kw.get("search_intent", ""),
            kw.get("price_segment", ""),
            kw.get("trend", ""),
            kw.get("trend_reason", ""),
        ))

    conn.commit()
    conn.close()
    return session_id


def get_trend_sessions(genre: str = "") -> list:
    """
    トレンドセッション一覧を返す。
    genre を指定するとそのジャンルのみ絞り込む。
    """
    conn = get_connection()
    cur  = conn.cursor()
    if genre:
        cur.execute("""
            SELECT * FROM trend_sessions
            WHERE genre = ?
            ORDER BY id DESC
        """, (genre,))
    else:
        cur.execute("""
            SELECT * FROM trend_sessions
            ORDER BY id DESC
        """)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def get_trend_keywords_by_genre(genre: str) -> list:
    """
    指定ジャンルの全キーワードトレンドデータを時系列で返す。
    グラフ描画に使う。
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT
            tk.*,
            ts.created_at AS session_date,
            ts.genre_trend
        FROM trend_keywords tk
        JOIN trend_sessions ts ON tk.session_id = ts.id
        WHERE tk.genre = ?
        ORDER BY tk.session_id ASC
    """, (genre,))
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def get_all_genres() -> list:
    """
    保存済みのジャンル一覧（重複なし）を返す。
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT DISTINCT genre FROM trend_sessions
        ORDER BY genre ASC
    """)
    rows = [row["genre"] for row in cur.fetchall()]
    conn.close()
    return rows


def get_genre_avg_scores() -> list:
    """
    ジャンルごとの最新平均スコアを返す。
    ジャンル比較グラフに使う。
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT genre, AVG(avg_score) as avg_score, COUNT(*) as session_count
        FROM trend_sessions
        GROUP BY genre
        ORDER BY avg_score DESC
    """)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows
