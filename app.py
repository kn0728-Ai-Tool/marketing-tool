# app.py  v2.7
# 追加機能：トレンド分析タブ（時系列・ヒートマップ・ランキング・ジャンル比較・AIサマリー）
 
import streamlit as st
import pandas as pd
import datetime
import json
import time
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
    page_title="🎯 AIキーワード分析ツール",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)
 
st.markdown("""
<style>
html, body, [class*="css"] {
  font-family: 'Hiragino Sans', 'Yu Gothic UI', 'Meiryo', sans-serif;
}
.hero-banner {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%);
  border-radius: 16px; padding: 36px 40px; margin-bottom: 28px;
  color: white; position: relative; overflow: hidden;
}
.hero-banner::before {
  content: ''; position: absolute; top: -40px; right: -40px;
  width: 200px; height: 200px; background: rgba(255,255,255,0.08); border-radius: 50%;
}
.hero-title { font-size:28px; font-weight:800; margin:0 0 8px; }
.hero-sub   { font-size:14px; opacity:0.85; margin:0; line-height:1.6; }
.hero-badge {
  display:inline-block; background:rgba(255,255,255,0.2);
  border:1px solid rgba(255,255,255,0.3); border-radius:20px;
  padding:3px 12px; font-size:12px; margin-bottom:12px;
}
.stTabs [data-baseweb="tab-list"] { gap:8px; border-bottom:2px solid #e2e8f0; }
.stTabs [data-baseweb="tab"] {
  border-radius:8px 8px 0 0; padding:10px 20px; font-weight:600;
  font-size:14px; color:#64748b; background:#f1f5f9;
  border:1px solid #e2e8f0; border-bottom:none;
}
.stTabs [aria-selected="true"] { background:white !important; color:#6366f1 !important; }
[data-testid="metric-container"] {
  background:white; border:1px solid #e8eaf0; border-radius:12px;
  padding:16px 20px; box-shadow:0 2px 8px rgba(0,0,0,0.05); transition:transform 0.2s;
}
[data-testid="metric-container"]:hover {
  transform:translateY(-2px); box-shadow:0 4px 16px rgba(0,0,0,0.10);
}
.badge { display:inline-block; padding:4px 14px; border-radius:20px; font-size:12px; font-weight:700; }
.badge-budget   { background:#d1fae5; color:#065f46; }
.badge-standard { background:#dbeafe; color:#1e40af; }
.badge-premium  { background:#ede9fe; color:#5b21b6; }
.badge-luxury   { background:#1f2937; color:#f9fafb; }
.kw-card {
  background:white; border-radius:16px; padding:24px; margin-bottom:16px;
  border:1px solid #e8eaf0; box-shadow:0 2px 12px rgba(0,0,0,0.06); transition:box-shadow 0.2s;
}
.kw-card:hover { box-shadow:0 6px 24px rgba(99,102,241,0.12); border-color:#c7d2fe; }
.kw-title  { font-size:18px; font-weight:700; color:#1e293b; margin-bottom:12px; }
.kw-meta   { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:16px; align-items:center; }
.meta-chip { background:#f1f5f9; border-radius:8px; padding:4px 10px; font-size:12px; color:#475569; }
.score-wrap  { margin:12px 0; }
.score-label { font-size:12px; color:#64748b; margin-bottom:4px; display:flex; justify-content:space-between; }
.score-bg    { background:#e2e8f0; border-radius:99px; height:8px; overflow:hidden; }
.score-fill  { height:8px; border-radius:99px; }
.ad-card {
  background:#fafafe; border:1px solid #e0e7ff; border-top:3px solid #6366f1;
  border-radius:10px; padding:14px 16px; position:relative; margin-bottom:8px;
}
.ad-num        { position:absolute; top:10px; right:12px; font-size:11px; color:#a5b4fc; font-weight:700; }
.ad-title-text { font-size:14px; font-weight:700; color:#3730a3; margin-bottom:6px; line-height:1.4; }
.ad-desc-text  { font-size:12px; color:#4b5563; line-height:1.6; }
.ad-appeal     { margin-top:8px; font-size:11px; color:#6366f1; font-weight:600; }
.advice-box {
  background:linear-gradient(135deg,#fffbeb,#fef3c7); border:1px solid #fcd34d;
  border-left:4px solid #f59e0b; border-radius:10px; padding:12px 16px;
  font-size:13px; color:#78350f; margin-top:12px; line-height:1.6;
}
.lp-advice-box {
  background:#f0fdf4; border:1px solid #86efac; border-left:4px solid #22c55e;
  border-radius:10px; padding:10px 16px; font-size:13px; color:#14532d; margin:6px 0;
}
.insight-card {
  background:white; border-radius:12px; padding:16px 20px; margin-bottom:12px;
  border:1px solid #e8eaf0; box-shadow:0 2px 8px rgba(0,0,0,0.05);
}
.insight-card-title { font-size:14px; font-weight:700; color:#1e293b; margin-bottom:10px; }
.insight-item {
  display:flex; align-items:flex-start; gap:8px;
  padding:8px 0; border-bottom:1px solid #f1f5f9; font-size:13px; color:#334155;
}
.insight-item:last-child { border-bottom:none; }
.insight-icon { font-size:16px; flex-shrink:0; margin-top:1px; }
.top-kw-card {
  background:#fafafe; border:1px solid #e0e7ff; border-left:4px solid #6366f1;
  border-radius:10px; padding:14px 16px; margin-bottom:10px;
}
.top-kw-name   { font-size:15px; font-weight:700; color:#3730a3; margin-bottom:4px; }
.top-kw-reason { font-size:12px; color:#475569; margin-bottom:4px; }
.top-kw-action { font-size:12px; color:#065f46; font-weight:600; }
.history-card {
  background:white; border-radius:12px; padding:16px 20px; margin-bottom:10px;
  border:1px solid #e8eaf0; box-shadow:0 2px 8px rgba(0,0,0,0.04);
  display:flex; justify-content:space-between; align-items:center;
}
.history-date  { font-size:13px; color:#64748b; }
.history-count { font-size:13px; font-weight:600; color:#6366f1; }
/* トレンド専用 */
.trend-badge-up   { background:#d1fae5; color:#065f46; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:700; }
.trend-badge-flat { background:#fef3c7; color:#92400e; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:700; }
.trend-badge-down { background:#fee2e2; color:#991b1b; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:700; }
.trend-insight-box {
  background:linear-gradient(135deg,#eff6ff,#dbeafe); border:1px solid #93c5fd;
  border-left:4px solid #3b82f6; border-radius:12px; padding:16px 20px;
  font-size:14px; color:#1e40af; margin:12px 0; line-height:1.7;
}
.genre-card {
  background:white; border-radius:12px; padding:16px 20px; margin-bottom:10px;
  border:1px solid #e8eaf0; box-shadow:0 2px 8px rgba(0,0,0,0.05);
  display:flex; justify-content:space-between; align-items:center;
}
.section-title {
  font-size:18px; font-weight:700; color:#1e293b;
  margin:32px 0 16px; padding-left:12px; border-left:4px solid #6366f1;
}
.empty-state {
  background:#f8fafc; border:2px dashed #c7d2fe; border-radius:16px; padding:48px; text-align:center;
}
.empty-state-icon  { font-size:48px; margin-bottom:12px; }
.empty-state-title { font-size:16px; font-weight:700; color:#6366f1; margin-bottom:8px; }
.empty-state-desc  { font-size:13px; color:#64748b; }
[data-testid="stSidebar"] { background:#1e293b !important; }
[data-testid="stSidebar"] * { color:#e2e8f0 !important; }
[data-testid="stSidebar"] .stTextInput input {
  background:#334155 !important; border:1px solid #475569 !important;
  color:#f1f5f9 !important; border-radius:8px;
}
@media (max-width: 768px) {
  .hero-title { font-size:20px; }
  .hero-banner { padding:24px 20px; }
}
</style>
""", unsafe_allow_html=True)
 
