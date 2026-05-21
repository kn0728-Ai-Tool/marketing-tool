# app.py  v3.0
# 追加機能：トレンド予測グラフ・ヒートマップ・年代別AI分析（タブ④拡張）

import streamlit as st
import pandas as pd
import numpy as np
import datetime
from zoneinfo import ZoneInfo
JST = ZoneInfo("Asia/Tokyo")
import json
import time
import re
import plotly.graph_objects as go
import plotly.express as px
from report import generate_html_report
from analyzer import get_client, analyze_keyword_structured
from csv_analyzer import (
    detect_columns, prepare_dataframe,
    analyze_csv_with_ai, get_top_bottom_keywords,
)
from trend_analyzer import analyze_trend_keywords
from database import (
    init_db, save_session,
    get_all_sessions, get_session_results,
    get_keyword_history, get_all_keywords,
    delete_session, get_segment_stats,
    init_trend_db, save_trend_session,
    get_trend_sessions, get_trend_keywords_by_genre,
    get_all_genres, get_genre_avg_scores,
)

init_db()
init_trend_db()

st.set_page_config(
    page_title="AI キーワード分析ツール",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ─── ベースフォント ─── */
html, body, [class*="css"] {
  font-family: 'Hiragino Sans', 'Yu Gothic UI', 'Meiryo', sans-serif;
}

/* ─── ヒーローバナー ─── */
.hero-banner {
  background: #0f172a;
  border-radius: 12px;
  padding: 32px 40px;
  margin-bottom: 24px;
  color: white;
  position: relative;
  overflow: hidden;
  border: 1px solid #1e293b;
}
.hero-banner::before {
  content: '';
  position: absolute;
  top: 0; right: 0; bottom: 0; left: 0;
  background: linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(6,182,212,0.08) 100%);
  pointer-events: none;
}
.hero-banner::after {
  content: '';
  position: absolute;
  top: -60px; right: -60px;
  width: 240px; height: 240px;
  background: radial-gradient(circle, rgba(99,102,241,0.2) 0%, transparent 70%);
  pointer-events: none;
}
.hero-title {
  font-size: 24px; font-weight: 800; margin: 0 0 6px;
  letter-spacing: -0.5px;
}
.hero-sub {
  font-size: 13px; opacity: 0.65; margin: 0; line-height: 1.7;
}
.hero-badge {
  display: inline-block;
  background: rgba(99,102,241,0.25);
  border: 1px solid rgba(99,102,241,0.4);
  border-radius: 4px;
  padding: 2px 10px; font-size: 11px;
  margin-bottom: 10px; letter-spacing: 0.05em;
  color: #a5b4fc;
}

/* ─── タブ ─── */
.stTabs [data-baseweb="tab-list"] {
  gap: 2px;
  border-bottom: 1px solid #e2e8f0;
  background: transparent;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 6px 6px 0 0;
  padding: 9px 18px;
  font-weight: 600;
  font-size: 13px;
  color: #64748b;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-bottom: none;
  transition: all 0.15s;
}
.stTabs [data-baseweb="tab"]:hover {
  color: #4338ca;
  background: #eef2ff;
}
.stTabs [aria-selected="true"] {
  background: white !important;
  color: #4338ca !important;
  border-color: #e2e8f0 !important;
  box-shadow: 0 -2px 0 #4338ca inset;
}

/* ─── メトリクスカード ─── */
[data-testid="metric-container"] {
  background: white;
  border: 1px solid #e8eaf0;
  border-radius: 10px;
  padding: 16px 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  transition: transform 0.15s, box-shadow 0.15s;
}
[data-testid="metric-container"]:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

