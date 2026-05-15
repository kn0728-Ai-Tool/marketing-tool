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
# 感情・競合・CTA の追加情報
        emotion     = r.get("emotion", "")
        competitor  = r.get("competitor_position", "")
        cta         = r.get("cta_suggestion", "")
        lp_advice   = r.get("lp_advice", "")

        if emotion or competitor or cta:
            st.markdown(f"""
<div style="display:flex;gap:8px;flex-wrap:wrap;margin:8px 0;">
  {"<span class='meta-chip'>😊 感情: " + emotion + "</span>" if emotion else ""}
  {"<span class='meta-chip'>⚔️ 差別化: " + competitor + "</span>" if competitor else ""}
  {"<span class='meta-chip'>🖱️ CTA案: " + cta + "</span>" if cta else ""}
</div>
""", unsafe_allow_html=True)

        if lp_advice:
            st.markdown(f"""
<div style="background:#f0fdf4;border:1px solid #86efac;border-left:4px solid #22c55e;
border-radius:10px;padding:10px 16px;font-size:13px;color:#14532d;margin:6px 0;">
  🖥️ LP改善提案：{lp_advice}
</div>
""", unsafe_allow_html=True)
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
        xaxis=dict(range=[0,11], title="購買意欲スコア"),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20,r=60,t=50,b=30),
        height=max(300, len(valid)*44),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
    fig.update_yaxes(showgrid=False)
    return fig

def make_segment_pie_chart(seg_counts):
    labels = [f"{SEGMENT_INFO[s]['emoji']} {s}" for s,c in seg_counts.items() if c>0]
    values = [c for c in seg_counts.values() if c>0]
    colors = [SEGMENT_INFO[s]["color"] for s,c in seg_counts.items() if c>0]
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker=dict(colors=colors, line=dict(color="white",width=2)),
        textinfo="label+percent", hole=0.45,
        hovertemplate="<b>%{label}</b><br>%{value}件<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="🎯 価格帯別 分布", font=dict(size=15,color="#1e293b")),
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
    labels = [f"{INTENT_EMOJI.get(k,'🔎')} {k}" for k in intent_counts]
    values = list(intent_counts.values())
    bar_colors = [colors_map.get(k,"#94a3b8") for k in intent_counts]
    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker=dict(color=bar_colors),
        text=values, textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y}件<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="🔍 検索意図別 件数", font=dict(size=15,color="#1e293b")),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20,r=20,t=50,b=30), height=300,
        showlegend=False,
    )
    fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9", dtick=1)
    fig.update_xaxes(showgrid=False)
    return fig

def make_history_line_chart(history: list, keyword: str):
    """キーワードの購買意欲推移グラフ"""
    dates  = [h.get("session_date","") for h in history]
    scores = [h.get("purchase_score", 0) for h in history]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=scores,
        mode="lines+markers+text",
        text=scores,
        textposition="top center",
        line=dict(color="#6366f1", width=3),
        marker=dict(size=10, color="#6366f1"),
        hovertemplate="<b>%{x}</b><br>スコア: %{y}/10<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=f"📈 「{keyword}」の購買意欲推移", font=dict(size=14,color="#1e293b")),
        xaxis=dict(title="分析日時"),
        yaxis=dict(title="購買意欲スコア", range=[0,11], dtick=1),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20,r=20,t=50,b=30), height=280,
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
    fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
    return fig