# =====================================
# 定数
# =====================================
SEGMENT_INFO = {
    "Budget":   {"badge":"badge-budget",   "emoji":"💚","label":"Budget（コスパ重視）",  "color":"#10b981","strategy":"コスパ訴求・割引訴求・最安値強調"},
    "Standard": {"badge":"badge-standard", "emoji":"💙","label":"Standard（標準層）",    "color":"#3b82f6","strategy":"機能・信頼性・バランス訴求"},
    "Premium":  {"badge":"badge-premium",  "emoji":"💜","label":"Premium（品質重視）",   "color":"#8b5cf6","strategy":"品質・体験・専門性訴求"},
    "Luxury":   {"badge":"badge-luxury",   "emoji":"🖤","label":"Luxury（高級志向）",    "color":"#1f2937","strategy":"ブランド・希少性・ステータス訴求"},
}
INTENT_EMOJI = {
    "比較検討段階":"🔍","購買直前":"🛒","情報収集":"📚","価格調査":"💰",
}
TREND_BADGE = {
    "上昇": '<span class="trend-badge-up">📈 上昇</span>',
    "横ばい": '<span class="trend-badge-flat">➡️ 横ばい</span>',
    "下降": '<span class="trend-badge-down">📉 下降</span>',
}
 
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
        title=dict(text="📈 購買意欲スコア比較", font=dict(size=15,color="#1e293b")),
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
        title=dict(text="🎯 価格帯別 分布",font=dict(size=15,color="#1e293b")),
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
        title=dict(text="🔍 検索意図別 件数",font=dict(size=15,color="#1e293b")),
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
        title=dict(text=f"📈 「{keyword}」の購買意欲推移",font=dict(size=14,color="#1e293b")),
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
 
 
# =====================================
# トレンド用グラフ生成関数
# =====================================
def make_trend_line_chart(trend_data: list, genre: str) -> go.Figure:
    """キーワード別の購買意欲スコア時系列グラフ"""
    df = pd.DataFrame(trend_data)
    if df.empty:
        return go.Figure()
 
    fig = go.Figure()
    keywords = df["keyword"].unique()
    colors_list = ["#6366f1","#10b981","#f59e0b","#ef4444","#8b5cf6",
                   "#3b82f6","#ec4899","#14b8a6","#f97316","#84cc16"]
 
    for i, kw in enumerate(keywords):
        kw_df = df[df["keyword"] == kw].sort_values("session_date")
        color = colors_list[i % len(colors_list)]
        fig.add_trace(go.Scatter(
            x=kw_df["session_date"],
            y=kw_df["purchase_score"],
            mode="lines+markers",
            name=kw[:15],
            line=dict(color=color, width=2),
            marker=dict(size=8, color=color),
            hovertemplate=f"<b>{kw}</b><br>%{{x}}<br>購買意欲: %{{y}}/10<extra></extra>",
        ))
 
    fig.update_layout(
        title=dict(text=f"📈 【{genre}】キーワード別 購買意欲スコア推移",
                   font=dict(size=15,color="#1e293b")),
        xaxis=dict(title="分析日時"),
        yaxis=dict(title="購買意欲スコア", range=[0,11], dtick=1),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20,r=20,t=60,b=40),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
    fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
    return fig
 
 
