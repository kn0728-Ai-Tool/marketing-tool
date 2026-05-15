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