# =====================================
# キーワードカード表示（共通関数）
# =====================================
def render_keyword_cards(filtered: list):
    for r in filtered:
        seg    = r.get("price_segment", "Standard")
        info   = SEGMENT_INFO.get(seg, SEGMENT_INFO["Standard"])
        score  = r.get("purchase_score", 0)
        intent = r.get("search_intent", "")
        ie     = INTENT_EMOJI.get(intent, "🔎")

        # 追加項目
        emotion    = r.get("emotion", "")
        competitor = r.get("competitor_position", "")
        cta        = r.get("cta_suggestion", "")
        lp_advice  = r.get("lp_advice", "")

        # カードヘッダー
        st.markdown(
            f'<div class="kw-card">'
            f'<div class="kw-title">{info["emoji"]} {r["keyword"]}</div>'
            f'<div class="kw-meta">'
            f'<span class="badge {info["badge"]}">{info["label"]}</span>'
            f'<span class="meta-chip">{ie} {intent}</span>'
            f'<span class="meta-chip">意図: {r.get("intent_reason", "")}</span>'
            f'<span class="meta-chip">層の理由: {r.get("segment_reason", "")}</span>'
            f'</div>'
            f'<div class="score-wrap">'
            f'<div class="score-label">'
            f'<span>購買意欲スコア</span>'
            f'<span style="font-weight:700;color:{info["color"]};">{score} / 10</span>'
            f'</div>'
            f'<div class="score-bg">'
            f'<div class="score-fill" style="width:{score * 10}%;background:{info["color"]};"></div>'
            f'</div>'
            f'</div>'
            f'<div style="font-size:13px;font-weight:600;color:#475569;margin:16px 0 8px;">'
            f'📣 広告文案（3パターン）'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # 広告文カード（3列）
        ad_cols = st.columns(3)
        for i, ad in enumerate(r.get("ad_copies", [])[:3]):
            with ad_cols[i]:
                title_text   = ad.get("title", "")
                desc_text    = ad.get("description", "")
                appeal_point = ad.get("appeal_point", "")
                copy_text    = f"【タイトル】{title_text}\n【説明文】{desc_text}"

                st.markdown(
                    f'<div class="ad-card">'
                    f'<div class="ad-num">案{i + 1}</div>'
                    f'<div class="ad-title-text">{title_text}</div>'
                    f'<div class="ad-desc-text">{desc_text}</div>'
                    + (
                        f'<div style="margin-top:8px;font-size:11px;'
                        f'color:#6366f1;font-weight:600;">✨ {appeal_point}</div>'
                        if appeal_point else ""
                    )
                    + f'</div>',
                    unsafe_allow_html=True,
                )

                with st.expander("📋 コピー", expanded=False):
                    st.code(copy_text, language=None)

        # 感情・競合・CTA チップ
        chips = ""
        if emotion:
            chips += f'<span class="meta-chip">😊 感情: {emotion}</span>'
        if competitor:
            chips += f'<span class="meta-chip">⚔️ 差別化: {competitor}</span>'
        if cta:
            chips += f'<span class="meta-chip">🖱️ CTA案: {cta}</span>'

        if chips:
            st.markdown(
                f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin:8px 0;">'
                f'{chips}'
                f'</div>',
                unsafe_allow_html=True,
            )

        # LP改善提案
        if lp_advice:
            st.markdown(
                f'<div style="background:#f0fdf4;border:1px solid #86efac;'
                f'border-left:4px solid #22c55e;border-radius:10px;'
                f'padding:10px 16px;font-size:13px;color:#14532d;margin:6px 0;">'
                f'🖥️ LP改善提案：{lp_advice}'
                f'</div>',
                unsafe_allow_html=True,
            )

        # アドバイスボックス
        st.markdown(
            f'<div class="advice-box">'
            f'💡 アドバイス：{r.get("advice", "")}'
            f'</div><br>',
            unsafe_allow_html=True,
        )

        ad_cols = st.columns(3)
        for i, ad in enumerate(r.get("ad_copies",[])[:3]):
            with ad_cols[i]:
                title_text = ad.get("title","")
                desc_text  = ad.get("description","")
                st.markdown(f"""
<div class="ad-card">
  <div class="ad-num">案{i+1}</div>
  <div class="ad-title-text">{title_text}</div>
  <div class="ad-desc-text">{desc_text}</div>
</div>
""", unsafe_allow_html=True)
                with st.expander("📋 コピー", expanded=False):
                    st.code(f"【タイトル】{title_text}\n【説明文】{desc_text}", language=None)

        st.markdown(f"""
<div class="advice-box">💡 アドバイス：{r.get('advice','')}</div><br>
""", unsafe_allow_html=True)

# =====================================
# サイドバー
# =====================================
with st.sidebar:
    st.markdown("### 🎯 AI分析ツール")
    st.markdown("---")
    if not api_key:
        st.markdown("**🔑 APIキー設定**")
        api_key = st.text_input(
            "OpenAI APIキー", type="password",
            placeholder="sk-proj-...", label_visibility="collapsed",
        )
    else:
        st.markdown("**🔑 APIキー**")
        st.success("設定済み ✅")
    st.markdown("---")
    st.markdown("**📋 使い方**")
    st.markdown("1. キーワードを入力（1行1つ）\n2. 「分析開始」をクリック\n3. 結果・グラフを確認\n4. 履歴から過去データを参照")
    st.markdown("---")
    st.markdown("**💡 価格帯の目安**")
    for seg, info in SEGMENT_INFO.items():
        st.markdown(f"{info['emoji']} **{seg}**  \n{info['strategy']}\n")
    st.markdown("---")
    st.caption("v2.2 | Powered by OpenAI")

# =====================================
# ヒーローバナー
# =====================================
st.markdown("""
<div class="hero-banner">
  <div class="hero-badge">✨ AI Powered Marketing Tool</div>
  <div class="hero-title">🎯 AIキーワード分析ツール</div>
  <div class="hero-sub">
    キーワードを入力するだけで、検索意図・価格帯・購買意欲・広告文案を自動生成。<br>
    分析履歴をDBに保存して、キーワードの推移も追跡できます。
  </div>
</div>
""", unsafe_allow_html=True)

# =====================================
# タブ
# =====================================
tab_analyze, tab_result, tab_chart, tab_history, tab_guide = st.tabs([
    "🔍 キーワード分析",
    "📝 分析結果",
    "📊 グラフ分析",
    "🗄️ 分析履歴",
    "📖 使い方ガイド",
])

# =====================================
# タブ①：キーワード分析
# =====================================
with tab_analyze:
    col_input, col_btn = st.columns([3,1])
    with col_input:
        keywords_input = st.text_area(
            "🔑 分析したいキーワードを入力（1行に1つ・最大20件）",
            height=180,
            placeholder="格安スマホ 乗り換え おすすめ\niPhone 最新 購入\nスマホ 高級 おすすめ",
        )
    with col_btn:
        st.markdown("<br>"*3, unsafe_allow_html=True)
        run_button = st.button("🚀 分析開始", use_container_width=True, type="primary")
        kw_list = [k.strip() for k in keywords_input.strip().splitlines() if k.strip()]
        st.info(f"入力数：**{len(kw_list)}件**")
        memo = st.text_input("📝 メモ（任意）", placeholder="例：競合調査 2024年6月")
        industry = st.text_input(
            "🏢 業種・ジャンル（任意）",
            placeholder="例：スマートフォン / 不動産 / 飲食店 / コスメ",
            help="入力すると業種に合わせた分析になります",
        )

    if run_button:
        if not api_key:
            st.error("⚠️ サイドバーにAPIキーを入力してください。"); st.stop()
        if not kw_list:
            st.warning("⚠️ キーワードを1つ以上入力してください。"); st.stop()
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

        # DBに自動保存
        session_id = save_session(results, memo=memo)
        status.success(f"✅ {len(kw_list)}件の分析完了！DBに保存しました（セッションID: {session_id}）")
        st.session_state["results"] = results

# =====================================
# タブ②：分析結果
# =====================================
with tab_result:
    if "results" not in st.session_state:
        st.info("👈 「🔍 キーワード分析」タブで分析してください。"); st.stop()

    results = st.session_state["results"]
    valid   = [r for r in results if "error" not in r]
    if not valid:
        st.error("有効な分析結果がありません。"); st.stop()

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
        seg_filter = st.multiselect("価格帯", list(SEGMENT_INFO.keys()), default=list(SEGMENT_INFO.keys()))
    with f2:
        intent_opts = sorted(set(r.get("search_intent","") for r in valid if r.get("search_intent")))
        intent_filter = st.multiselect("検索意図", intent_opts, default=intent_opts)
    with f3:
        score_min = st.slider("購買意欲スコア（最小）", 1, 10, 1)

    filtered = [r for r in valid
        if r.get("price_segment") in seg_filter
        and r.get("search_intent") in intent_filter
        and r.get("purchase_score",0) >= score_min]
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
            "キーワード":r.get("keyword",""), "検索意図":r.get("search_intent",""),
            "価格帯層":r.get("price_segment",""), "購買意欲(1-10)":r.get("purchase_score",""),
            "広告タイトル案1":ad1.get("title",""), "広告説明文案1":ad1.get("description",""),
            "アドバイス":r.get("advice",""),
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown('<p class="section-title">💾 データ保存</p>', unsafe_allow_html=True)
    now       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_data  = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    json_data = json.dumps(results, ensure_ascii=False, indent=2).encode("utf-8")
    dl1,dl2 = st.columns(2)
    with dl1:
        st.download_button("📥 CSVでダウンロード", data=csv_data,
            file_name=f"keyword_analysis_{now}.csv", mime="text/csv", use_container_width=True)
    with dl2:
        st.download_button("📥 JSONでダウンロード", data=json_data,
            file_name=f"keyword_analysis_{now}.json", mime="application/json", use_container_width=True)

# =====================================
# タブ③：グラフ分析
# =====================================
with tab_chart:
    if "results" not in st.session_state:
        st.info("👈 「🔍 キーワード分析」タブで分析してください。"); st.stop()

    results = st.session_state["results"]
    valid   = [r for r in results if "error" not in r]
    if not valid:
        st.error("有効な分析結果がありません。"); st.stop()

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
# タブ④：分析履歴
# =====================================
with tab_history:
    st.markdown('<p class="section-title">🗄️ 分析履歴</p>', unsafe_allow_html=True)

    sessions = get_all_sessions()

    if not sessions:
        st.info("まだ分析履歴がありません。「🔍 キーワード分析」タブで分析してください。")
        st.stop()

    # ---- 全セッション一覧 ----
    st.markdown(f"**保存済みセッション数：{len(sessions)}件**")
    st.markdown("---")

    for s in sessions:
        col_info, col_btn1, col_btn2 = st.columns([4, 1, 1])

        with col_info:
            memo_text = f"　📝 {s['memo']}" if s.get("memo") else ""
            st.markdown(f"""
<div class="history-card">
  <div>
    <div class="history-date">🕐 {s['created_at']}{memo_text}</div>
  </div>
  <div class="history-count">📊 {s['kw_count']}件のキーワード</div>
</div>
""", unsafe_allow_html=True)

        with col_btn1:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📂 表示", key=f"show_{s['id']}", use_container_width=True):
                # このセッションの結果をセッションステートに読み込む
                loaded = get_session_results(s["id"])
                st.session_state["results"]         = loaded
                st.session_state["history_session"] = s
                st.success(f"セッション {s['id']} を読み込みました。「📝 分析結果」タブを確認してください。")

        with col_btn2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ 削除", key=f"del_{s['id']}", use_container_width=True):
                delete_session(s["id"])
                st.warning(f"セッション {s['id']} を削除しました。")
                st.rerun()

    st.markdown("---")

    # ---- キーワード推移 ----
    st.markdown('<p class="section-title">📈 キーワード別 推移を確認</p>', unsafe_allow_html=True)

    all_kws = get_all_keywords()
    if all_kws:
        selected_kw = st.selectbox(
            "推移を見たいキーワードを選択",
            options=all_kws,
            help="複数回分析されたキーワードの購買意欲スコアの推移を表示します"
        )
        if selected_kw:
            history = get_keyword_history(selected_kw)
            if len(history) >= 2:
                st.plotly_chart(
                    make_history_line_chart(history, selected_kw),
                    use_container_width=True,
                )
                # 推移の変化をコメント
                first_score = history[0]["purchase_score"]
                last_score  = history[-1]["purchase_score"]
                diff        = last_score - first_score
                if diff > 0:
                    st.success(f"📈 初回分析から **+{diff}点** 上昇しています。購買意欲が高まっています。")
                elif diff < 0:
                    st.warning(f"📉 初回分析から **{diff}点** 下降しています。訴求の見直しを検討してください。")
                else:
                    st.info("➡️ スコアに変化はありません。")
            else:
                st.info(f"「{selected_kw}」はまだ1回しか分析されていません。複数回分析するとここに推移グラフが表示されます。")
    else:
        st.info("保存済みのキーワードがありません。")

    st.markdown("---")

    # ---- 全履歴の集計stats ----
    st.markdown('<p class="section-title">📊 全履歴サマリー</p>', unsafe_allow_html=True)
    stats = get_segment_stats()
    if stats:
        stat_rows = []
        for seg, data in stats.items():
            info = SEGMENT_INFO.get(seg, {})
            stat_rows.append({
                "価格帯層":         f"{info.get('emoji','')} {seg}",
                "分析件数":         f"{data['count']}件",
                "平均購買意欲":     f"{data['avg_score']:.1f}/10",
                "推奨戦略":         info.get("strategy",""),
            })
        st.dataframe(pd.DataFrame(stat_rows), use_container_width=True, hide_index=True)

# =====================================
# タブ⑤：使い方ガイド
# =====================================
with tab_guide:
    st.markdown('<p class="section-title">📖 使い方ガイド</p>', unsafe_allow_html=True)
    st.markdown("""
### STEP 1　キーワードを入力する
1行1つ・最大20件まで分析できます。メモ欄に目的を記録しておくと履歴で見返しやすくなります。

---

### STEP 2　分析開始ボタンを押す
AIがキーワードごとに検索意図・価格帯・購買意欲・広告文案を自動生成します。
**結果はDBに自動保存されます。**

---

### STEP 3　グラフで傾向を把握する
「📊 グラフ分析」タブで購買意欲・価格帯分布・検索意図を視覚的に確認できます。

---

### STEP 4　履歴でキーワードの推移を追う
「🗄️ 分析履歴」タブで過去の分析を再表示したり、キーワードの購買意欲スコア推移を確認できます。

---

### 💡 価格帯別の広告戦略

| 価格帯 | 主な訴求軸 | キーワード例 |
|--------|-----------|-------------|
| 💚 Budget | コスパ・割引・最安値 | 格安・安い・お得 |
| 💙 Standard | 機能・信頼性・実績 | おすすめ・人気・比較 |
| 💜 Premium | 品質・体験・専門性 | 高品質・こだわり・プロ |
| 🖤 Luxury | ブランド・希少性・限定 | 高級・限定・ブランド |
""")