/* ─── バッジ ─── */
.badge {
  display: inline-block;
  padding: 3px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
}
.badge-budget   { background: #d1fae5; color: #065f46; }
.badge-standard { background: #dbeafe; color: #1e40af; }
.badge-premium  { background: #ede9fe; color: #5b21b6; }
.badge-luxury   { background: #1e293b; color: #e2e8f0; }

/* ─── キーワードカード ─── */
.kw-card {
  background: white;
  border-radius: 10px;
  padding: 22px 24px;
  margin-bottom: 14px;
  border: 1px solid #e8eaf0;
  box-shadow: 0 1px 6px rgba(0,0,0,0.04);
  transition: box-shadow 0.15s, border-color 0.15s;
}
.kw-card:hover {
  box-shadow: 0 4px 16px rgba(67,56,202,0.08);
  border-color: #c7d2fe;
}
.kw-title  { font-size: 17px; font-weight: 700; color: #1e293b; margin-bottom: 12px; }
.kw-meta   { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 14px; align-items: center; }
.meta-chip {
  background: #f1f5f9;
  border-radius: 4px;
  padding: 3px 10px;
  font-size: 12px;
  color: #475569;
}

/* ─── スコアバー ─── */
.score-wrap  { margin: 10px 0; }
.score-label {
  font-size: 12px; color: #64748b; margin-bottom: 4px;
  display: flex; justify-content: space-between;
}
.score-bg   { background: #f1f5f9; border-radius: 99px; height: 7px; overflow: hidden; }
.score-fill { height: 7px; border-radius: 99px; }

/* ─── 広告文カード ─── */
.ad-card {
  background: #fafbff;
  border: 1px solid #e8eaf0;
  border-top: 3px solid #4338ca;
  border-radius: 8px;
  padding: 14px 16px;
  position: relative;
  margin-bottom: 8px;
}
.ad-num        { position: absolute; top: 9px; right: 11px; font-size: 11px; color: #a5b4fc; font-weight: 700; }
.ad-title-text { font-size: 14px; font-weight: 700; color: #312e81; margin-bottom: 6px; line-height: 1.4; }
.ad-desc-text  { font-size: 12px; color: #4b5563; line-height: 1.65; }
.ad-appeal     { margin-top: 8px; font-size: 11px; color: #4338ca; font-weight: 600; }

/* ─── アドバイスボックス ─── */
.advice-box {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-left: 3px solid #d97706;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 13px;
  color: #78350f;
  margin-top: 12px;
  line-height: 1.65;
}
.lp-advice-box {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-left: 3px solid #16a34a;
  border-radius: 8px;
  padding: 10px 16px;
  font-size: 13px;
  color: #14532d;
  margin: 6px 0;
}

/* ─── インサイトカード ─── */
.insight-card {
  background: white;
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 12px;
  border: 1px solid #e8eaf0;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.insight-card-title {
  font-size: 14px; font-weight: 700; color: #1e293b;
  margin-bottom: 10px; padding-bottom: 8px;
  border-bottom: 1px solid #f1f5f9;
}
.insight-item {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 7px 0; border-bottom: 1px solid #f8fafc;
  font-size: 13px; color: #334155; line-height: 1.55;
}
.insight-item:last-child { border-bottom: none; }
.insight-icon { font-size: 14px; flex-shrink: 0; margin-top: 1px; }

/* ─── 注目キーワードカード ─── */
.top-kw-card {
  background: #fafbff;
  border: 1px solid #e0e7ff;
  border-left: 3px solid #4338ca;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 10px;
}
.top-kw-name   { font-size: 15px; font-weight: 700; color: #312e81; margin-bottom: 4px; }
.top-kw-reason { font-size: 12px; color: #475569; margin-bottom: 4px; line-height: 1.5; }
.top-kw-action { font-size: 12px; color: #065f46; font-weight: 600; }

/* ─── 履歴カード ─── */
.history-card {
  background: white;
  border-radius: 8px;
  padding: 14px 18px;
  margin-bottom: 8px;
  border: 1px solid #e8eaf0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.history-date  { font-size: 13px; color: #64748b; }
.history-count { font-size: 13px; font-weight: 600; color: #4338ca; }

/* ─── トレンドバッジ ─── */
.trend-badge-up   { background: #d1fae5; color: #065f46; padding: 3px 10px; border-radius: 4px; font-size: 12px; font-weight: 700; }
.trend-badge-flat { background: #fef3c7; color: #92400e; padding: 3px 10px; border-radius: 4px; font-size: 12px; font-weight: 700; }
.trend-badge-down { background: #fee2e2; color: #991b1b; padding: 3px 10px; border-radius: 4px; font-size: 12px; font-weight: 700; }

/* ─── トレンドインサイトボックス ─── */
.trend-insight-box {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-left: 3px solid #0284c7;
  border-radius: 8px;
  padding: 16px 20px;
  font-size: 14px;
  color: #0c4a6e;
  margin: 12px 0;
  line-height: 1.75;
}

/* ─── セクションタイトル ─── */
.section-title {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  margin: 28px 0 14px;
  padding-left: 10px;
  border-left: 3px solid #4338ca;
}

/* ─── 空ステート ─── */
.empty-state {
  background: #f8fafc;
  border: 1.5px dashed #c7d2fe;
  border-radius: 12px;
  padding: 48px;
  text-align: center;
}
.empty-state-icon  { font-size: 40px; margin-bottom: 12px; }
.empty-state-title { font-size: 15px; font-weight: 700; color: #4338ca; margin-bottom: 8px; }
.empty-state-desc  { font-size: 13px; color: #64748b; line-height: 1.6; }

/* ─── サイドバー ─── */
[data-testid="stSidebar"] { background: #0f172a !important; }
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] .stTextInput input {
  background: #1e293b !important;
  border: 1px solid #334155 !important;
  color: #f1f5f9 !important;
  border-radius: 6px;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
  color: #f1f5f9 !important;
}

/* ─── レスポンシブ ─── */
@media (max-width: 768px) {
  .hero-title  { font-size: 19px; }
  .hero-banner { padding: 22px 20px; }
}
</style>
""", unsafe_allow_html=True)

# =====================================
# 定数
# =====================================
SEGMENT_INFO = {
    "Budget":   {"badge":"badge-budget",   "emoji":"","label":"Budget — コスパ重視",  "color":"#10b981","strategy":"コスパ訴求・割引訴求・最安値強調"},
    "Standard": {"badge":"badge-standard", "emoji":"","label":"Standard — 標準層",    "color":"#3b82f6","strategy":"機能・信頼性・バランス訴求"},
    "Premium":  {"badge":"badge-premium",  "emoji":"","label":"Premium — 品質重視",   "color":"#8b5cf6","strategy":"品質・体験・専門性訴求"},
    "Luxury":   {"badge":"badge-luxury",   "emoji":"","label":"Luxury — 高級志向",    "color":"#1f2937","strategy":"ブランド・希少性・ステータス訴求"},
}
INTENT_EMOJI = {
    "比較検討段階":"","購買直前":"","情報収集":"","価格調査":"",
}
TREND_BADGE = {
    "上昇":   '<span class="trend-badge-up">↑ 上昇</span>',
    "横ばい": '<span class="trend-badge-flat">→ 横ばい</span>',
    "下降":   '<span class="trend-badge-down">↓ 下降</span>',
}

# グラフ色（線・塗りつぶし）
CHART_COLORS = [
    {"line": "#6366f1", "fill": "rgba(99,102,241,0.05)"},
    {"line": "#10b981", "fill": "rgba(16,185,129,0.05)"},
    {"line": "#f59e0b", "fill": "rgba(245,158,11,0.05)"},
    {"line": "#ef4444", "fill": "rgba(239,68,68,0.05)"},
    {"line": "#8b5cf6", "fill": "rgba(139,92,246,0.05)"},
]

api_key = ""
if hasattr(st, "secrets"):
    api_key = st.secrets.get("OPENAI_API_KEY", "")


# =====================================
# ヘルパー
# =====================================
def show_empty_state(icon, title, desc):
    st.markdown(
        f'<div class="empty-state">'
        f'<div class="empty-state-icon">{icon}</div>'
        f'<div class="empty-state-title">{title}</div>'
        f'<div class="empty-state-desc">{desc}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# =====================================
# グラフ生成関数（既存）
# =====================================
def make_score_bar_chart(valid):
    keywords = [r.get("keyword","")[:15] for r in valid]
    scores   = [r.get("purchase_score",0) for r in valid]
    segs     = [r.get("price_segment","Standard") for r in valid]
    colors   = [SEGMENT_INFO.get(s,SEGMENT_INFO["Standard"])["color"] for s in segs]
    fig = go.Figure(go.Bar(
        x=scores, y=keywords, orientation="h",
        marker=dict(color=colors),
        text=[f"{s}点" for s in scores], textposition="outside",
        hovertemplate="<b>%{y}</b><br>購買意欲: %{x}/10<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="購買意欲スコア比較", font=dict(size=15,color="#1e293b")),
        xaxis=dict(range=[0,11],title="購買意欲スコア"),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20,r=60,t=50,b=30),
        height=max(300,len(valid)*44), showlegend=False,
    )
    fig.update_xaxes(showgrid=True,gridcolor="#f1f5f9")
    fig.update_yaxes(showgrid=False)
    return fig

def make_segment_pie_chart(seg_counts):
    labels = [f"{SEGMENT_INFO[s]['emoji']} {s}" for s,c in seg_counts.items() if c>0]
    values = [c for c in seg_counts.values() if c>0]
    colors = [SEGMENT_INFO[s]["color"] for s,c in seg_counts.items() if c>0]
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker=dict(colors=colors,line=dict(color="white",width=2)),
        textinfo="label+percent", hole=0.45,
        hovertemplate="<b>%{label}</b><br>%{value}件<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="価格帯別 分布",font=dict(size=15,color="#1e293b")),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20,r=20,t=50,b=20), height=320,
    )
    return fig

def make_intent_bar_chart(valid):
    intent_counts = {}
    for r in valid:
        k = r.get("search_intent","不明")
        intent_counts[k] = intent_counts.get(k,0)+1
    colors_map = {"比較検討段階":"#6366f1","購買直前":"#10b981","情報収集":"#f59e0b","価格調査":"#ef4444"}
    labels     = [f"{INTENT_EMOJI.get(k,'🔎')} {k}" for k in intent_counts]
    values     = list(intent_counts.values())
    bar_colors = [colors_map.get(k,"#94a3b8") for k in intent_counts]
    fig = go.Figure(go.Bar(
        x=labels, y=values, marker=dict(color=bar_colors),
        text=values, textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y}件<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="検索意図別 件数",font=dict(size=15,color="#1e293b")),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20,r=20,t=50,b=30), height=300, showlegend=False,
    )
    fig.update_yaxes(showgrid=True,gridcolor="#f1f5f9",dtick=1)
    fig.update_xaxes(showgrid=False)
    return fig

def make_history_line_chart(history, keyword):
    dates  = [h.get("session_date","") for h in history]
    scores = [h.get("purchase_score",0) for h in history]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=scores, mode="lines+markers+text",
        text=scores, textposition="top center",
        line=dict(color="#6366f1",width=3),
        marker=dict(size=10,color="#6366f1"),
        hovertemplate="<b>%{x}</b><br>スコア: %{y}/10<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=f"「{keyword}」の購買意欲推移",font=dict(size=14,color="#1e293b")),
        xaxis=dict(title="分析日時"),
        yaxis=dict(title="購買意欲スコア",range=[0,11],dtick=1),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20,r=20,t=50,b=30), height=280,
    )
    fig.update_xaxes(showgrid=True,gridcolor="#f1f5f9")
    fig.update_yaxes(showgrid=True,gridcolor="#f1f5f9")
    return fig

def make_csv_bar_chart(df, x_col, y_col, title, color="#6366f1"):
    fig = go.Figure(go.Bar(
        x=df[x_col].astype(str).str[:20], y=df[y_col],
        marker=dict(color=color),
        text=df[y_col].round(2), textposition="outside",
        hovertemplate=f"<b>%{{x}}</b><br>{y_col}: %{{y}}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=14,color="#1e293b")),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20,r=20,t=50,b=80),
        height=360, showlegend=False,
        xaxis=dict(tickangle=-30),
    )
    fig.update_yaxes(showgrid=True,gridcolor="#f1f5f9")
    fig.update_xaxes(showgrid=False)
    return fig

def make_trend_line_chart(trend_data, genre):
    df = pd.DataFrame(trend_data)
    if df.empty:
        return go.Figure()
    fig = go.Figure()
    keywords = df["keyword"].unique()
    for i, kw in enumerate(keywords):
        kw_df = df[df["keyword"] == kw].sort_values("session_date")
        c = CHART_COLORS[i % len(CHART_COLORS)]
        fig.add_trace(go.Scatter(
            x=kw_df["session_date"], y=kw_df["purchase_score"],
            mode="lines+markers", name=kw[:15],
            line=dict(color=c["line"], width=2),
            marker=dict(size=8, color=c["line"]),
            hovertemplate=f"<b>{kw}</b><br>%{{x}}<br>購買意欲: %{{y}}/10<extra></extra>",
        ))
    fig.update_layout(
        title=dict(text=f"【{genre}】キーワード別 購買意欲スコア推移",
                   font=dict(size=15,color="#1e293b")),
        xaxis=dict(title="分析日時"),
        yaxis=dict(title="購買意欲スコア", range=[0,11], dtick=1),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20,r=20,t=60,b=40), height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True,gridcolor="#f1f5f9")
    fig.update_yaxes(showgrid=True,gridcolor="#f1f5f9")
    return fig

def make_heatmap_chart(trend_data, genre):
    df = pd.DataFrame(trend_data)
    if df.empty:
        return go.Figure()
    latest = df.sort_values("session_date").groupby("keyword").last().reset_index()
    pivot  = latest[["keyword","purchase_score"]].set_index("keyword")
    fig = go.Figure(go.Heatmap(
        z=pivot["purchase_score"].values.reshape(1,-1),
        x=pivot.index.tolist(), y=[genre],
        colorscale=[[0.0,"#fee2e2"],[0.3,"#fef3c7"],[0.6,"#d1fae5"],[1.0,"#065f46"]],
        zmin=0, zmax=10,
        text=pivot["purchase_score"].values.reshape(1,-1),
        texttemplate="%{text}", textfont=dict(size=14,color="white"),
        hovertemplate="<b>%{x}</b><br>購買意欲スコア: %{z}/10<extra></extra>",
        colorbar=dict(title="購買意欲"),
    ))
    fig.update_layout(
        title=dict(text=f"【{genre}】購買意欲ヒートマップ（最新）",
                   font=dict(size=15,color="#1e293b")),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20,r=20,t=60,b=80), height=220,
        xaxis=dict(tickangle=-30),
    )
    return fig

def make_ranking_chart(trend_data, genre):
    df = pd.DataFrame(trend_data)
    if df.empty:
        return go.Figure()
    latest = df.sort_values("session_date").groupby("keyword").last().reset_index()
    latest = latest.sort_values("purchase_score", ascending=True)
    score_colors = [
        "#10b981" if s >= 8 else "#f59e0b" if s >= 5 else "#ef4444"
        for s in latest["purchase_score"]
    ]
    fig = go.Figure(go.Bar(
        x=latest["purchase_score"], y=latest["keyword"].str[:15],
        orientation="h", marker=dict(color=score_colors),
        text=latest["purchase_score"], textposition="outside",
        hovertemplate="<b>%{y}</b><br>購買意欲: %{x}/10<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=f"【{genre}】キーワードランキング",
                   font=dict(size=15,color="#1e293b")),
        xaxis=dict(range=[0,11],title="購買意欲スコア"),
        yaxis=dict(title=""),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20,r=60,t=60,b=30),
        height=max(300,len(latest)*44), showlegend=False,
    )
    fig.update_xaxes(showgrid=True,gridcolor="#f1f5f9")
    fig.update_yaxes(showgrid=False)
    return fig

def make_genre_compare_chart(genre_scores):
    if not genre_scores:
        return go.Figure()
    genres = [g["genre"] for g in genre_scores]
    scores = [round(g["avg_score"],1) for g in genre_scores]
    bar_colors = [
        "#10b981" if s >= 7 else "#f59e0b" if s >= 4 else "#ef4444"
        for s in scores
    ]
    fig = go.Figure(go.Bar(
        x=genres, y=scores, marker=dict(color=bar_colors),
        text=[f"{s}点" for s in scores], textposition="outside",
        hovertemplate="<b>%{x}</b><br>平均購買意欲: %{y}/10<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="ジャンル別 平均購買意欲スコア比較",
                   font=dict(size=15,color="#1e293b")),
        xaxis=dict(title="ジャンル"),
        yaxis=dict(range=[0,11],title="平均購買意欲スコア"),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20,r=20,t=60,b=60), height=360, showlegend=False,
    )
    fig.update_yaxes(showgrid=True,gridcolor="#f1f5f9")
    fig.update_xaxes(showgrid=False)
    return fig


# =====================================
# キーワードカード表示
# =====================================
def render_keyword_cards(filtered: list):
    for r in filtered:
        seg    = r.get("price_segment","Standard")
        info   = SEGMENT_INFO.get(seg,SEGMENT_INFO["Standard"])
        score  = r.get("purchase_score",0)
        intent = r.get("search_intent","")
        ie     = INTENT_EMOJI.get(intent,"🔎")
        emotion    = r.get("emotion","")
        competitor = r.get("competitor_position","")
        cta        = r.get("cta_suggestion","")
        lp_advice  = r.get("lp_advice","")

        st.markdown(
            f'<div class="kw-card">'
            f'<div class="kw-title">{info["emoji"]} {r["keyword"]}</div>'
            f'<div class="kw-meta">'
            f'<span class="badge {info["badge"]}">{info["label"]}</span>'
            f'<span class="meta-chip">{ie} {intent}</span>'
            f'<span class="meta-chip">意図: {r.get("intent_reason","")}</span>'
            f'<span class="meta-chip">層の理由: {r.get("segment_reason","")}</span>'
            f'</div>'
            f'<div class="score-wrap">'
            f'<div class="score-label"><span>購買意欲スコア</span>'
            f'<span style="font-weight:700;color:{info["color"]};">{score} / 10</span></div>'
            f'<div class="score-bg">'
            f'<div class="score-fill" style="width:{score*10}%;background:{info["color"]};"></div>'
            f'</div></div>'
            f'<div style="font-size:13px;font-weight:600;color:#475569;margin:16px 0 8px;">広告文案（3パターン）</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        ad_cols = st.columns(3)
        for i, ad in enumerate(r.get("ad_copies",[])[:3]):
            with ad_cols[i]:
                title_text   = ad.get("title","")
                desc_text    = ad.get("description","")
                appeal_point = ad.get("appeal_point","")
                appeal_html  = f'<div class="ad-appeal">{appeal_point}</div>' if appeal_point else ""
                st.markdown(
                    f'<div class="ad-card"><div class="ad-num">案{i+1}</div>'
                    f'<div class="ad-title-text">{title_text}</div>'
                    f'<div class="ad-desc-text">{desc_text}</div>'
                    f'{appeal_html}</div>',
                    unsafe_allow_html=True,
                )
                with st.expander("コピー", expanded=False):
                    st.code(f"【タイトル】{title_text}\n【説明文】{desc_text}", language=None)

        chips = ""
        if emotion:    chips += f'<span class="meta-chip">感情: {emotion}</span>'
        if competitor: chips += f'<span class="meta-chip">差別化: {competitor}</span>'
        if cta:        chips += f'<span class="meta-chip">CTA案: {cta}</span>'
        if chips:
            st.markdown(f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin:8px 0;">{chips}</div>', unsafe_allow_html=True)
        if lp_advice:
            st.markdown(f'<div class="lp-advice-box">LP 改善提案：{lp_advice}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="advice-box">アドバイス：{r.get("advice","")}</div><br>', unsafe_allow_html=True)


# =====================================
# サイドバー
# =====================================
with st.sidebar:
    st.markdown("### AI キーワード分析")
    st.markdown("---")
    if not api_key:
        st.markdown("**APIキー設定**")
        api_key = st.text_input("OpenAI APIキー", type="password",
            placeholder="sk-proj-...", label_visibility="collapsed")
    else:
        st.markdown("**APIキー**")
        st.success("設定済み")
    st.markdown("---")
    st.markdown("**使い方**")
    st.markdown("1. キーワード入力 or CSV アップロード\n2. 「分析開始」をクリック\n3. トレンド分析で市場推移を確認\n4. レポートをダウンロード")
    st.markdown("---")
    st.markdown("**価格帯の目安**")
    for seg, info in SEGMENT_INFO.items():
        st.markdown(f"**{seg}**  \n{info['strategy']}\n")
    st.markdown("---")
    st.caption("v3.0 | Powered by OpenAI")


# =====================================
# ヒーローバナー
# =====================================
st.markdown("""
<div class="hero-banner">
  <div class="hero-badge">AI Powered Marketing Tool</div>
  <div class="hero-title">AI キーワード分析ツール</div>
  <div class="hero-sub">
    キーワード入力または CSV アップロードで、トレンド・改善点・広告文案を AI が自動生成。<br>
    Google Trends の実データで日本市場のトレンドをひと目で把握できます。
  </div>
</div>
""", unsafe_allow_html=True)


# =====================================
# タブ定義
# =====================================
tab_analyze, tab_result, tab_chart, tab_trend, tab_csv, tab_summary, tab_digest, tab_history, tab_guide = st.tabs([
    "キーワード分析",
    "分析結果",
    "グラフ分析",
    "トレンド分析",
    "CSV分析",
    "文章要約・整形",
    "ダイジェスト & プレゼン",
    "分析履歴",
    "使い方ガイド",
])


# =====================================
# タブ①：キーワード分析
# =====================================
with tab_analyze:
    col_input, col_btn = st.columns([3,1])
    with col_input:
        default_kw = st.session_state.pop("csv_keywords","")
        keywords_input = st.text_area(
            "分析したいキーワードを入力（1行に1つ・最大20件）",
            value=default_kw, height=180,
            placeholder="格安スマホ 乗り換え おすすめ\niPhone 最新 購入\nスマホ 高級 おすすめ",
        )
    with col_btn:
        st.markdown("<br>"*3, unsafe_allow_html=True)
        run_button = st.button("分析開始", use_container_width=True, type="primary")
        kw_list  = [k.strip() for k in keywords_input.strip().splitlines() if k.strip()]
        st.info(f"入力数：**{len(kw_list)}件**")
        memo     = st.text_input("メモ（任意）", placeholder="例：競合調査 2024年6月")
        industry = st.text_input("業種・ジャンル（任意）", placeholder="例：スマートフォン / 不動産")

    if run_button:
        if not api_key:
            st.error("サイドバーに API キーを入力してください。")
        elif not kw_list:
            st.warning("キーワードを1つ以上入力してください。")
        else:
            if len(kw_list) > 20:
                st.warning("最初の20件を分析します。")
                kw_list = kw_list[:20]
            client   = get_client(api_key)
            results  = []
            progress = st.progress(0)
            status   = st.empty()
            for i, kw in enumerate(kw_list):
                status.markdown(f"分析中... **{kw}** ({i+1}/{len(kw_list)})")
                progress.progress((i+1)/len(kw_list))
                try:
                    data = analyze_keyword_structured(client, kw, industry=industry)
                    results.append(data)
                except Exception as e:
                    results.append({"keyword":kw,"error":str(e)})
                time.sleep(0.5)
            progress.empty()
            session_id = save_session(results, memo=memo)
            status.success(f"{len(kw_list)}件の分析完了（セッションID: {session_id}）")
            st.session_state["results"] = results


# =====================================
# タブ②：分析結果
# =====================================
with tab_result:
    if "results" not in st.session_state:
        show_empty_state("📝","まだ分析結果がありません",
            "「キーワード分析」タブでキーワードを入力して分析してください。")
    else:
        if "loaded_session_id" in st.session_state:
            sid = st.session_state.pop("loaded_session_id")
            st.success(f"セッション {sid} の分析結果を読み込みました。")
        results = st.session_state["results"]
        valid   = [r for r in results if "error" not in r]
        if not valid:
            st.error("有効な分析結果がありません。")
        else:
            st.markdown('<p class="section-title">分析サマリー</p>', unsafe_allow_html=True)
            seg_counts = {s:0 for s in SEGMENT_INFO}
            for r in valid:
                seg = r.get("price_segment","")
                if seg in seg_counts: seg_counts[seg]+=1
            avg_score = sum(r.get("purchase_score",0) for r in valid)/len(valid)
            c1,c2,c3,c4,c5,c6 = st.columns(6)
            c1.metric("分析件数",     f"{len(valid)}件")
            c2.metric("平均購買意欲", f"{avg_score:.1f}/10")
            c3.metric("Budget",   f"{seg_counts['Budget']}件")
            c4.metric("Standard", f"{seg_counts['Standard']}件")
            c5.metric("Premium",  f"{seg_counts['Premium']}件")
            c6.metric("Luxury",   f"{seg_counts['Luxury']}件")
            st.markdown("---")
            f1,f2,f3 = st.columns(3)
            with f1:
                seg_filter = st.multiselect("価格帯",list(SEGMENT_INFO.keys()),default=list(SEGMENT_INFO.keys()))
            with f2:
                intent_opts = sorted(set(r.get("search_intent","") for r in valid if r.get("search_intent")))
                intent_filter = st.multiselect("検索意図",intent_opts,default=intent_opts)
            with f3:
                score_min = st.slider("購買意欲スコア（最小）",1,10,1)
            filtered = [
                r for r in valid
                if r.get("price_segment") in seg_filter
                and r.get("search_intent") in intent_filter
                and r.get("purchase_score",0) >= score_min
            ]
            st.caption(f"表示中：{len(filtered)}件 / {len(valid)}件")
            st.markdown("---")
            st.markdown('<p class="section-title">キーワード別 詳細分析</p>', unsafe_allow_html=True)
            render_keyword_cards(filtered)
            st.markdown("---")
            st.markdown('<p class="section-title">一覧比較表</p>', unsafe_allow_html=True)
            rows = []
            for r in filtered:
                ad1 = r.get("ad_copies",[{}])[0]
                rows.append({
                    "キーワード":      r.get("keyword",""),
                    "検索意図":        r.get("search_intent",""),
                    "価格帯層":        r.get("price_segment",""),
                    "購買意欲(1-10)": r.get("purchase_score",""),
                    "広告タイトル案1": ad1.get("title",""),
                    "広告説明文案1":   ad1.get("description",""),
                    "アドバイス":      r.get("advice",""),
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown('<p class="section-title">データ保存</p>', unsafe_allow_html=True)
            now        = datetime.datetime.now(JST).strftime("%Y%m%d_%H%M%S")
            csv_data   = df.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig")
            json_data  = json.dumps(results,ensure_ascii=False,indent=2).encode("utf-8")
            html_report = generate_html_report(results=filtered, title="AIキーワード分析レポート",
                memo=f"分析件数: {len(filtered)}件")
            html_data  = html_report.encode("utf-8")
            dl1,dl2,dl3 = st.columns(3)
            with dl1:
                st.download_button("CSV でダウンロード",data=csv_data,
                    file_name=f"keyword_analysis_{now}.csv",mime="text/csv",use_container_width=True)
            with dl2:
                st.download_button("JSON でダウンロード",data=json_data,
                    file_name=f"keyword_analysis_{now}.json",mime="application/json",use_container_width=True)
            with dl3:
                st.download_button("HTML レポートをダウンロード",data=html_data,
                    file_name=f"report_{now}.html",mime="text/html",use_container_width=True)
            st.markdown("---")
            st.markdown('<p class="section-title">レポートプレビュー</p>', unsafe_allow_html=True)
            st.caption("ダウンロードしたHTMLをブラウザで開いて Ctrl+P → 「PDFとして保存」でPDF化できます。")
            with st.expander("レポートのプレビューを表示", expanded=False):
                st.components.v1.html(html_report, height=600, scrolling=True)


# =====================================
# タブ③：グラフ分析
# =====================================
with tab_chart:
    if "results" not in st.session_state:
        show_empty_state("📊","まだ分析結果がありません",
            "「キーワード分析」タブでキーワードを入力して分析してください。")
    else:
        results = st.session_state["results"]
        valid   = [r for r in results if "error" not in r]
        if not valid:
            st.error("有効な分析結果がありません。")
        else:
            seg_counts = {s:0 for s in SEGMENT_INFO}
            for r in valid:
                seg = r.get("price_segment","")
                if seg in seg_counts: seg_counts[seg]+=1
            st.markdown('<p class="section-title">グラフ分析</p>', unsafe_allow_html=True)
            st.plotly_chart(make_score_bar_chart(valid), use_container_width=True)
            st.markdown("---")
            g1,g2 = st.columns(2)
            with g1: st.plotly_chart(make_segment_pie_chart(seg_counts), use_container_width=True)
            with g2: st.plotly_chart(make_intent_bar_chart(valid), use_container_width=True)
            st.markdown("---")
            st.markdown('<p class="section-title">グラフの読み方</p>', unsafe_allow_html=True)
            st.markdown("""
| グラフ | 見るべきポイント |
|--------|----------------|
| 購買意欲スコア | 8点以上は入札単価を上げる価値あり |
| 価格帯別分布 | 多い層の広告文を優先的に強化する |
| 検索意図別件数 | 「購買直前」が多ければ直接訴求が有効 |
""")


# =====================================
# タブ④：トレンド分析（Google Trends 実データ）v3.1
# =====================================
with tab_trend:
    st.markdown('<p class="section-title">日本市場 トレンド分析</p>', unsafe_allow_html=True)
    st.caption("Google Trends の実データを使って、日本市場における検索ボリュームの推移をリアルタイムで分析します。")

    # ====================================================
    # ① トレンド予測（独立セクション・常時表示）
    # ====================================================
    with st.expander("トレンド予測（キーワードを入力してすぐ使えます）", expanded=True):
        st.caption("キーワードを入力するだけで、Google Trends のデータから将来の検索トレンドを予測します。トレンド分析の実行は不要です。")
        col_p1, col_p2 = st.columns([3, 1])
        with col_p1:
            pred_keyword = st.text_input(
                "予測するキーワード",
                placeholder="例: ワイヤレスイヤホン",
                key="pred_kw",
            )
        with col_p2:
            forecast_weeks = st.number_input(
                "予測週数", min_value=4, max_value=52, value=12, step=4, key="pred_weeks"
            )

        if st.button("予測を実行", key="btn_predict"):
            if not pred_keyword:
                st.warning("キーワードを入力してください。")
            else:
                with st.spinner("Google Trends からデータ取得 & 予測中..."):
                    try:
                        from pytrends.request import TrendReq
                        pytrends = TrendReq(hl="ja-JP", tz=540)
                        pytrends.build_payload([pred_keyword], timeframe="today 12-m", geo="JP")
                        df_pred_raw = pytrends.interest_over_time()

                        if df_pred_raw.empty or pred_keyword not in df_pred_raw.columns:
                            st.warning("データが取得できませんでした。別のキーワードをお試しください。")
                        else:
                            dates_p  = df_pred_raw.index.strftime("%Y-%m-%d").tolist()
                            values_p = df_pred_raw[pred_keyword].tolist()

                            xp = np.arange(len(values_p), dtype=float)
                            yp = np.array(values_p, dtype=float)
                            coeffs_p = np.polyfit(xp, yp, 1)
                            slope_p  = coeffs_p[0]
                            yhat_p   = np.polyval(coeffs_p, xp)
                            ss_res_p = np.sum((yp - yhat_p) ** 2)
                            ss_tot_p = np.sum((yp - np.mean(yp)) ** 2)
                            r2_p     = float(1 - ss_res_p / ss_tot_p) if ss_tot_p != 0 else 0.0
                            std_p    = float(np.std(yp - yhat_p))

                            fw = int(forecast_weeks)
                            last_dt_p    = datetime.datetime.strptime(dates_p[-1], "%Y-%m-%d")
                            future_dates_p = [(last_dt_p + datetime.timedelta(weeks=i+1)).strftime("%Y-%m-%d") for i in range(fw)]
                            future_xp    = np.arange(len(xp), len(xp) + fw, dtype=float)
                            future_yp    = np.polyval(coeffs_p, future_xp)
                            future_yp_c  = np.clip(future_yp, 0, 100).tolist()
                            upper_p      = np.clip(future_yp + 1.96 * std_p, 0, 100).tolist()
                            lower_p      = np.clip(future_yp - 1.96 * std_p, 0, 100).tolist()

                            trend_label_p = "↑ 上昇傾向" if slope_p > 0.3 else ("↓ 下降傾向" if slope_p < -0.3 else "→ 横ばい")

                            st.session_state["pred_result"] = {
                                "keyword": pred_keyword,
                                "dates": dates_p, "values": values_p,
                                "future_dates": future_dates_p,
                                "future_y": future_yp_c,
                                "upper": upper_p, "lower": lower_p,
                                "slope": slope_p, "r2": r2_p,
                                "trend_label": trend_label_p,
                                "fw": fw,
                            }
                    except Exception as e:
                        st.error(f"エラーが発生しました: {e}")

        if "pred_result" in st.session_state:
            pr = st.session_state["pred_result"]
            m1, m2, m3 = st.columns(3)
            m1.metric("トレンド判定",  pr["trend_label"])
            m2.metric("週あたり変化",  f'{pr["slope"]:+.2f} pt')
            m3.metric("モデル精度 R²", f'{pr["r2"]:.3f}')

            fig_pred = go.Figure()
            fig_pred.add_trace(go.Scatter(
                x=pr["dates"], y=pr["values"],
                mode="lines+markers", name="実績値",
                line=dict(color="#3b82f6", width=2), marker=dict(size=4),
            ))
            fig_pred.add_trace(go.Scatter(
                x=pr["future_dates"] + pr["future_dates"][::-1],
                y=pr["upper"] + pr["lower"][::-1],
                fill="toself", fillcolor="rgba(251,146,60,0.15)",
                line=dict(color="rgba(255,255,255,0)"),
                name="95% 信頼区間", showlegend=True,
            ))
            fig_pred.add_trace(go.Scatter(
                x=pr["future_dates"], y=pr["future_y"],
                mode="lines+markers", name="予測値",
                line=dict(color="#f97316", width=2, dash="dash"),
                marker=dict(size=5, symbol="diamond"),
            ))
            fig_pred.update_layout(
                title=dict(text=f'「{pr["keyword"]}」トレンド予測（{pr["fw"]}週先まで）', font=dict(size=14, color="#1e293b")),
                xaxis_title="日付", yaxis_title="検索インデックス（0-100）",
                legend=dict(orientation="h", y=-0.2),
                height=420, plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=20, r=20, t=60, b=60),
            )
            fig_pred.add_vline(x=pr["dates"][-1], line_dash="dot", line_color="gray", annotation_text="現在")
            st.plotly_chart(fig_pred, use_container_width=True)

    st.markdown("---")

    # ---- 入力エリア ----
    col_kws, col_opts = st.columns([2,1])
    with col_kws:
        trend_keywords_input = st.text_area(
            "調べたいキーワードを入力（1行に1つ・最大5件）",
            height=140,
            placeholder="格安スマホ\niPhone\nSIMフリー\nスマホ 乗り換え\nアンドロイド",
            help="Google Trendsは1回のリクエストで最大5キーワードまで比較できます",
        )
    with col_opts:
        timeframe_option = st.selectbox(
            "期間を選択",
            options=[
                ("直近1ヶ月",  "today 1-m"),
                ("直近3ヶ月",  "today 3-m"),
                ("直近12ヶ月", "today 12-m"),
                ("直近5年",    "today 5-y"),
            ],
            format_func=lambda x: x[0],
            index=1,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        trend_run = st.button("市場トレンドを取得", type="primary", use_container_width=True)
        st.caption("※ Google Trendsへのアクセスのため\n取得に10〜20秒かかります")

    trend_kw_list = [k.strip() for k in trend_keywords_input.strip().splitlines() if k.strip()]

    if trend_run:
        if not trend_kw_list:
            st.warning("キーワードを1つ以上入力してください。")
        else:
            if len(trend_kw_list) > 5:
                st.warning("最初の5件を取得します。")
                trend_kw_list = trend_kw_list[:5]
            with st.spinner("Google Trends から日本市場データを取得中...（10〜20秒かかります）"):
                try:
                    from market_trend import fetch_market_trends
                    market_data = fetch_market_trends(
                        trend_kw_list,
                        timeframe=timeframe_option[1],
                    )
                    st.session_state["market_data"]     = market_data
                    st.session_state["market_keywords"] = trend_kw_list
                    st.success(f"データ取得完了（取得日時: {market_data['fetched_at']}）")
                except Exception as e:
                    st.error(f"データ取得中にエラーが発生しました: {e}")
                    st.info("Google Trendsへのアクセスが一時的に制限されている場合があります。1〜2分後に再試行してください。")

    # ---- 取得済みデータの表示 ----
    if "market_data" not in st.session_state:
        show_empty_state("📈","市場トレンドデータがありません",
            "キーワードを入力して「市場トレンドを取得」を押してください。\nGoogle Trendsの実データで日本市場の検索ボリューム推移を表示します。")
    else:
        market_data = st.session_state["market_data"]
        kws         = st.session_state.get("market_keywords",[])
        trend_df    = market_data.get("trend_df", pd.DataFrame())
        summaries   = market_data.get("summaries",[])

        # ---- サマリーカード ----
        st.markdown('<p class="section-title">キーワード別サマリー</p>', unsafe_allow_html=True)
        # Google Trends取得時のエラーを表示
        if market_data.get("error_trends"):
            st.error(f"トレンドデータ取得エラー: {market_data['error_trends']}")

        if summaries:
            cols = st.columns(len(summaries))
            trend_icons  = {"上昇":"↑","横ばい":"→","下降":"↓"}
            trend_colors = {"上昇":"#10b981","横ばい":"#f59e0b","下降":"#ef4444"}
            for i, s in enumerate(summaries):
                trend      = s.get("trend","")
                icon       = trend_icons.get(trend,"")
                color      = trend_colors.get(trend,"#64748b")
                change_pct = s.get("change_pct",0)
                change_str = f"+{change_pct}%" if change_pct >= 0 else f"{change_pct}%"
                with cols[i]:
                    st.markdown(
                        f'<div style="background:white;border-radius:12px;padding:16px;'
                        f'border:1px solid #e8eaf0;box-shadow:0 2px 8px rgba(0,0,0,0.05);text-align:center;">'
                        f'<div style="font-size:12px;color:#64748b;margin-bottom:4px;">{s["keyword"][:12]}</div>'
                        f'<div style="font-size:24px;font-weight:800;color:{color};">{icon} {trend}</div>'
                        f'<div style="font-size:13px;color:{color};font-weight:600;">{change_str}</div>'
                        f'<div style="font-size:11px;color:#94a3b8;margin-top:4px;">'
                        f'最新値: {s["latest"]} | 平均: {s["avg"]}</div>'
                        f'<div style="font-size:11px;color:#94a3b8;">ピーク: {s["peak_date"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
        else:
            st.info("サマリーデータがありません。")

        st.markdown("---")

        # ---- 時系列グラフ ----
        if not trend_df.empty:
            st.markdown('<p class="section-title">検索ボリューム推移（Google Trends）</p>', unsafe_allow_html=True)
            fig = go.Figure()
            for i, kw in enumerate(kws):
                if kw in trend_df.columns:
                    c = CHART_COLORS[i % len(CHART_COLORS)]
                    fig.add_trace(go.Scatter(
                        x=trend_df.index,
                        y=trend_df[kw],
                        mode="lines",
                        name=kw,
                        line=dict(color=c["line"], width=2.5),
                        fill="tozeroy",
                        fillcolor=c["fill"],
                        hovertemplate=f"<b>{kw}</b><br>%{{x|%Y-%m-%d}}<br>人気度: %{{y}}<extra></extra>",
                    ))
            fig.update_layout(
                title=dict(
                    text="日本市場 検索ボリューム推移（Google Trends・数値は相対的な人気度 0〜100）",
                    font=dict(size=14,color="#1e293b"),
                ),
                xaxis=dict(title="日付",showgrid=True,gridcolor="#f1f5f9"),
                yaxis=dict(title="検索人気度（0〜100）",range=[0,105]),
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=20,r=20,t=70,b=40), height=420,
                hovermode="x unified",
                legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("※ Google Trendsの数値は絶対的な検索数ではなく、期間内の最高値を100とした相対的な人気度です。")

        st.markdown("---")

        # ---- 地域別グラフ ----
        region_df = market_data.get("region_df", pd.DataFrame())
        if not region_df.empty:
            st.markdown('<p class="section-title">都道府県別 検索人気度</p>', unsafe_allow_html=True)
            first_kw = kws[0] if kws else ""
            if first_kw and first_kw in region_df.columns:
                top_regions = region_df[first_kw].sort_values(ascending=False).head(15)
                rg1, rg2 = st.columns([2,1])
                with rg1:
                    fig_region = go.Figure(go.Bar(
                        x=top_regions.values, y=top_regions.index,
                        orientation="h", marker=dict(color="#6366f1"),
                        text=top_regions.values, textposition="outside",
                        hovertemplate="<b>%{y}</b><br>人気度: %{x}<extra></extra>",
                    ))
                    fig_region.update_layout(
                        title=dict(text=f"「{first_kw}」の都道府県別 検索人気度 TOP15",
                                   font=dict(size=13,color="#1e293b")),
                        xaxis=dict(range=[0,115],title="人気度"),
                        yaxis=dict(autorange="reversed"),
                        plot_bgcolor="white", paper_bgcolor="white",
                        margin=dict(l=20,r=60,t=50,b=30),
                        height=420, showlegend=False,
                    )
                    fig_region.update_xaxes(showgrid=True,gridcolor="#f1f5f9")
                    st.plotly_chart(fig_region, use_container_width=True)
                with rg2:
                    st.markdown('<div class="insight-card"><div class="insight-card-title">地域別 インサイト</div>', unsafe_allow_html=True)
                    for region, val in top_regions.head(3).items():
                        st.markdown(
                            f'<div class="insight-item"><span class="insight-icon">·</span>'
                            f'<div><b>{region}</b>: 人気度 {val}</div></div>',
                            unsafe_allow_html=True,
                        )
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.caption("※ 最も検索している地域が100、それに対する相対値で表示")
            st.markdown("---")

        # ---- 関連キーワード ----
        related_queries = market_data.get("related_queries",{})
        if related_queries:
            st.markdown('<p class="section-title">関連キーワード（Google Trends）</p>', unsafe_allow_html=True)
            st.caption("実際にこのキーワードと一緒に検索されているワードです。広告キーワードの拡張に活用できます。")
            rq_cols = st.columns(min(len(related_queries),3))
            for i, (kw, queries) in enumerate(related_queries.items()):
                with rq_cols[i % 3]:
                    st.markdown(
                        f'<div class="insight-card">'
                        f'<div class="insight-card-title">「{kw}」の関連キーワード</div>',
                        unsafe_allow_html=True,
                    )
                    if queries:
                        for q in queries[:5]:
                            query_text = q.get("query","")
                            value      = q.get("value","")
                            st.markdown(
                                f'<div class="insight-item"><span class="insight-icon">🔎</span>'
                                f'<div>{query_text} <span style="color:#6366f1;font-size:11px;">({value}%)</span></div></div>',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.caption("関連キーワードが見つかりませんでした")
                    st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("---")

        # ---- 最新ニュース ----
        news_data = market_data.get("news",{})
        if news_data:
            st.markdown('<p class="section-title">最新ニュース（Google News）</p>', unsafe_allow_html=True)
            st.caption("このキーワードに関する日本の最新ニュースです。市場の動きを把握するのに役立ちます。")
            for kw, news_list in news_data.items():
                if not news_list:
                    continue
                st.markdown(f"**「{kw}」のニュース**")
                for news in news_list:
                    title   = news.get("title","")
                    link    = news.get("link","")
                    pubdate = news.get("pubDate","")
                    st.markdown(
                        f'<div class="insight-item"><span class="insight-icon">·</span>'
                        f'<div>'
                        f'<a href="{link}" target="_blank" style="color:#3730a3;font-weight:600;text-decoration:none;">{title}</a>'
                        f'<div style="font-size:11px;color:#94a3b8;margin-top:2px;">{pubdate}</div>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )
                st.markdown("")
            st.markdown("---")

        # ---- AIによる市場分析 ----
        st.markdown('<p class="section-title">AI による市場トレンド分析</p>', unsafe_allow_html=True)
        st.caption("取得した Google Trends データをもとに、AI が市場動向と広告戦略を分析します。")
        if not api_key:
            st.warning("サイドバーに API キーを入力すると、AI による分析ができます。")
        else:
            if st.button("AI で市場トレンドを分析する", type="primary"):
                with st.spinner("AIが市場データを分析中..."):
                    try:
                        summary_text = "\n".join([
                            f"- {s['keyword']}: 人気度平均{s['avg']}、{s['trend']}トレンド（{s['change_pct']:+.1f}%）、ピーク日{s['peak_date']}"
                            for s in summaries
                        ])
                        news_text = ""
                        for kw, news_list in news_data.items():
                            for n in news_list[:2]:
                                news_text += f"- {n['title']}\n"
                        from openai import OpenAI
                        oa_client = OpenAI(api_key=api_key)
                        response  = oa_client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role":"system","content":"あなたは日本市場のデジタルマーケティング専門家です。"},
                                {"role":"user","content":f"""
以下のGoogle Trendsデータと最新ニュースをもとに、日本市場のトレンドを分析してください。

【Google Trends サマリー】
{summary_text}

【最新ニュース】
{news_text}

以下の観点で分析し、マーケターが今すぐ使える具体的な提言を日本語で述べてください：
1. 市場全体のトレンド解説（2〜3文）
2. 注目すべきキーワードとその理由
3. 広告・コンテンツ戦略への提言（3点）
4. 今後1〜3ヶ月の市場予測
"""},
                            ],
                            temperature=0.7,
                            max_tokens=800,
                        )
                        st.session_state["market_ai_comment"] = response.choices[0].message.content
                    except Exception as e:
                        st.error(f"AI分析中にエラーが発生しました: {e}")

            if "market_ai_comment" in st.session_state:
                comment_html = st.session_state["market_ai_comment"].replace("\n","<br>")
                st.markdown(
                    f'<div class="trend-insight-box">'
                    f'AI 市場分析：<br><br>{comment_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )


        # ====================================================
        # ② ヒートマップ（トレンド分析後に自動表示）
        # ====================================================
        st.markdown("---")
        st.markdown('<p class="section-title">曜日 × 時間帯 ヒートマップ</p>', unsafe_allow_html=True)
        st.caption("トレンド分析で取得したキーワードの検索アクティビティを曜日×時間帯で自動表示します。広告配信の最適時間帯発見に活用できます。")

        heat_kw_target = kws[0] if kws else ""
        if heat_kw_target:
            try:
                days_h  = ["月", "火", "水", "木", "金", "土", "日"]
                hours_h = list(range(24))
                hour_base_h = np.array([
                    5, 3, 2, 2, 3, 8, 20, 40, 60, 70, 72, 70,
                    65, 68, 70, 72, 75, 78, 80, 75, 65, 50, 35, 18,
                ], dtype=float)
                day_coeff_h = np.array([1.0, 1.0, 1.0, 1.0, 1.1, 1.2, 1.1])

                if not trend_df.empty and heat_kw_target in trend_df.columns:
                    weekly_vals_h = trend_df[heat_kw_target].tolist()
                    scale_h = float(np.mean(weekly_vals_h[-4:])) / 70.0 if len(weekly_vals_h) >= 4 else 1.0
                else:
                    scale_h = 1.0

                rng_h = np.random.default_rng(abs(hash(heat_kw_target)) % (2**32))
                matrix_h = []
                for d_idx in range(7):
                    row_h = []
                    for h_idx in range(24):
                        val_h = hour_base_h[h_idx] * day_coeff_h[d_idx] * scale_h
                        val_h = float(np.clip(val_h * rng_h.uniform(0.9, 1.1), 0, 100))
                        row_h.append(round(val_h, 1))
                    matrix_h.append(row_h)

                fig_heat = go.Figure(data=go.Heatmap(
                    z=matrix_h,
                    x=[f"{h:02d}:00" for h in hours_h],
                    y=days_h,
                    colorscale="YlOrRd",
                    colorbar=dict(title="検索強度"),
                    hoverongaps=False,
                    hovertemplate="曜日: %{y}<br>時間: %{x}<br>強度: %{z}<extra></extra>",
                ))
                fig_heat.update_layout(
                    title=dict(text=f"「{heat_kw_target}」の曜日×時間帯ヒートマップ（推定）", font=dict(size=14, color="#1e293b")),
                    xaxis_title="時間帯", yaxis_title="曜日",
                    height=400, plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=60, b=40),
                )
                st.plotly_chart(fig_heat, use_container_width=True)
                st.caption("※ 時間帯データは週次トレンドと一般的な検索行動モデルから推定した値です。")

                matrix_np_h = np.array(matrix_h)
                peak_idx_h  = int(np.argmax(matrix_np_h))
                st.info(f"最も検索が活発な時間帯：**{days_h[peak_idx_h // 24]}曜日 {peak_idx_h % 24:02d}:00〜{peak_idx_h % 24 + 1:02d}:00**")

            except Exception as e:
                st.error(f"ヒートマップ生成中にエラーが発生しました: {e}")

        # ====================================================
        # ③ 年代別分析（折りたたみ表示・ボタン実行）
        # ====================================================
        st.markdown("---")
        with st.expander("年代別 AI 分析（クリックして展開）", expanded=False):
            st.caption("OpenAI API が各年代の関心度・購買意向・効果的な訴求チャネルを分析します。分析するキーワードはトレンド分析で取得した1件目が自動入力されます。")

            DEFAULT_RANGES = [(10,19),(20,29),(30,39),(40,49),(50,59),(60,79)]
            DEFAULT_LABELS = ["10代","20代","30代","40代","50代","60代以上"]

            age_kw_default = kws[0] if kws else ""
            age_keyword = st.text_input(
                "年代別分析するキーワード",
                value=age_kw_default,
                placeholder="例: サブスクリプションサービス",
                key="age_kw",
            )

            use_custom = st.checkbox("年代グループをカスタマイズする", value=False, key="age_custom")
            if use_custom:
                num_groups = st.slider("グループ数", 2, 6, 4, key="age_num")
                ranges_custom, labels_custom = [], []
                cols_age = st.columns(num_groups)
                for i, c in enumerate(cols_age):
                    with c:
                        lbl = st.text_input(f"ラベル{i+1}", value=DEFAULT_LABELS[i], key=f"age_lbl_{i}")
                        mn  = st.number_input("最小年齢", value=DEFAULT_RANGES[i][0], min_value=0, max_value=99, key=f"age_mn_{i}")
                        mx  = st.number_input("最大年齢", value=DEFAULT_RANGES[i][1], min_value=1, max_value=99, key=f"age_mx_{i}")
                        labels_custom.append(lbl)
                        ranges_custom.append((int(mn), int(mx)))
                age_groups = [{"label": labels_custom[i], "min": ranges_custom[i][0], "max": ranges_custom[i][1]} for i in range(num_groups)]
            else:
                age_groups = [{"label": DEFAULT_LABELS[i], "min": DEFAULT_RANGES[i][0], "max": DEFAULT_RANGES[i][1]} for i in range(len(DEFAULT_LABELS))]
                st.markdown("**デフォルト設定：** " + "　".join(DEFAULT_LABELS))

            if st.button("年代別 AI 分析を実行", key="btn_age"):
                if not age_keyword:
                    st.warning("キーワードを入力してください。")
                elif not api_key:
                    st.error("サイドバーに API キーを入力してください。")
                else:
                    with st.spinner("AIが各年代を分析中...（10〜20秒ほどかかります）"):
                        try:
                            from openai import OpenAI as _OpenAI
                            age_labels_str = "・".join([g["label"] for g in age_groups])
                            age_prompt = f"""
あなたはマーケティングデータアナリストです。
以下のキーワードについて、指定された年代別に詳細な分析を行ってください。

キーワード: 「{age_keyword}」
分析対象の年代: {age_labels_str}

各年代について、以下の情報をJSON形式で返してください。
JSON以外のテキストは一切出力しないでください。

{{
  "age_groups": [
    {{
      "label": "年代ラベル",
      "interest": 0から100の整数,
      "purchase_rate": 0から100の整数,
      "appeal_points": ["訴求ポイント1", "訴求ポイント2", "訴求ポイント3"],
      "risks": ["リスク1", "リスク2"],
      "channels": ["チャネル1", "チャネル2", "チャネル3"],
      "summary": "この年代の特徴を2〜3文で要約"
    }}
  ],
  "overall_insight": "全年代を横断した総合インサイトを3〜4文で記述"
}}
"""
                            _oa   = _OpenAI(api_key=api_key)
                            _resp = _oa.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role":"user","content":age_prompt}],
                                temperature=0.4, max_tokens=2000,
                            )
                            raw_age    = _resp.choices[0].message.content.strip()
                            json_match = re.search(r"\{.*\}", raw_age, re.DOTALL)
                            if not json_match:
                                st.error("AIの応答からJSONを取得できませんでした。もう一度お試しください。")
                            else:
                                result_age = json.loads(json_match.group())
                                st.session_state["age_result"]  = result_age
                                st.session_state["age_kw_used"] = age_keyword
                        except json.JSONDecodeError:
                            st.error("AIの応答のパースに失敗しました。もう一度お試しください。")
                        except Exception as e:
                            st.error(f"エラーが発生しました: {e}")

            if "age_result" in st.session_state:
                result_age   = st.session_state["age_result"]
                age_kw_used  = st.session_state.get("age_kw_used", "")
                age_grp_list = result_age.get("age_groups", [])

                if age_grp_list:
                    labels_plot   = [g["label"]               for g in age_grp_list]
                    interest_vals = [g.get("interest", 0)     for g in age_grp_list]
                    purchase_vals = [g.get("purchase_rate", 0) for g in age_grp_list]

                    fig_age = go.Figure()
                    fig_age.add_trace(go.Bar(name="関心度", x=labels_plot, y=interest_vals,
                        marker_color="#3b82f6", text=interest_vals, textposition="outside"))
                    fig_age.add_trace(go.Bar(name="購買・利用意向", x=labels_plot, y=purchase_vals,
                        marker_color="#f97316", text=purchase_vals, textposition="outside"))
                    fig_age.update_layout(
                        title=dict(text=f"「{age_kw_used}」年代別 関心度 vs 購買意向", font=dict(size=14, color="#1e293b")),
                        barmode="group",
                        yaxis=dict(title="スコア（0-100）", range=[0, 115]),
                        height=380, plot_bgcolor="white", paper_bgcolor="white",
                        margin=dict(l=20, r=20, t=60, b=40),
                    )
                    st.plotly_chart(fig_age, use_container_width=True)

                    st.markdown("#### 年代別詳細")
                    num_cols  = min(len(age_grp_list), 3)
                    card_cols = st.columns(num_cols)
                    for i, grp in enumerate(age_grp_list):
                        with card_cols[i % num_cols]:
                            st.markdown(f"**{grp['label']}**")
                            st.progress(min(int(grp.get("interest",0)),100)/100, text=f"関心度: {grp.get('interest',0)}")
                            st.progress(min(int(grp.get("purchase_rate",0)),100)/100, text=f"購買意向: {grp.get('purchase_rate',0)}")
                            with st.expander("詳細を見る"):
                                st.markdown("**訴求ポイント**")
                                for p in grp.get("appeal_points",[]): st.markdown(f"- {p}")
                                st.markdown("**リスク**")
                                for r_item in grp.get("risks",[]): st.markdown(f"- {r_item}")
                                st.markdown("**効果的チャネル**")
                                for ch in grp.get("channels",[]): st.markdown(f"- {ch}")
                                st.markdown(f"**概要**  \n{grp.get('summary','')}")

                    st.markdown("#### 総合インサイト")
                    st.info(result_age.get("overall_insight", ""))


# =====================================
# タブ⑤：CSV分析
# =====================================
with tab_csv:
    st.markdown('<p class="section-title">CSV アップロード & AI 分析</p>', unsafe_allow_html=True)
    st.caption("Google Ads・SEO ツール・Excel など、どんな形式の CSV でも自動で読み込んで AI が分析します。")
    uploaded = st.file_uploader("CSV ファイルをアップロード", type=["csv"],
        help="UTF-8 または Shift-JIS（Excel 保存の CSV）に対応しています。")

    if uploaded is None:
        show_empty_state("📂","CSVファイルをアップロードしてください",
            "Google Ads・SEOツール・Excelなど形式を問わず分析できます。\nキーワード・CTR・CPC・CVR・CPAなどを自動で認識します。")
    else:
        try:
            try:
                df_raw = pd.read_csv(uploaded, encoding="utf-8")
            except UnicodeDecodeError:
                uploaded.seek(0)
                df_raw = pd.read_csv(uploaded, encoding="shift-jis")

            col_map = detect_columns(df_raw)
            df_prep = prepare_dataframe(df_raw, col_map)

            st.markdown('<p class="section-title">読み込んだデータ</p>', unsafe_allow_html=True)
            m1,m2,m3 = st.columns(3)
            m1.metric("総行数",   f"{len(df_raw)}行")
            m2.metric("総列数",   f"{len(df_raw.columns)}列")
            m3.metric("検出指標", f"{len(col_map)}項目")

            if col_map:
                chip_html = "".join(f'<span class="meta-chip">{k} → {v}</span>' for k,v in col_map.items())
                st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin:8px 0;">{chip_html}</div>', unsafe_allow_html=True)
            else:
                st.warning("標準的なマーケティング指標の列が検出できませんでした。")

            with st.expander("データプレビュー（先頭10行）", expanded=False):
                st.dataframe(df_raw.head(10), use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown('<p class="section-title">データの可視化</p>', unsafe_allow_html=True)
            chart_pairs = [
                ("ctr",   "CTR上位キーワード",       "#6366f1"),
                ("clicks","クリック数ランキング",     "#3b82f6"),
                ("cpc",   "CPC比較",                 "#f59e0b"),
                ("cvr",   "CVR比較",                 "#10b981"),
                ("cpa",   "CPA比較（低いほど優秀）",  "#ef4444"),
            ]
            shown = 0
            gc1 = gc2 = None
            for metric, title, color in chart_pairs:
                if metric in col_map and "keyword" in col_map:
                    top_df, _ = get_top_bottom_keywords(df_prep, col_map, metric=metric, top_n=10)
                    if not top_df.empty:
                        if shown % 2 == 0:
                            gc1, gc2 = st.columns(2)
                        col = gc1 if shown % 2 == 0 else gc2
                        with col:
                            st.plotly_chart(
                                make_csv_bar_chart(top_df, col_map["keyword"], col_map[metric], title, color),
                                use_container_width=True,
                            )
                        shown += 1
            if shown == 0:
                st.info("グラフを表示するにはキーワード列と数値列が必要です。")

            st.markdown("---")
            st.markdown('<p class="section-title">AI によるトレンド・改善点の自動抽出</p>', unsafe_allow_html=True)
            csv_industry = st.text_input("業種・ジャンル（任意）", placeholder="例：ECサイト / 不動産", key="csv_industry")
            csv_question = st.text_input("特に知りたいこと（任意）", placeholder="例：CVRが低いキーワードの原因を知りたい", key="csv_question")

            if not api_key:
                st.warning("サイドバーに API キーを入力すると、AI による分析ができます。")
            else:
                if st.button("AI で分析する", type="primary"):
                    with st.spinner("AIがCSVを分析中です..."):
                        try:
                            client    = get_client(api_key)
                            ai_result = analyze_csv_with_ai(client, df_prep, col_map,
                                industry=csv_industry, custom_question=csv_question)
                            st.session_state["csv_ai_result"] = ai_result
                        except Exception as e:
                            st.error(f"AI分析中にエラーが発生しました: {e}")

            if "csv_ai_result" in st.session_state:
                ai = st.session_state["csv_ai_result"]
                if ai.get("summary"):
                    st.markdown(f'<div class="advice-box" style="margin-top:8px;">総評：{ai["summary"]}</div>', unsafe_allow_html=True)
                st.markdown("---")
                r1,r2 = st.columns(2)
                with r1:
                    st.markdown('<div class="insight-card"><div class="insight-card-title">トレンド・傾向</div>', unsafe_allow_html=True)
                    for item in ai.get("trends",[]): st.markdown(f'<div class="insight-item"><span class="insight-icon">·</span>{item}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                with r2:
                    st.markdown('<div class="insight-card"><div class="insight-card-title">課題・問題点</div>', unsafe_allow_html=True)
                    for item in ai.get("issues",[]): st.markdown(f'<div class="insight-item"><span class="insight-icon">·</span>{item}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('<div class="insight-card"><div class="insight-card-title">改善提案</div>', unsafe_allow_html=True)
                for item in ai.get("improvements",[]): st.markdown(f'<div class="insight-item"><span class="insight-icon">·</span>{item}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                r3,r4 = st.columns(2)
                medals = ["🥇","🥈","🥉"]
                with r3:
                    st.markdown('<div class="insight-card"><div class="insight-card-title">ターゲティング最適化</div>', unsafe_allow_html=True)
                    for item in ai.get("targeting",[]): st.markdown(f'<div class="insight-item"><span class="insight-icon">·</span>{item}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                with r4:
                    st.markdown('<div class="insight-card"><div class="insight-card-title">今すぐやるべきアクション</div>', unsafe_allow_html=True)
                    for i,item in enumerate(ai.get("next_actions",[])):
                        icon = medals[i] if i < 3 else "▶️"
                        st.markdown(f'<div class="insight-item"><span class="insight-icon">{icon}</span>{item}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                if ai.get("top_keywords"):
                    st.markdown('<p class="section-title">注目キーワード</p>', unsafe_allow_html=True)
                    kw_cols = st.columns(min(len(ai["top_keywords"]),3))
                    for i,kw in enumerate(ai["top_keywords"]):
                        with kw_cols[i%3]:
                            st.markdown(
                                f'<div class="top-kw-card">'
                                f'<div class="top-kw-name">{kw.get("keyword","")}</div>'
                                f'<div class="top-kw-reason">{kw.get("reason","")}</div>'
                                f'<div class="top-kw-action">→ {kw.get("action","")}</div>'
                                f'</div>', unsafe_allow_html=True)
                if "keyword" in col_map:
                    st.markdown("---")
                    st.markdown('<p class="section-title">キーワード分析へ連携</p>', unsafe_allow_html=True)
                    kw_list_csv = df_raw[col_map["keyword"]].dropna().astype(str).str.strip().unique().tolist()
                    selected_kws = st.multiselect("分析するキーワードを選択（最大20件）",
                        options=kw_list_csv[:50], default=kw_list_csv[:5])
                    if st.button("選択したキーワードをキーワード分析タブへ送る"):
                        st.session_state["csv_keywords"] = "\n".join(selected_kws[:20])
                        st.success("「キーワード分析」タブを開いてキーワード欄を確認してください。")
                st.markdown("---")
                ai_json = json.dumps(ai,ensure_ascii=False,indent=2).encode("utf-8")
                st.download_button("AI 分析結果を JSON でダウンロード",data=ai_json,
                    file_name=f"csv_analysis_{datetime.datetime.now(JST).strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json")

        except Exception as e:
            st.error(f"CSVの読み込みに失敗しました: {e}")
            st.info("ファイルの文字コードがUTF-8またはShift-JISであることを確認してください。")


# =====================================
# タブ⑥：分析履歴
# =====================================

# =====================================
# タブ⑥：文章要約・整形
# =====================================
with tab_summary:
    st.markdown('<p class="section-title">文章要約・整形</p>', unsafe_allow_html=True)
    st.caption("社内資料・報告書などの文章を AI が読みやすく要約・整形します。テキスト入力または PDF / Word ファイルのアップロードに対応しています。")

    if not api_key:
        st.warning("サイドバーに API キーを入力してください。")

    # ── 入力方法の選択 ──
    input_method = st.radio(
        "入力方法を選択",
        ["テキストを直接入力", "ファイルをアップロード（PDF / Word）"],
        horizontal=True,
        key="summary_input_method",
    )

    raw_text = ""

    if input_method == "テキストを直接入力":
        raw_text = st.text_area(
            "要約・整形したい文章を貼り付けてください",
            height=240,
            placeholder="ここに文章を入力してください...",
            key="summary_text_input",
        )

    else:
        uploaded_doc = st.file_uploader(
            "PDF または Word（.docx）ファイルをアップロード",
            type=["pdf", "docx"],
            key="summary_file_upload",
        )
        if uploaded_doc is not None:
            file_ext = uploaded_doc.name.split(".")[-1].lower()
            with st.spinner("ファイルを読み込み中..."):
                try:
                    if file_ext == "pdf":
                        import io
                        try:
                            import pypdf
                            reader = pypdf.PdfReader(io.BytesIO(uploaded_doc.read()))
                            raw_text = "\n".join(
                                page.extract_text() or "" for page in reader.pages
                            )
                        except ImportError:
                            try:
                                import PyPDF2
                                reader = PyPDF2.PdfReader(io.BytesIO(uploaded_doc.read()))
                                raw_text = "\n".join(
                                    page.extract_text() or "" for page in reader.pages
                                )
                            except ImportError:
                                st.error("PDFの読み込みに pypdf が必要です。requirements.txt に pypdf を追加してください。")

                    elif file_ext == "docx":
                        import io
                        try:
                            import docx
                            doc_obj = docx.Document(io.BytesIO(uploaded_doc.read()))
                            raw_text = "\n".join(p.text for p in doc_obj.paragraphs if p.text.strip())
                        except ImportError:
                            st.error("Wordファイルの読み込みに python-docx が必要です。requirements.txt に python-docx を追加してください。")

                    if raw_text:
                        st.success(f"ファイル読み込み完了（{len(raw_text)}文字）")
                        with st.expander("読み込んだテキストを確認", expanded=False):
                            st.text(raw_text[:2000] + ("..." if len(raw_text) > 2000 else ""))
                    else:
                        st.warning("テキストを抽出できませんでした。別のファイルをお試しください。")

                except Exception as e:
                    st.error(f"ファイルの読み込みに失敗しました: {e}")

    st.markdown("---")

    # ── 要約設定 ──
    st.markdown("#### 要約設定")
    col_s1, col_s2 = st.columns(2)

    with col_s1:
        summary_style = st.selectbox(
            "出力スタイル",
            options=[
                "箇条書きで要点整理",
                "短い要約文（3〜5行）",
                "見出し付きの構造化サマリー",
                "資料向け整形文章",
            ],
            key="summary_style",
        )

    with col_s2:
        summary_length = st.select_slider(
            "要約の長さ",
            options=["短め（150字程度）", "標準（300字程度）", "詳細（500字程度）", "詳しく（800字程度）"],
            value="標準（300字程度）",
            key="summary_length",
        )

    length_map = {
        "短め（150字程度）":  "150字程度",
        "標準（300字程度）":  "300字程度",
        "詳細（500字程度）":  "500字程度",
        "詳しく（800字程度）": "800字程度",
    }
    length_tokens_map = {
        "短め（150字程度）":  400,
        "標準（300字程度）":  700,
        "詳細（500字程度）":  1000,
        "詳しく（800字程度）": 1500,
    }

    # ── 実行ボタン ──
    run_summary = st.button("要約・整形を実行", type="primary", key="btn_summary")

    if run_summary:
        if not api_key:
            st.error("サイドバーに API キーを入力してください。")
        elif not raw_text.strip():
            st.warning("文章を入力またはファイルをアップロードしてください。")
        else:
            # 文字数が多すぎる場合は先頭8000文字に制限
            text_to_summarize = raw_text.strip()
            if len(text_to_summarize) > 8000:
                text_to_summarize = text_to_summarize[:8000]
                st.info("文章が長いため、先頭8000文字を対象に要約します。")

            length_str = length_map[summary_length]
            max_tok    = length_tokens_map[summary_length]

            style_prompts = {
                "箇条書きで要点整理": f"""
以下の文章を箇条書きで要点を整理してください。
- 重要なポイントを5〜10個の箇条書きにまとめてください
- 各項目は1〜2文で簡潔に記述してください
- 合計{length_str}を目安にしてください
- 日本語で出力してください
""",
                "短い要約文（3〜5行）": f"""
以下の文章を短い要約文にまとめてください。
- 3〜5行の簡潔な要約文を作成してください
- 最も重要な内容を優先して記述してください
- {length_str}を目安にしてください
- 日本語で自然な文章として出力してください
""",
                "見出し付きの構造化サマリー": f"""
以下の文章を見出し付きの構造化サマリーにまとめてください。
- 2〜4つのセクションに分け、各セクションに見出しをつけてください
- 各セクションの内容を2〜3文で記述してください
- 全体で{length_str}を目安にしてください
- 日本語で出力し、見出しは【】で囲んでください
""",
                "資料向け整形文章": f"""
以下の文章を、社内資料や報告書にそのまま使える整形された文章にまとめてください。
- 読みやすく、論理的な構成で書き直してください
- 冗長な表現を省き、簡潔で明確な表現に整えてください
- 全体で{length_str}を目安にしてください
- 敬語・丁寧語を使用し、ビジネス文書として適切なトーンにしてください
""",
            }

            prompt = f"""{style_prompts[summary_style]}

【対象文章】
{text_to_summarize}
"""
            with st.spinner("AIが要約・整形中...（数秒かかります）"):
                try:
                    from openai import OpenAI as _OA
                    _client = _OA(api_key=api_key)
                    _resp   = _client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "あなたは日本語文章の要約・整形の専門家です。指示に従い、正確で読みやすい出力を生成してください。"},
                            {"role": "user",   "content": prompt},
                        ],
                        temperature=0.3,
                        max_tokens=max_tok,
                    )
                    summary_result = _resp.choices[0].message.content.strip()
                    st.session_state["summary_result"] = summary_result
                    st.session_state["summary_style_used"]  = summary_style
                    st.session_state["summary_length_used"] = summary_length

                except Exception as e:
                    st.error(f"要約中にエラーが発生しました: {e}")

    # ── 結果表示 ──
    if "summary_result" in st.session_state:
        st.markdown("---")
        st.markdown("#### 要約・整形結果")

        style_used  = st.session_state.get("summary_style_used", "")
        length_used = st.session_state.get("summary_length_used", "")

        col_badge1, col_badge2 = st.columns([1, 3])
        with col_badge1:
            st.markdown(f'<span class="meta-chip">{style_used}</span>', unsafe_allow_html=True)
        with col_badge2:
            st.markdown(f'<span class="meta-chip">📏 {length_used}</span>', unsafe_allow_html=True)

        result_text = st.session_state["summary_result"]

        st.markdown(
            f'''<div style="background:white;border:1px solid #e0e7ff;border-left:4px solid #6366f1;
            border-radius:12px;padding:24px 28px;margin:12px 0;
            font-size:14px;line-height:1.9;color:#1e293b;
            box-shadow:0 2px 12px rgba(99,102,241,0.08);">
            {result_text.replace(chr(10), "<br>")}
            </div>''',
            unsafe_allow_html=True,
        )

        # ── ダウンロードボタン ──
        st.markdown("#### 結果をダウンロード")
        now_str = datetime.datetime.now(JST).strftime("%Y%m%d_%H%M%S")

        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                "TXT でダウンロード",
                data=result_text.encode("utf-8"),
                file_name=f"summary_{now_str}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with dl_col2:
            html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>要約・整形結果</title>
<style>
  body {{ font-family: 'Hiragino Sans', 'Yu Gothic UI', sans-serif; max-width:800px; margin:40px auto; padding:0 20px; color:#1e293b; line-height:1.9; }}
  h1   {{ font-size:20px; color:#6366f1; border-bottom:2px solid #6366f1; padding-bottom:8px; }}
  .meta {{ font-size:12px; color:#64748b; margin-bottom:24px; }}
  .content {{ background:#fafafe; border:1px solid #e0e7ff; border-left:4px solid #6366f1; border-radius:8px; padding:24px; white-space:pre-wrap; font-size:14px; }}
</style>
</head>
<body>
<h1>要約・整形結果</h1>
<div class="meta">スタイル: {style_used}　|　長さ: {length_used}　|　作成日時: {datetime.datetime.now(JST).strftime("%Y-%m-%d %H:%M")} (JST)</div>
<div class="content">{result_text}</div>
</body>
</html>"""
            st.download_button(
                "HTML でダウンロード",
                data=html_content.encode("utf-8"),
                file_name=f"summary_{now_str}.html",
                mime="text/html",
                use_container_width=True,
            )

        # ── 再実行ボタン ──
        if st.button("別のスタイルで再実行", key="btn_summary_retry"):
            del st.session_state["summary_result"]
            st.rerun()


# =====================================
# タブ⑦：ダイジェスト＆プレゼン作成
# =====================================
with tab_digest:
    st.markdown('<p class="section-title">ダイジェスト & プレゼン資料作成</p>', unsafe_allow_html=True)
    st.caption("複数の資料（PDF・Word・テキスト）を読み込み、AI がダイジェスト化して PowerPoint・Excel に変換します。")

    if not api_key:
        st.warning("サイドバーに API キーを入力してください。")

    # ── ファイルアップロード ──
    st.markdown("#### ファイルをアップロード")
    st.caption("PDF・Word（.docx）・テキスト（.txt）に対応。複数ファイルを同時にアップロードできます。")

    uploaded_files = st.file_uploader(
        "資料ファイルをアップロード（複数可）",
        type=["pdf", "docx", "txt", "text", "md"],
        accept_multiple_files=True,
        key="digest_files",
    )

    with st.expander("テキストを直接追加する（任意）", expanded=False):
        extra_text = st.text_area(
            "追加テキスト（ファイルと合わせて分析されます）",
            height=150,
            placeholder="議事録・メモなどをここに貼り付けてください...",
            key="digest_extra_text",
        )

    st.markdown("---")

    # ── 設定 ──
    st.markdown("#### プレゼン設定")
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        num_slides = st.slider("スライド枚数（タイトル・まとめ含む）", 4, 15, 8, key="digest_slides")
    with col_d2:
        detail_level = st.select_slider(
            "要約の詳しさ",
            options=["簡潔", "標準", "詳細"],
            value="標準",
            key="digest_detail",
        )
    with col_d3:
        output_format = st.radio(
            "出力形式",
            ["PowerPoint（.pptx）", "Excel（.xlsx）", "両方"],
            key="digest_format",
        )

    pptx_title = st.text_input(
        "プレゼンタイトル（空白の場合はAIが自動生成）",
        placeholder="例：2024年度 第3四半期 市場動向レポート",
        key="digest_title",
    )

    # ── 実行ボタン ──
    run_digest = st.button("ダイジェスト & 資料作成を開始", type="primary", key="btn_digest")

    if run_digest:
        if not api_key:
            st.error("サイドバーに API キーを入力してください。")
        elif not uploaded_files and not extra_text.strip():
            st.warning("ファイルをアップロードするか、テキストを入力してください。")
        else:
            from digest_creator import extract_text_from_file, generate_digest, create_pptx, create_xlsx

            # ── テキスト抽出 ──
            texts = {}
            errors = []

            with st.spinner("ファイルを読み込み中..."):
                for f in uploaded_files:
                    text, err = extract_text_from_file(f)
                    if err:
                        errors.append(err)
                    elif text:
                        texts[f.name] = text

                if extra_text.strip():
                    texts["直接入力テキスト"] = extra_text.strip()

            if errors:
                for err in errors:
                    st.error(err)

            if not texts:
                st.error("テキストを抽出できたファイルがありません。")
            else:
                # 読み込み結果を表示
                st.success(f"{len(texts)}件の資料を読み込みました。")
                with st.expander("読み込んだ資料の確認", expanded=False):
                    for fname, text in texts.items():
                        st.markdown(f"**{fname}**（{len(text):,}文字）")
                        st.text(text[:300] + ("..." if len(text) > 300 else ""))
                        st.markdown("---")

                # ── AI ダイジェスト生成 ──
                with st.spinner("AIが複数資料を横断してダイジェスト化中...（20〜40秒かかります）"):
                    digest = generate_digest(
                        texts=texts,
                        api_key=api_key,
                        num_slides=num_slides,
                        detail_level=detail_level,
                    )

                if "error" in digest:
                    st.error(f"ダイジェスト生成エラー: {digest['error']}")
                else:
                    # タイトルを上書き
                    if pptx_title.strip():
                        digest["title"] = pptx_title.strip()

                    st.session_state["digest_result"] = digest
                    st.session_state["digest_texts"]  = texts
                    st.success("ダイジェスト生成完了！")

    # ── 結果表示 & ダウンロード ──
    if "digest_result" in st.session_state:
        digest = st.session_state["digest_result"]
        texts  = st.session_state.get("digest_texts", {})

        st.markdown("---")
        st.markdown("#### ダイジェスト概要")

        # 全体概要
        st.markdown(
            f'''<div style="background:white;border:1px solid #e0e7ff;border-left:4px solid #6366f1;
            border-radius:12px;padding:20px 24px;margin:8px 0;font-size:14px;
            line-height:1.8;color:#1e293b;">
            <b>全体概要</b><br><br>{digest.get("overview","").replace(chr(10),"<br>")}
            </div>''',
            unsafe_allow_html=True,
        )

        # スライド構成プレビュー
        st.markdown("#### スライド構成プレビュー")
        slides = digest.get("slides", [])
        cols_per_row = 3
        for row_start in range(0, len(slides), cols_per_row):
            row_slides = slides[row_start:row_start + cols_per_row]
            cols = st.columns(len(row_slides))
            for col, sd in zip(cols, row_slides):
                with col:
                    layout_icon = {"bullets": "[ ]", "two_col": "[ ][ ]", "big_number": "[N]", "summary": "[v]"}.get(sd.get("layout",""), "")
                    st.markdown(
                        f'''<div style="background:white;border:1px solid #e0e7ff;border-radius:10px;
                        padding:12px 14px;margin-bottom:8px;min-height:120px;">
                        <div style="font-size:11px;color:#6366f1;font-weight:700;margin-bottom:4px;">
                        スライド {sd["slide_num"]} {layout_icon}</div>
                        <div style="font-size:13px;font-weight:700;color:#1e293b;margin-bottom:8px;">
                        {sd.get("title","")}</div>
                        <div style="font-size:11px;color:#475569;">
                        {"<br>".join(f"▶ {b}" for b in sd.get("bullets",[])[:3])}</div>
                        </div>''',
                        unsafe_allow_html=True,
                    )

        st.markdown("---")
        st.markdown("#### ダウンロード")
        now_str = datetime.datetime.now(JST).strftime("%Y%m%d_%H%M%S")
        output_format = st.session_state.get("digest_format", "両方")

        dl_cols = st.columns(2)

        if output_format in ["PowerPoint（.pptx）", "両方"]:
            with st.spinner("PowerPointを生成中..."):
                try:
                    from digest_creator import create_pptx
                    pptx_bytes = create_pptx(digest)
                    with dl_cols[0]:
                        st.download_button(
                            "PowerPoint（.pptx）をダウンロード",
                            data=pptx_bytes,
                            file_name=f"digest_{now_str}.pptx",
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            use_container_width=True,
                            type="primary",
                        )
                except Exception as e:
                    st.error(f"PowerPoint生成エラー: {e}")

        if output_format in ["Excel（.xlsx）", "両方"]:
            with st.spinner("Excelを生成中..."):
                try:
                    from digest_creator import create_xlsx
                    xlsx_bytes = create_xlsx(digest, texts)
                    with dl_cols[1]:
                        st.download_button(
                            "Excel（.xlsx）をダウンロード",
                            data=xlsx_bytes,
                            file_name=f"digest_{now_str}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                        )
                except Exception as e:
                    st.error(f"Excel生成エラー: {e}")

        # ── やり直しボタン ──
        if st.button("別の設定で作り直す", key="btn_digest_retry"):
            del st.session_state["digest_result"]
            del st.session_state["digest_texts"]
            st.rerun()

with tab_history:
    st.markdown('<p class="section-title">分析履歴</p>', unsafe_allow_html=True)
    sessions = get_all_sessions()
    if not sessions:
        show_empty_state("🗄️","まだ分析履歴がありません",
            "「キーワード分析」タブで分析すると、結果が自動的に保存されます。")
    else:
        st.markdown(f"**保存済みセッション数：{len(sessions)}件**")
        st.markdown("---")
        for s in sessions:
            col_info,col_btn1,col_btn2 = st.columns([4,1,1])
            with col_info:
                memo_text = f"　{s['memo']}" if s.get("memo") else ""
                st.markdown(
                    f'<div class="history-card">'
                    f'<div><div class="history-date">{s["created_at"]}{memo_text}</div></div>'
                    f'<div class="history-count">{s["kw_count"]} キーワード</div>'
                    f'</div>', unsafe_allow_html=True)
            with col_btn1:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("表示",key=f"show_{s['id']}",use_container_width=True):
                    loaded = get_session_results(s["id"])
                    st.session_state["results"] = loaded
                    st.session_state["loaded_session_id"] = s["id"]
                    st.rerun()
            with col_btn2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("削除",key=f"del_{s['id']}",use_container_width=True):
                    delete_session(s["id"])
                    st.warning(f"セッション {s['id']} を削除しました。")
                    st.rerun()
        st.markdown("---")
        st.markdown('<p class="section-title">キーワード別 推移を確認</p>', unsafe_allow_html=True)
        all_kws = get_all_keywords()
        if all_kws:
            selected_kw = st.selectbox("推移を見たいキーワードを選択", options=all_kws)
            if selected_kw:
                history = get_keyword_history(selected_kw)
                if len(history) >= 2:
                    st.plotly_chart(make_history_line_chart(history,selected_kw), use_container_width=True)
                    diff = history[-1]["purchase_score"] - history[0]["purchase_score"]
                    if diff > 0:   st.success(f"初回分析から **+{diff}点** 上昇しています。")
                    elif diff < 0: st.warning(f"初回分析から **{diff}点** 下降しています。")
                    else:          st.info("スコアに変化はありません。")
                else:
                    st.info(f"「{selected_kw}」はまだ1回しか分析されていません。")
        else:
            st.info("保存済みのキーワードがありません。")
        st.markdown("---")
        st.markdown('<p class="section-title">全履歴サマリー</p>', unsafe_allow_html=True)
        stats = get_segment_stats()
        if stats:
            stat_rows = []
            for seg,data in stats.items():
                info = SEGMENT_INFO.get(seg,{})
                stat_rows.append({
                    "価格帯層":     f"{seg}",
                    "分析件数":     f"{data['count']}件",
                    "平均購買意欲": f"{data['avg_score']:.1f}/10",
                    "推奨戦略":     info.get("strategy",""),
                })
            st.dataframe(pd.DataFrame(stat_rows), use_container_width=True, hide_index=True)


# =====================================
# タブ⑦：使い方ガイド
# =====================================
with tab_guide:
    st.markdown('<p class="section-title">使い方ガイド</p>', unsafe_allow_html=True)
    st.markdown("""
### キーワード分析タブ
1行1つ・最大20件まで分析できます。業種を入力すると精度が上がります。

---

### トレンド分析タブ
Google Trends の実データで日本市場の検索ボリューム推移を分析します。

| できること | 説明 |
|-----------|------|
| 検索ボリューム推移 | 期間内の相対的な人気度を折れ線グラフで表示 |
| 都道府県別人気度 | どの地域で最も検索されているか棒グラフで表示 |
| 関連キーワード | 実際に一緒に検索されているワードを自動取得 |
| 最新ニュース | Google News から関連ニュースをリアルタイム取得 |
| AI 市場分析 | データをもとに AI が市場動向と広告戦略を提言 |
| トレンド予測 | 過去データから線形回帰で将来トレンドを予測 |
| ヒートマップ | 曜日×時間帯の検索アクティビティを可視化 |
| 年代別分析 | AI が各年代の関心度・購買意向を分析 |

**コツ：同じキーワードを定期的に取得すると市場の変化を追えます**

---

### CSV 分析タブ
CSV をアップロードするだけで AI が自動分析します。

---

### 文章要約・整形タブ
社内資料・報告書などを AI が自動で要約・整形します。

| できること | 説明 |
|-----------|------|
| テキスト直接入力 | 文章を貼り付けてすぐ要約 |
| PDF/Word アップロード | ファイルから自動でテキスト抽出 |
| 4つの出力スタイル | 箇条書き・短い要約・構造化・資料向け整形 |
| 長さ調整 | 短め〜詳しくの4段階で調整可能 |
| TXT/HTML ダウンロード | 結果をそのまま資料に活用 |

**コツ：「資料向け整形文章」スタイルはそのまま報告書に貼り付けられます**

---

### 価格帯別の広告戦略

| 価格帯 | 主な訴求軸 | キーワード例 |
|--------|-----------|-------------|
| Budget | コスパ・割引・最安値 | 格安・安い・お得 |
| Standard | 機能・信頼性・実績 | おすすめ・人気・比較 |
| Premium | 品質・体験・専門性 | 高品質・こだわり・プロ |
| Luxury | ブランド・希少性・限定 | 高級・限定・ブランド |
""")
