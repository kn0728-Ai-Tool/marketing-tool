# app.py  v2.2
# 追加機能：SQLite DB・分析履歴・キーワード推移

import streamlit as st
import pandas as pd
import datetime
import json
import time
import plotly.graph_objects as go
import plotly.express as px
from analyzer  import get_client, analyze_keyword_structured
from database  import (
    init_db, save_session,
    get_all_sessions, get_session_results,
    get_keyword_history, get_all_keywords,
    delete_session, get_segment_stats,
)

# =====================================
# DB初期化（アプリ起動時に毎回実行）
# =====================================
init_db()

# =====================================
# ページ設定
# =====================================
st.set_page_config(
    page_title="🎯 AIキーワード分析ツール",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================
# カスタムCSS
# =====================================
st.markdown("""
<style>
html, body, [class*="css"] {
  font-family: 'Hiragino Sans', 'Yu Gothic UI', 'Meiryo', sans-serif;
}
.hero-banner {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%);
  border-radius: 16px;
  padding: 36px 40px;
  margin-bottom: 28px;
  color: white;
  position: relative;
  overflow: hidden;
}
.hero-banner::before {
  content: '';
  position: absolute;
  top: -40px; right: -40px;
  width: 200px; height: 200px;
  background: rgba(255,255,255,0.08);
  border-radius: 50%;
}
.hero-title {
  font-size: 28px;
  font-weight: 800;
  margin: 0 0 8px;
}
.hero-sub {
  font-size: 14px;
  opacity: 0.85;
  margin: 0;
  line-height: 1.6;
}
.hero-badge {
  display: inline-block;
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 20px;
  padding: 3px 12px;
  font-size: 12px;
  margin-bottom: 12px;
}
.stTabs [data-baseweb="tab-list"] {
  gap: 8px;
  border-bottom: 2px solid #e2e8f0;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 8px 8px 0 0;
  padding: 10px 20px;
  font-weight: 600;
  font-size: 14px;
  color: #64748b;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-bottom: none;
}
.stTabs [aria-selected="true"] {
  background: white !important;
  color: #6366f1 !important;
}
[data-testid="metric-container"] {
  background: white;
  border: 1px solid #e8eaf0;
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  transition: transform 0.2s;
}
[data-testid="metric-container"]:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.10);
}
.badge { display:inline-block; padding:4px 14px; border-radius:20px; font-size:12px; font-weight:700; }
.badge-budget   { background:#d1fae5; color:#065f46; }
.badge-standard { background:#dbeafe; color:#1e40af; }
.badge-premium  { background:#ede9fe; color:#5b21b6; }
.badge-luxury   { background:#1f2937; color:#f9fafb; }
.kw-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 16px;
  border: 1px solid #e8eaf0;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  transition: box-shadow 0.2s;
}
.kw-card:hover {
  box-shadow: 0 6px 24px rgba(99,102,241,0.12);
  border-color: #c7d2fe;
}
.kw-title { font-size:18px; font-weight:700; color:#1e293b; margin-bottom:12px; }
.kw-meta  { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:16px; align-items:center; }
.meta-chip { background:#f1f5f9; border-radius:8px; padding:4px 10px; font-size:12px; color:#475569; }
.score-wrap { margin:12px 0; }
.score-label { font-size:12px; color:#64748b; margin-bottom:4px; display:flex; justify-content:space-between; }
.score-bg   { background:#e2e8f0; border-radius:99px; height:8px; overflow:hidden; }
.score-fill { height:8px; border-radius:99px; }
.ad-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.ad-card {
  background: #fafafe;
  border: 1px solid #e0e7ff;
  border-top: 3px solid #6366f1;
  border-radius: 10px;
  padding: 14px 16px;
  position: relative;
}
.ad-num { position:absolute; top:10px; right:12px; font-size:11px; color:#a5b4fc; font-weight:700; }
.ad-title-text { font-size:14px; font-weight:700; color:#3730a3; margin-bottom:6px; line-height:1.4; }
.ad-desc-text  { font-size:12px; color:#4b5563; line-height:1.6; }
.advice-box {
  background: linear-gradient(135deg, #fffbeb, #fef3c7);
  border: 1px solid #fcd34d;
  border-left: 4px solid #f59e0b;
  border-radius: 10px;
  padding: 12px 16px;
  font-size: 13px;
  color: #78350f;
  margin-top: 12px;
  line-height: 1.6;
}

/* 履歴カード */
.history-card {
  background: white;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 10px;
  border: 1px solid #e8eaf0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.history-date  { font-size:13px; color:#64748b; }
.history-count { font-size:13px; font-weight:600; color:#6366f1; }

.section-title {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin: 32px 0 16px;
  padding-left: 12px;
  border-left: 4px solid #6366f1;
}
[data-testid="stSidebar"] { background: #1e293b !important; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stTextInput input {
  background: #334155 !important;
  border: 1px solid #475569 !important;
  color: #f1f5f9 !important;
  border-radius: 8px;
}
@media (max-width: 768px) {
  .hero-title { font-size: 20px; }
  .hero-banner { padding: 24px 20px; }
  .ad-grid { grid-template-columns: 1fr; }
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

# =====================================
# APIキー
# =====================================
api_key = ""
if hasattr(st, "secrets"):
    api_key = st.secrets.get("OPENAI_API_KEY", "")

# =====================================
# グラフ生成関数
# =====================================
def make_score_bar_chart(valid):
    keywords = [r.get("keyword","")[:15] for r in valid]
    scores   = [r.get("purchase_score", 0) for r in valid]
    segs     = [r.get("price_segment","Standard") for r in valid]
    colors   = [SEGMENT_INFO.get(s, SEGMENT_INFO["Standard"])["color"] for s in segs]
    fig = go.Figure(go.Bar(
        x=scores, y=keywords, orientation="h",
        marker=dict(color=colors),
        text=[f"{s}点" for s in scores], textposition="outside",
        hovertemplate="<b>%{y}</b><br>購買意欲: %{x}/10<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="📈 購買意欲スコア比較", font=dict(size=15, color="#1e293b")),