def make_heatmap_chart(trend_data: list, genre: str) -> go.Figure:
    """ジャンル×キーワードの購買意欲ヒートマップ"""
    df = pd.DataFrame(trend_data)
    if df.empty:
        return go.Figure()
 
    # 最新セッションのデータだけ使ってピボット
    latest = df.sort_values("session_date").groupby("keyword").last().reset_index()
    pivot  = latest[["keyword","purchase_score"]].set_index("keyword")
 
    fig = go.Figure(go.Heatmap(
        z=pivot["purchase_score"].values.reshape(1, -1),
        x=pivot.index.tolist(),
        y=[genre],
        colorscale=[
            [0.0,  "#fee2e2"],
            [0.3,  "#fef3c7"],
            [0.6,  "#d1fae5"],
            [1.0,  "#065f46"],
        ],
        zmin=0, zmax=10,
        text=pivot["purchase_score"].values.reshape(1, -1),
        texttemplate="%{text}",
        textfont=dict(size=14, color="white"),
        hovertemplate="<b>%{x}</b><br>購買意欲スコア: %{z}/10<extra></extra>",
        colorbar=dict(title="購買意欲", tickvals=[0,2,4,6,8,10]),
    ))
    fig.update_layout(
        title=dict(text=f"🗺️ 【{genre}】購買意欲ヒートマップ（最新）",
                   font=dict(size=15,color="#1e293b")),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20,r=20,t=60,b=80),
        height=220,
        xaxis=dict(tickangle=-30),
    )
    return fig
 
 
def make_ranking_chart(trend_data: list, genre: str) -> go.Figure:
    """カテゴリ内キーワードランキング棒グラフ"""
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
        x=latest["purchase_score"],
        y=latest["keyword"].str[:15],
        orientation="h",
        marker=dict(color=score_colors),
        text=latest["purchase_score"],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>購買意欲: %{x}/10<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=f"🏆 【{genre}】キーワードランキング",
                   font=dict(size=15,color="#1e293b")),
        xaxis=dict(range=[0,11], title="購買意欲スコア"),
        yaxis=dict(title=""),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20,r=60,t=60,b=30),
        height=max(300, len(latest)*44),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=True,gridcolor="#f1f5f9")
    fig.update_yaxes(showgrid=False)
    return fig
 
 
def make_genre_compare_chart(genre_scores: list) -> go.Figure:
    """ジャンル比較棒グラフ"""
    if not genre_scores:
        return go.Figure()
 
    genres = [g["genre"] for g in genre_scores]
    scores = [round(g["avg_score"], 1) for g in genre_scores]
    counts = [g["session_count"] for g in genre_scores]
 
    bar_colors = [
        "#10b981" if s >= 7 else "#f59e0b" if s >= 4 else "#ef4444"
        for s in scores
    ]
 
    fig = go.Figure(go.Bar(
        x=genres,
        y=scores,
        marker=dict(color=bar_colors),
        text=[f"{s}点" for s in scores],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>平均購買意欲: %{y}/10<br>分析回数: " +
                      "<br>".join([f"{c}回" for c in counts]) + "<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="🌐 ジャンル別 平均購買意欲スコア比較",
                   font=dict(size=15,color="#1e293b")),
        xaxis=dict(title="ジャンル"),
        yaxis=dict(range=[0,11], title="平均購買意欲スコア"),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20,r=20,t=60,b=60),
        height=360,
        showlegend=False,
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
            f'<div style="font-size:13px;font-weight:600;color:#475569;margin:16px 0 8px;">📣 広告文案（3パターン）</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        ad_cols = st.columns(3)
        for i, ad in enumerate(r.get("ad_copies",[])[:3]):
            with ad_cols[i]:
                title_text   = ad.get("title","")
                desc_text    = ad.get("description","")
                appeal_point = ad.get("appeal_point","")
                appeal_html  = f'<div class="ad-appeal">✨ {appeal_point}</div>' if appeal_point else ""
                st.markdown(
                    f'<div class="ad-card"><div class="ad-num">案{i+1}</div>'
                    f'<div class="ad-title-text">{title_text}</div>'
                    f'<div class="ad-desc-text">{desc_text}</div>'
                    f'{appeal_html}</div>',
                    unsafe_allow_html=True,
                )
                with st.expander("📋 コピー", expanded=False):
                    st.code(f"【タイトル】{title_text}\n【説明文】{desc_text}", language=None)
 
        chips = ""
        if emotion:    chips += f'<span class="meta-chip">😊 感情: {emotion}</span>'
        if competitor: chips += f'<span class="meta-chip">⚔️ 差別化: {competitor}</span>'
        if cta:        chips += f'<span class="meta-chip">🖱️ CTA案: {cta}</span>'
        if chips:
            st.markdown(f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin:8px 0;">{chips}</div>', unsafe_allow_html=True)
        if lp_advice:
            st.markdown(f'<div class="lp-advice-box">🖥️ LP改善提案：{lp_advice}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="advice-box">💡 アドバイス：{r.get("advice","")}</div><br>', unsafe_allow_html=True)
 
 
# =====================================
# サイドバー
# =====================================
with st.sidebar:
    st.markdown("### 🎯 AI分析ツール")
    st.markdown("---")
    if not api_key:
        st.markdown("**🔑 APIキー設定**")
        api_key = st.text_input("OpenAI APIキー", type="password",
            placeholder="sk-proj-...", label_visibility="collapsed")
    else:
        st.markdown("**🔑 APIキー**")
        st.success("設定済み ✅")
    st.markdown("---")
    st.markdown("**📋 使い方**")
    st.markdown("1. キーワード入力 or CSV アップロード\n2. 「分析開始」をクリック\n3. トレンド分析でジャンル推移を確認\n4. レポートをダウンロード")
    st.markdown("---")
    st.markdown("**💡 価格帯の目安**")
    for seg, info in SEGMENT_INFO.items():
        st.markdown(f"{info['emoji']} **{seg}**  \n{info['strategy']}\n")
    st.markdown("---")
    st.caption("v2.7 | Powered by OpenAI")
 
 
# =====================================
# ヒーローバナー
# =====================================
st.markdown("""
<div class="hero-banner">
  <div class="hero-badge">✨ AI Powered Marketing Tool</div>
  <div class="hero-title">🎯 AIキーワード分析ツール</div>
  <div class="hero-sub">
    キーワード入力 or CSVアップロードで、トレンド・改善点・広告文案をAIが自動生成。<br>
    ジャンル別トレンド分析で市場の流れをひと目で把握できます。
  </div>
</div>
""", unsafe_allow_html=True)
 
 
# =====================================
# タブ定義
# =====================================
tab_analyze, tab_result, tab_chart, tab_trend, tab_csv, tab_history, tab_guide = st.tabs([
    "🔍 キーワード分析",
    "📝 分析結果",
    "📊 グラフ分析",
    "📈 トレンド分析",
    "📂 CSV分析",
    "🗄️ 分析履歴",
    "📖 使い方ガイド",
])
 
 
# =====================================
# タブ①：キーワード分析
# =====================================
with tab_analyze:
    col_input, col_btn = st.columns([3,1])
    with col_input:
        default_kw = st.session_state.pop("csv_keywords", "")
        keywords_input = st.text_area(
            "🔑 分析したいキーワードを入力（1行に1つ・最大20件）",
            value=default_kw, height=180,
            placeholder="格安スマホ 乗り換え おすすめ\niPhone 最新 購入\nスマホ 高級 おすすめ",
        )
    with col_btn:
        st.markdown("<br>"*3, unsafe_allow_html=True)
        run_button = st.button("🚀 分析開始", use_container_width=True, type="primary")
        kw_list  = [k.strip() for k in keywords_input.strip().splitlines() if k.strip()]
        st.info(f"入力数：**{len(kw_list)}件**")
        memo     = st.text_input("📝 メモ（任意）", placeholder="例：競合調査 2024年6月")
        industry = st.text_input("🏢 業種・ジャンル（任意）", placeholder="例：スマートフォン / 不動産")
 
    if run_button:
        if not api_key:
            st.error("⚠️ サイドバーにAPIキーを入力してください。")
        elif not kw_list:
            st.warning("⚠️ キーワードを1つ以上入力してください。")
        else:
            if len(kw_list) > 20:
                st.warning("⚠️ 最初の20件を分析します。")
                kw_list = kw_list[:20]
            client   = get_client(api_key)
            results  = []
            progress = st.progress(0)
            status   = st.empty()
            for i, kw in enumerate(kw_list):
                status.markdown(f"⏳ 分析中... **{kw}** ({i+1}/{len(kw_list)})")
                progress.progress((i+1)/len(kw_list))
                try:
                    data = analyze_keyword_structured(client, kw, industry=industry)
                    results.append(data)
                except Exception as e:
                    results.append({"keyword":kw,"error":str(e)})
                time.sleep(0.5)
            progress.empty()
            session_id = save_session(results, memo=memo)
            status.success(f"✅ {len(kw_list)}件の分析完了！（セッションID: {session_id}）")
            st.session_state["results"] = results
 
 
# =====================================
# タブ②：分析結果
# =====================================
with tab_result:
    if "results" not in st.session_state:
        show_empty_state("📝","まだ分析結果がありません",
            "「🔍 キーワード分析」タブでキーワードを入力して分析してください。")
    else:
        results = st.session_state["results"]
        valid   = [r for r in results if "error" not in r]
        if not valid:
            st.error("有効な分析結果がありません。")
        else:
            st.markdown('<p class="section-title">📊 分析サマリー</p>', unsafe_allow_html=True)
            seg_counts = {s:0 for s in SEGMENT_INFO}
            for r in valid:
                seg = r.get("price_segment","")
                if seg in seg_counts: seg_counts[seg]+=1
            avg_score = sum(r.get("purchase_score",0) for r in valid)/len(valid)
            c1,c2,c3,c4,c5,c6 = st.columns(6)
            c1.metric("分析件数",     f"{len(valid)}件")
            c2.metric("平均購買意欲", f"{avg_score:.1f}/10")
            c3.metric("💚 Budget",   f"{seg_counts['Budget']}件")
            c4.metric("💙 Standard", f"{seg_counts['Standard']}件")
            c5.metric("💜 Premium",  f"{seg_counts['Premium']}件")
            c6.metric("🖤 Luxury",   f"{seg_counts['Luxury']}件")
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
            st.markdown('<p class="section-title">📝 キーワード別 詳細分析</p>', unsafe_allow_html=True)
            render_keyword_cards(filtered)
            st.markdown("---")
            st.markdown('<p class="section-title">📋 一覧比較表</p>', unsafe_allow_html=True)
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
            st.markdown('<p class="section-title">💾 データ保存</p>', unsafe_allow_html=True)
            now        = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_data   = df.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig")
            json_data  = json.dumps(results,ensure_ascii=False,indent=2).encode("utf-8")
            html_report = generate_html_report(results=filtered, title="AIキーワード分析レポート",
                memo=f"分析件数: {len(filtered)}件")
            html_data  = html_report.encode("utf-8")
            dl1,dl2,dl3 = st.columns(3)
            with dl1:
                st.download_button("📥 CSVでダウンロード",data=csv_data,
                    file_name=f"keyword_analysis_{now}.csv",mime="text/csv",use_container_width=True)
            with dl2:
                st.download_button("📥 JSONでダウンロード",data=json_data,
                    file_name=f"keyword_analysis_{now}.json",mime="application/json",use_container_width=True)
            with dl3:
                st.download_button("📄 HTMLレポートをダウンロード",data=html_data,
                    file_name=f"report_{now}.html",mime="text/html",use_container_width=True)
            st.markdown("---")
            st.markdown('<p class="section-title">👁️ レポートプレビュー</p>', unsafe_allow_html=True)
            st.caption("ダウンロードしたHTMLをブラウザで開いて Ctrl+P → 「PDFとして保存」でPDF化できます。")
            with st.expander("レポートのプレビューを表示", expanded=False):
                st.components.v1.html(html_report, height=600, scrolling=True)
 
 
# =====================================
# タブ③：グラフ分析
# =====================================
with tab_chart:
    if "results" not in st.session_state:
        show_empty_state("📊","まだ分析結果がありません",
            "「🔍 キーワード分析」タブでキーワードを入力して分析してください。")
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
            st.markdown('<p class="section-title">📊 グラフ分析</p>', unsafe_allow_html=True)
            st.plotly_chart(make_score_bar_chart(valid), use_container_width=True)
            st.markdown("---")
            g1,g2 = st.columns(2)
            with g1: st.plotly_chart(make_segment_pie_chart(seg_counts), use_container_width=True)
            with g2: st.plotly_chart(make_intent_bar_chart(valid), use_container_width=True)
            st.markdown("---")
            st.markdown('<p class="section-title">💡 グラフの読み方</p>', unsafe_allow_html=True)
            st.markdown("""
| グラフ | 見るべきポイント |
|--------|----------------|
| 📈 購買意欲スコア | 8点以上は入札単価を上げる価値あり |
| 🎯 価格帯別分布 | 多い層の広告文を優先的に強化する |
| 🔍 検索意図別件数 | 「購買直前」が多ければ直接訴求が有効 |
""")
 
 
# =====================================
# タブ④：トレンド分析（新規）
# =====================================
with tab_trend:
    st.markdown('<p class="section-title">📈 ジャンル・カテゴリ別 トレンド分析</p>', unsafe_allow_html=True)
    st.caption("ジャンルとキーワードを入力して分析するたびにデータが蓄積され、時系列でトレンドが見えてきます。")
 
    # ---- 入力エリア ----
    col_genre, col_kws = st.columns([1, 2])
    with col_genre:
        trend_genre = st.text_input(
            "🏷️ ジャンル・カテゴリ名",
            placeholder="例：スマートフォン",
            help="同じジャンル名で繰り返し分析するとトレンドグラフが育ちます",
        )
        trend_industry = st.text_input(
            "🏢 業種（任意）",
            placeholder="例：EC / 不動産 / SaaS",
            key="trend_industry",
        )
    with col_kws:
        trend_keywords_input = st.text_area(
            "🔑 キーワードを入力（1行に1つ・最大10件）",
            height=130,
            placeholder="格安スマホ 乗り換え\niPhone 購入\nスマホ 高級\nSIMフリー おすすめ",
        )
 
    trend_kw_list = [k.strip() for k in trend_keywords_input.strip().splitlines() if k.strip()]
    col_info, col_run = st.columns([3,1])
    with col_info:
        st.caption(f"ジャンル: **{trend_genre or '未入力'}**　キーワード数: **{len(trend_kw_list)}件**")
    with col_run:
        trend_run = st.button("📈 トレンド分析開始", type="primary", use_container_width=True)
 
    if trend_run:
        if not api_key:
            st.error("⚠️ サイドバーにAPIキーを入力してください。")
        elif not trend_genre:
            st.warning("⚠️ ジャンル・カテゴリ名を入力してください。")
        elif not trend_kw_list:
            st.warning("⚠️ キーワードを1つ以上入力してください。")
        else:
            if len(trend_kw_list) > 10:
                st.warning("⚠️ 最初の10件を分析します。")
                trend_kw_list = trend_kw_list[:10]
            with st.spinner(f"「{trend_genre}」のトレンドを分析中..."):
                try:
                    client     = get_client(api_key)
                    trend_result = analyze_trend_keywords(client, trend_genre, trend_kw_list)
                    session_id = save_trend_session(trend_genre, trend_result)
                    st.session_state["trend_result"] = trend_result
                    st.session_state["trend_genre"]  = trend_genre
                    st.success(f"✅ 「{trend_genre}」の分析完了！DBに保存しました（ID: {session_id}）")
                except Exception as e:
                    st.error(f"分析中にエラーが発生しました: {e}")
 
    st.markdown("---")
 
    # ---- 最新分析結果の表示 ----
    if "trend_result" in st.session_state:
        tr     = st.session_state["trend_result"]
        tgenre = st.session_state.get("trend_genre","")
 
        # ジャンルサマリー
        trend_label = TREND_BADGE.get(tr.get("genre_trend",""), "")
        st.markdown(
            f'<div class="trend-insight-box">'
            f'<div style="font-size:16px;font-weight:800;margin-bottom:8px;">'
            f'📊 {tgenre} &nbsp; {trend_label} &nbsp;'
            f'<span style="font-size:22px;color:#3b82f6;">平均スコア {tr.get("genre_avg_score",0)}/10</span>'
            f'</div>'
            f'<div>{tr.get("genre_summary","")}</div>'
            f'<div style="margin-top:10px;font-weight:700;">🤖 AIインサイト：{tr.get("ai_insight","")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
 
        # 注目キーワード
        top_kw     = tr.get("top_keyword","")
        rising_kw  = tr.get("rising_keyword","")
        if top_kw or rising_kw:
            hc1,hc2 = st.columns(2)
            with hc1:
                st.markdown(
                    f'<div class="insight-card">'
                    f'<div class="insight-card-title">🏆 最も購買意欲が高いキーワード</div>'
                    f'<div style="font-size:20px;font-weight:800;color:#6366f1;">{top_kw}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with hc2:
                st.markdown(
                    f'<div class="insight-card">'
                    f'<div class="insight-card-title">🚀 最も上昇トレンドのキーワード</div>'
                    f'<div style="font-size:20px;font-weight:800;color:#10b981;">{rising_kw}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
 
        # キーワード一覧テーブル
        st.markdown('<p class="section-title">📋 キーワード別 分析結果</p>', unsafe_allow_html=True)
        kw_rows = []
        for kw in tr.get("keywords",[]):
            trend_val = kw.get("trend","")
            badge     = TREND_BADGE.get(trend_val, trend_val)
            kw_rows.append({
                "キーワード":   kw.get("keyword",""),
                "購買意欲":     kw.get("purchase_score",""),
                "検索意図":     kw.get("search_intent",""),
                "価格帯":       kw.get("price_segment",""),
                "トレンド":     trend_val,
                "トレンド理由": kw.get("trend_reason",""),
            })
        kw_df = pd.DataFrame(kw_rows)
        st.dataframe(kw_df, use_container_width=True, hide_index=True)
 
    st.markdown("---")
 
    # ---- 保存済みジャンルの選択と時系列グラフ ----
    st.markdown('<p class="section-title">📊 ジャンル別 時系列グラフ</p>', unsafe_allow_html=True)
    all_genres = get_all_genres()
 
    if not all_genres:
        show_empty_state("📈","まだトレンドデータがありません",
            "上のフォームでジャンルとキーワードを入力して「トレンド分析開始」を押してください。\n同じジャンルを繰り返し分析するとグラフが育ちます。")
    else:
        selected_genre = st.selectbox(
            "表示するジャンルを選択",
            options=all_genres,
            help="同じジャンルで複数回分析すると時系列グラフが表示されます",
        )
 
        if selected_genre:
            trend_data = get_trend_keywords_by_genre(selected_genre)
 
            if trend_data:
                # 時系列グラフ
                st.plotly_chart(
                    make_trend_line_chart(trend_data, selected_genre),
                    use_container_width=True,
                )
                st.markdown("---")
 
                # ヒートマップ＋ランキング
                hm1, hm2 = st.columns([2,1])
                with hm1:
                    st.plotly_chart(
                        make_heatmap_chart(trend_data, selected_genre),
                        use_container_width=True,
                    )
                with hm2:
                    st.plotly_chart(
                        make_ranking_chart(trend_data, selected_genre),
                        use_container_width=True,
                    )
            else:
                st.info(f"「{selected_genre}」のトレンドデータがまだありません。")
 
    st.markdown("---")
 
    # ---- ジャンル比較グラフ ----
    st.markdown('<p class="section-title">🌐 ジャンル比較グラフ</p>', unsafe_allow_html=True)
    genre_scores = get_genre_avg_scores()
 
    if len(genre_scores) >= 2:
        st.plotly_chart(
            make_genre_compare_chart(genre_scores),
            use_container_width=True,
        )
        st.caption("🟢 7点以上: 購買意欲高　🟡 4〜6点: 普通　🔴 3点以下: 低め")
    elif len(genre_scores) == 1:
        st.info("ジャンルが1つだけです。2つ以上のジャンルを分析するとここに比較グラフが表示されます。")
    else:
        st.info("まだジャンルデータがありません。トレンド分析を実行してください。")
 
    # ---- 分析履歴一覧 ----
    st.markdown("---")
    st.markdown('<p class="section-title">🗄️ トレンド分析履歴</p>', unsafe_allow_html=True)
    trend_sessions = get_trend_sessions()
    if trend_sessions:
        hist_rows = []
        for s in trend_sessions:
            hist_rows.append({
                "分析日時":       s.get("created_at",""),
                "ジャンル":       s.get("genre",""),
                "キーワード数":   f"{s.get('kw_count',0)}件",
                "平均スコア":     f"{s.get('avg_score',0):.1f}/10",
                "ジャンルトレンド": s.get("genre_trend",""),
                "AIインサイト":   s.get("ai_insight",""),
            })
        st.dataframe(pd.DataFrame(hist_rows), use_container_width=True, hide_index=True)
    else:
        st.info("まだトレンド分析履歴がありません。")
 
 
# =====================================
# タブ⑤：CSV分析
# =====================================
with tab_csv:
    st.markdown('<p class="section-title">📂 CSVアップロード＆AI分析</p>', unsafe_allow_html=True)
    st.caption("Google Ads・SEOツール・Excelなど、どんな形式のCSVでも自動で読み込んでAIが分析します。")
 
    uploaded = st.file_uploader("CSVファイルをアップロード", type=["csv"],
        help="UTF-8またはShift-JIS（Excel保存のCSV）に対応しています。")
 
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
 
            st.markdown('<p class="section-title">📋 読み込んだデータ</p>', unsafe_allow_html=True)
            m1,m2,m3 = st.columns(3)
            m1.metric("総行数",   f"{len(df_raw)}行")
            m2.metric("総列数",   f"{len(df_raw.columns)}列")
            m3.metric("検出指標", f"{len(col_map)}項目")
 
            if col_map:
                chip_html = "".join(f'<span class="meta-chip">✅ {k} → {v}</span>' for k,v in col_map.items())
                st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin:8px 0;">{chip_html}</div>', unsafe_allow_html=True)
            else:
                st.warning("標準的なマーケティング指標の列が検出できませんでした。")
 
            with st.expander("データプレビュー（先頭10行）", expanded=False):
                st.dataframe(df_raw.head(10), use_container_width=True, hide_index=True)
 
            st.markdown("---")
            st.markdown('<p class="section-title">📊 データの可視化</p>', unsafe_allow_html=True)
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
                                make_csv_bar_chart(top_df, col_map["keyword"], col_map[metric], f"📊 {title}", color),
                                use_container_width=True,
                            )
                        shown += 1
            if shown == 0:
                st.info("グラフを表示するにはキーワード列と数値列が必要です。")
 
            st.markdown("---")
            st.markdown('<p class="section-title">🤖 AIによるトレンド・改善点の自動抽出</p>', unsafe_allow_html=True)
            csv_industry = st.text_input("🏢 業種・ジャンル（任意）", placeholder="例：ECサイト / 不動産", key="csv_industry")
            csv_question = st.text_input("💬 特に知りたいこと（任意）", placeholder="例：CVRが低いキーワードの原因を知りたい", key="csv_question")
 
            if not api_key:
                st.warning("⚠️ サイドバーにAPIキーを入力すると、AIによる分析ができます。")
            else:
                if st.button("🤖 AIで分析する", type="primary"):
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
                    st.markdown(f'<div class="advice-box" style="margin-top:8px;">📋 総評：{ai["summary"]}</div>', unsafe_allow_html=True)
                st.markdown("---")
                r1,r2 = st.columns(2)
                with r1:
                    st.markdown('<div class="insight-card"><div class="insight-card-title">📈 トレンド・傾向</div>', unsafe_allow_html=True)
                    for item in ai.get("trends",[]): st.markdown(f'<div class="insight-item"><span class="insight-icon">📌</span>{item}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                with r2:
                    st.markdown('<div class="insight-card"><div class="insight-card-title">⚠️ 課題・問題点</div>', unsafe_allow_html=True)
                    for item in ai.get("issues",[]): st.markdown(f'<div class="insight-item"><span class="insight-icon">🔴</span>{item}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('<div class="insight-card"><div class="insight-card-title">💡 改善提案</div>', unsafe_allow_html=True)
                for item in ai.get("improvements",[]): st.markdown(f'<div class="insight-item"><span class="insight-icon">✅</span>{item}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                r3,r4 = st.columns(2)
                medals = ["🥇","🥈","🥉"]
                with r3:
                    st.markdown('<div class="insight-card"><div class="insight-card-title">🎯 ターゲティング最適化</div>', unsafe_allow_html=True)
                    for item in ai.get("targeting",[]): st.markdown(f'<div class="insight-item"><span class="insight-icon">🎯</span>{item}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                with r4:
                    st.markdown('<div class="insight-card"><div class="insight-card-title">🚀 今すぐやるべきアクション</div>', unsafe_allow_html=True)
                    for i,item in enumerate(ai.get("next_actions",[])):
                        icon = medals[i] if i < 3 else "▶️"
                        st.markdown(f'<div class="insight-item"><span class="insight-icon">{icon}</span>{item}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                if ai.get("top_keywords"):
                    st.markdown('<p class="section-title">⭐ 注目キーワード</p>', unsafe_allow_html=True)
                    kw_cols = st.columns(min(len(ai["top_keywords"]),3))
                    for i,kw in enumerate(ai["top_keywords"]):
                        with kw_cols[i%3]:
                            st.markdown(
                                f'<div class="top-kw-card">'
                                f'<div class="top-kw-name">🔍 {kw.get("keyword","")}</div>'
                                f'<div class="top-kw-reason">{kw.get("reason","")}</div>'
                                f'<div class="top-kw-action">→ {kw.get("action","")}</div>'
                                f'</div>', unsafe_allow_html=True)
                if "keyword" in col_map:
                    st.markdown("---")
                    st.markdown('<p class="section-title">🔗 キーワード分析へ連携</p>', unsafe_allow_html=True)
                    kw_list_csv = df_raw[col_map["keyword"]].dropna().astype(str).str.strip().unique().tolist()
                    selected_kws = st.multiselect("分析するキーワードを選択（最大20件）",
                        options=kw_list_csv[:50], default=kw_list_csv[:5])
                    if st.button("📤 選択したキーワードを分析タブへ送る"):
                        st.session_state["csv_keywords"] = "\n".join(selected_kws[:20])
                        st.success("✅ 「🔍 キーワード分析」タブを開いてキーワード欄を確認してください。")
                st.markdown("---")
                ai_json = json.dumps(ai,ensure_ascii=False,indent=2).encode("utf-8")
                st.download_button("📥 AI分析結果をJSONでダウンロード",data=ai_json,
                    file_name=f"csv_analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json")
 
        except Exception as e:
            st.error(f"CSVの読み込みに失敗しました: {e}")
            st.info("ファイルの文字コードがUTF-8またはShift-JISであることを確認してください。")
 
 
# =====================================
# タブ⑥：分析履歴
# =====================================
with tab_history:
    st.markdown('<p class="section-title">🗄️ 分析履歴</p>', unsafe_allow_html=True)
    sessions = get_all_sessions()
    if not sessions:
        show_empty_state("🗄️","まだ分析履歴がありません",
            "「🔍 キーワード分析」タブで分析すると、結果が自動的に保存されます。")
    else:
        st.markdown(f"**保存済みセッション数：{len(sessions)}件**")
        st.markdown("---")
        for s in sessions:
            col_info,col_btn1,col_btn2 = st.columns([4,1,1])
            with col_info:
                memo_text = f"　📝 {s['memo']}" if s.get("memo") else ""
                st.markdown(
                    f'<div class="history-card">'
                    f'<div><div class="history-date">🕐 {s["created_at"]}{memo_text}</div></div>'
                    f'<div class="history-count">📊 {s["kw_count"]}件のキーワード</div>'
                    f'</div>', unsafe_allow_html=True)
            with col_btn1:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("📂 表示",key=f"show_{s['id']}",use_container_width=True):
                    loaded = get_session_results(s["id"])
                    st.session_state["results"] = loaded
                    st.success(f"セッション {s['id']} を読み込みました。「📝 分析結果」タブを確認してください。")
            with col_btn2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ 削除",key=f"del_{s['id']}",use_container_width=True):
                    delete_session(s["id"])
                    st.warning(f"セッション {s['id']} を削除しました。")
                    st.rerun()
        st.markdown("---")
        st.markdown('<p class="section-title">📈 キーワード別 推移を確認</p>', unsafe_allow_html=True)
        all_kws = get_all_keywords()
        if all_kws:
            selected_kw = st.selectbox("推移を見たいキーワードを選択", options=all_kws)
            if selected_kw:
                history = get_keyword_history(selected_kw)
                if len(history) >= 2:
                    st.plotly_chart(make_history_line_chart(history,selected_kw), use_container_width=True)
                    diff = history[-1]["purchase_score"] - history[0]["purchase_score"]
                    if diff > 0:   st.success(f"📈 初回分析から **+{diff}点** 上昇しています。")
                    elif diff < 0: st.warning(f"📉 初回分析から **{diff}点** 下降しています。")
                    else:          st.info("➡️ スコアに変化はありません。")
                else:
                    st.info(f"「{selected_kw}」はまだ1回しか分析されていません。")
        else:
            st.info("保存済みのキーワードがありません。")
        st.markdown("---")
        st.markdown('<p class="section-title">📊 全履歴サマリー</p>', unsafe_allow_html=True)
        stats = get_segment_stats()
        if stats:
            stat_rows = []
            for seg,data in stats.items():
                info = SEGMENT_INFO.get(seg,{})
                stat_rows.append({
                    "価格帯層":     f"{info.get('emoji','')} {seg}",
                    "分析件数":     f"{data['count']}件",
                    "平均購買意欲": f"{data['avg_score']:.1f}/10",
                    "推奨戦略":     info.get("strategy",""),
                })
            st.dataframe(pd.DataFrame(stat_rows), use_container_width=True, hide_index=True)
 
 
# =====================================
# タブ⑦：使い方ガイド
# =====================================
with tab_guide:
    st.markdown('<p class="section-title">📖 使い方ガイド</p>', unsafe_allow_html=True)
    st.markdown("""
### 🔍 キーワード分析タブ
1行1つ・最大20件まで分析できます。業種を入力すると精度が上がります。
 
---
 
### 📈 トレンド分析タブ（新機能）
ジャンル名とキーワードを入力して分析するたびにデータが蓄積されます。
 
| できること | 説明 |
|-----------|------|
| 時系列グラフ | 同じジャンルを繰り返し分析すると購買意欲の推移が折れ線で表示 |
| ヒートマップ | ジャンル×キーワードの購買意欲を色の濃さで一目で把握 |
| ランキング表 | カテゴリ内で購買意欲が高いキーワードを順位表示 |
| ジャンル比較 | 複数のジャンルを分析すると平均スコアを棒グラフで比較 |
| AIインサイト | ジャンル全体のトレンドと今すぐ取るべきアクションを自動生成 |
 
💡 **コツ：同じジャンル名で週次・月次に繰り返し分析するとトレンドグラフが育ちます**
 
---
 
### 📂 CSV分析タブ
CSVをアップロードするだけでAIが自動分析します。
 
---
 
### 💡 価格帯別の広告戦略
 
| 価格帯 | 主な訴求軸 | キーワード例 |
|--------|-----------|-------------|
| 💚 Budget | コスパ・割引・最安値 | 格安・安い・お得 |
| 💙 Standard | 機能・信頼性・実績 | おすすめ・人気・比較 |
| 💜 Premium | 品質・体験・専門性 | 高品質・こだわり・プロ |
| 🖤 Luxury | ブランド・希少性・限定 | 高級・限定・ブランド |
""")
 
