# app.py  v2.1
# 追加機能：グラフ（棒・円）＋ コピーボタン

import streamlit as st
import pandas as pd
import datetime
import json
import time
import plotly.graph_objects as go
import plotly.express as px
from analyzer import get_client, analyze_keyword_structured

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

/* ヒーローバナー */
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
  letter-spacing: -0.5px;
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

/* タブ */
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

/* メトリクスカード */
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

/* バッジ */
.badge {
  display: inline-block;
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
}
.badge-budget   { background:#d1fae5; color:#065f46; }
.badge-standard { background:#dbeafe; color:#1e40af; }
.badge-premium  { background:#ede9fe; color:#5b21b6; }
.badge-luxury   { background:#1f2937; color:#f9fafb; }

/* キーワードカード */
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
.kw-title {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 12px;
}
.kw-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 16px;
  align-items: center;
}
.meta-chip {
  background: #f1f5f9;
  border-radius: 8px;
  padding: 4px 10px;
  font-size: 12px;
  color: #475569;
}

/* スコアバー */
.score-wrap { margin: 12px 0; }
.score-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
  display: flex;
  justify-content: space-between;
}
.score-bg {
  background: #e2e8f0;
  border-radius: 99px;
  height: 8px;
  overflow: hidden;
}
.score-fill {
  height: 8px;
  border-radius: 99px;
}

/* 広告文グリッド */
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
  padding: 14px 16px 48px;   /* 下にコピーボタン分のスペース */
  position: relative;
}
.ad-num {
  position: absolute;
  top: 10px; right: 12px;
  font-size: 11px;
  color: #a5b4fc;
  font-weight: 700;
}
.ad-title-text {
  font-size: 14px;
  font-weight: 700;
  color: #3730a3;
  margin-bottom: 6px;
  line-height: 1.4;
}
.ad-desc-text {
  font-size: 12px;
  color: #4b5563;
  line-height: 1.6;
}

/* コピーボタン */
.copy-btn-wrap {
  position: absolute;
  bottom: 10px; right: 10px;
}

/* アドバイスボックス */
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

/* グラフセクション */
.chart-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid #e8eaf0;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  margin-bottom: 16px;
}

/* セクション見出し */
.section-title {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin: 32px 0 16px;
  padding-left: 12px;
  border-left: 4px solid #6366f1;
}

/* サイドバー */
[data-testid="stSidebar"] {
  background: #1e293b !important;
}
[data-testid="stSidebar"] * {
  color: #e2e8f0 !important;
}
[data-testid="stSidebar"] .stTextInput input {
  background: #334155 !important;
  border: 1px solid #475569 !important;
  color: #f1f5f9 !important;
  border-radius: 8px;
}

/* スマホ対応 */
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
    "Budget": {
        "badge":    "badge-budget",
        "emoji":    "💚",
        "label":    "Budget（コスパ重視）",
        "color":    "#10b981",
        "strategy": "コスパ訴求・割引訴求・最安値強調",
    },
    "Standard": {
        "badge":    "badge-standard",
        "emoji":    "💙",
        "label":    "Standard（標準層）",
        "color":    "#3b82f6",
        "strategy": "機能・信頼性・バランス訴求",
    },
    "Premium": {
        "badge":    "badge-premium",
        "emoji":    "💜",
        "label":    "Premium（品質重視）",
        "color":    "#8b5cf6",
        "strategy": "品質・体験・専門性訴求",
    },
    "Luxury": {
        "badge":    "badge-luxury",
        "emoji":    "🖤",
        "label":    "Luxury（高級志向）",
        "color":    "#1f2937",
        "strategy": "ブランド・希少性・ステータス訴求",
    },
}

INTENT_EMOJI = {
    "比較検討段階": "🔍",
    "購買直前":     "🛒",
    "情報収集":     "📚",
    "価格調査":     "💰",
}

# =====================================
# APIキー取得
# =====================================
api_key = ""
if hasattr(st, "secrets"):
    api_key = st.secrets.get("OPENAI_API_KEY", "")


# =====================================
# グラフ生成関数
# =====================================
def make_score_bar_chart(valid: list) -> go.Figure:
    """購買意欲スコアの横棒グラフ"""
    keywords = [r.get("keyword", "")[:15] for r in valid]
    scores   = [r.get("purchase_score", 0) for r in valid]
    segs     = [r.get("price_segment", "Standard") for r in valid]
    colors   = [SEGMENT_INFO.get(s, SEGMENT_INFO["Standard"])["color"] for s in segs]

    fig = go.Figure(go.Bar(
        x=scores,
        y=keywords,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{s}点" for s in scores],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>購買意欲: %{x}/10<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="📈 購買意欲スコア比較", font=dict(size=15, color="#1e293b")),
        xaxis=dict(range=[0, 11], title="購買意欲スコア", tickfont=dict(size=11)),
        yaxis=dict(title="", tickfont=dict(size=11), autorange="reversed"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=60, t=50, b=30),
        height=max(300, len(valid) * 44),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9", zeroline=False)
    fig.update_yaxes(showgrid=False)
    return fig


def make_segment_pie_chart(seg_counts: dict) -> go.Figure:
    """価格帯別の円グラフ"""
    labels = []
    values = []
    colors = []
    for seg, count in seg_counts.items():
        if count > 0:
            labels.append(f"{SEGMENT_INFO[seg]['emoji']} {seg}")
            values.append(count)
            colors.append(SEGMENT_INFO[seg]["color"])

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors, line=dict(color="white", width=2)),
        textinfo="label+percent",
        textfont=dict(size=13),
        hole=0.45,
        hovertemplate="<b>%{label}</b><br>%{value}件（%{percent}）<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="🎯 価格帯別 分布", font=dict(size=15, color="#1e293b")),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=50, b=20),
        height=320,
        showlegend=True,
        legend=dict(orientation="v", x=1.0, y=0.5),
    )
    return fig


def make_intent_bar_chart(valid: list) -> go.Figure:
    """検索意図別の件数グラフ"""
    intent_counts = {}
    for r in valid:
        intent = r.get("search_intent", "不明")
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    labels = [f"{INTENT_EMOJI.get(k,'🔎')} {k}" for k in intent_counts]
    values = list(intent_counts.values())
    colors_map = {
        "比較検討段階": "#6366f1",
        "購買直前":     "#10b981",
        "情報収集":     "#f59e0b",
        "価格調査":     "#ef4444",
    }
    bar_colors = [colors_map.get(k, "#94a3b8") for k in intent_counts]

    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=values,
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y}件<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="🔍 検索意図別 件数", font=dict(size=15, color="#1e293b")),
        xaxis=dict(title="", tickfont=dict(size=12)),
        yaxis=dict(title="件数", tickfont=dict(size=11), dtick=1),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=50, b=30),
        height=300,
        showlegend=False,
    )
    fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9", zeroline=False)
    fig.update_xaxes(showgrid=False)
    return fig


# =====================================
# サイドバー
# =====================================
with st.sidebar:
    st.markdown("### 🎯 AI分析ツール")
    st.markdown("---")
    if not api_key:
        st.markdown("**🔑 APIキー設定**")
        api_key = st.text_input(
            "OpenAI APIキー",
            type="password",
            placeholder="sk-proj-...",
            label_visibility="collapsed",
        )
    else:
        st.markdown("**🔑 APIキー**")
        st.success("設定済み ✅")

    st.markdown("---")
    st.markdown("**📋 使い方**")
    st.markdown("""
1. キーワードを入力（1行1つ）
2. 「分析開始」をクリック
3. 結果・グラフを確認
4. CSVでダウンロード
""")
    st.markdown("---")
    st.markdown("**💡 価格帯の目安**")
    for seg, info in SEGMENT_INFO.items():
        st.markdown(f"{info['emoji']} **{seg}**  \n{info['strategy']}")
        st.markdown("")
    st.markdown("---")
    st.caption("v2.1 | Powered by OpenAI")


# =====================================
# ヒーローバナー
# =====================================
st.markdown("""
<div class="hero-banner">
  <div class="hero-badge">✨ AI Powered Marketing Tool</div>
  <div class="hero-title">🎯 AIキーワード分析ツール</div>
  <div class="hero-sub">
    キーワードを入力するだけで、検索意図・価格帯・購買意欲・広告文案を自動生成。<br>
    Budget から Luxury まで、ターゲット層に最適な広告戦略を提案します。
  </div>
</div>
""", unsafe_allow_html=True)


# =====================================
# タブ
# =====================================
tab_analyze, tab_result, tab_chart, tab_guide = st.tabs([
    "🔍 キーワード分析",
    "📝 分析結果",
    "📊 グラフ分析",
    "📖 使い方ガイド",
])


# =====================================
# タブ①：キーワード分析
# =====================================
with tab_analyze:
    col_input, col_btn = st.columns([3, 1])

    with col_input:
        keywords_input = st.text_area(
            "🔑 分析したいキーワードを入力（1行に1つ・最大20件）",
            height=180,
            placeholder=(
                "格安スマホ 乗り換え おすすめ\n"
                "iPhone 最新 購入\n"
                "スマホ 高級 おすすめ\n"
                "スマホ 比較 2024"
            ),
        )

    with col_btn:
        st.markdown("<br>" * 3, unsafe_allow_html=True)
        run_button = st.button(
            "🚀 分析開始",
            use_container_width=True,
            type="primary",
        )
        kw_list = [k.strip() for k in keywords_input.strip().splitlines() if k.strip()]
        st.info(f"入力数：**{len(kw_list)}件**")

    if run_button:
        if not api_key:
            st.error("⚠️ サイドバーにAPIキーを入力してください。")
            st.stop()
        if not kw_list:
            st.warning("⚠️ キーワードを1つ以上入力してください。")
            st.stop()
        if len(kw_list) > 20:
            st.warning("⚠️ 最初の20件を分析します。")
            kw_list = kw_list[:20]

        client   = get_client(api_key)
        results  = []
        progress = st.progress(0)
        status   = st.empty()

        for i, kw in enumerate(kw_list):
            status.markdown(f"⏳ 分析中... **{kw}** ({i+1}/{len(kw_list)})")
            progress.progress((i + 1) / len(kw_list))
            try:
                data = analyze_keyword_structured(client, kw)
                results.append(data)
            except Exception as e:
                results.append({"keyword": kw, "error": str(e)})
            time.sleep(0.5)

        progress.empty()
        status.success(f"✅ {len(kw_list)}件の分析完了！「📝 分析結果」「📊 グラフ分析」タブを確認してください。")
        st.session_state["results"] = results


# =====================================
# タブ②：分析結果
# =====================================
with tab_result:
    if "results" not in st.session_state:
        st.info("👈 「🔍 キーワード分析」タブで分析してください。")
        st.stop()

    results = st.session_state["results"]
    valid   = [r for r in results if "error" not in r]

    if not valid:
        st.error("有効な分析結果がありません。")
        st.stop()

    # サマリー
    st.markdown('<p class="section-title">📊 分析サマリー</p>', unsafe_allow_html=True)

    seg_counts = {s: 0 for s in SEGMENT_INFO}
    for r in valid:
        seg = r.get("price_segment", "")
        if seg in seg_counts:
            seg_counts[seg] += 1

    avg_score = sum(r.get("purchase_score", 0) for r in valid) / len(valid)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("分析件数",     f"{len(valid)}件")
    c2.metric("平均購買意欲", f"{avg_score:.1f}/10")
    c3.metric("💚 Budget",   f"{seg_counts['Budget']}件")
    c4.metric("💙 Standard", f"{seg_counts['Standard']}件")
    c5.metric("💜 Premium",  f"{seg_counts['Premium']}件")
    c6.metric("🖤 Luxury",   f"{seg_counts['Luxury']}件")

    st.markdown("---")

    # フィルター
    st.markdown('<p class="section-title">🔍 絞り込み</p>', unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    with f1:
        seg_filter = st.multiselect(
            "価格帯",
            options=list(SEGMENT_INFO.keys()),
            default=list(SEGMENT_INFO.keys()),
        )
    with f2:
        intent_opts = sorted(set(r.get("search_intent","") for r in valid if r.get("search_intent")))
        intent_filter = st.multiselect(
            "検索意図",
            options=intent_opts,
            default=intent_opts,
        )
    with f3:
        score_min = st.slider("購買意欲スコア（最小）", 1, 10, 1)

    filtered = [
        r for r in valid
        if r.get("price_segment") in seg_filter
        and r.get("search_intent") in intent_filter
        and r.get("purchase_score", 0) >= score_min
    ]
    st.caption(f"表示中：{len(filtered)}件 / {len(valid)}件")
    st.markdown("---")

    # キーワード別カード＋コピーボタン
    st.markdown('<p class="section-title">📝 キーワード別 詳細分析</p>', unsafe_allow_html=True)

    for r in filtered:
        seg    = r.get("price_segment", "Standard")
        info   = SEGMENT_INFO.get(seg, SEGMENT_INFO["Standard"])
        score  = r.get("purchase_score", 0)
        intent = r.get("search_intent", "")
        ie     = INTENT_EMOJI.get(intent, "🔎")

        # カードヘッダー部分
        st.markdown(f"""
<div class="kw-card">
  <div class="kw-title">{info['emoji']} {r['keyword']}</div>
  <div class="kw-meta">
    <span class="badge {info['badge']}">{info['label']}</span>
    <span class="meta-chip">{ie} {intent}</span>
    <span class="meta-chip">意図: {r.get('intent_reason','')}</span>
    <span class="meta-chip">層の理由: {r.get('segment_reason','')}</span>
  </div>
  <div class="score-wrap">
    <div class="score-label">
      <span>購買意欲スコア</span>
      <span style="font-weight:700;color:{info['color']};">{score} / 10</span>
    </div>
    <div class="score-bg">
      <div class="score-fill" style="width:{score*10}%;background:{info['color']};"></div>
    </div>
  </div>
  <div style="font-size:13px;font-weight:600;color:#475569;margin:16px 0 8px;">
    📣 広告文案（3パターン）
  </div>
</div>
""", unsafe_allow_html=True)

        # 広告文カード＋コピーボタン（Streamlitのボタンで実装）
        ad_cols = st.columns(3)
        for i, ad in enumerate(r.get("ad_copies", [])[:3]):
            with ad_cols[i]:
                title_text = ad.get("title", "")
                desc_text  = ad.get("description", "")
                copy_text  = f"【タイトル】{title_text}\n【説明文】{desc_text}"

                # 広告文の表示
                st.markdown(f"""
<div class="ad-card">
  <div class="ad-num">案{i+1}</div>
  <div class="ad-title-text">{title_text}</div>
  <div class="ad-desc-text">{desc_text}</div>
</div>
""", unsafe_allow_html=True)

                # コピーボタン
                # st.code でテキストを選択しやすく表示
                with st.expander("📋 テキストをコピー", expanded=False):
                    st.code(copy_text, language=None)

        # アドバイス
        st.markdown(f"""
<div class="advice-box" style="margin-top:8px;">
  💡 アドバイス：{r.get('advice','')}
</div>
<br>
""", unsafe_allow_html=True)

    # 一覧表
    st.markdown("---")
    st.markdown('<p class="section-title">📋 一覧比較表</p>', unsafe_allow_html=True)

    rows = []
    for r in filtered:
        ad1 = r.get("ad_copies", [{}])[0]
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

    # ダウンロード
    st.markdown("---")
    st.markdown('<p class="section-title">💾 データ保存</p>', unsafe_allow_html=True)
    now       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_data  = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    json_data = json.dumps(results, ensure_ascii=False, indent=2).encode("utf-8")

    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            "📥 CSVでダウンロード（Excel用）",
            data=csv_data,
            file_name=f"keyword_analysis_{now}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with dl2:
        st.download_button(
            "📥 JSONでダウンロード（生データ）",
            data=json_data,
            file_name=f"keyword_analysis_{now}.json",
            mime="application/json",
            use_container_width=True,
        )


# =====================================
# タブ③：グラフ分析
# =====================================
with tab_chart:
    if "results" not in st.session_state:
        st.info("👈 「🔍 キーワード分析」タブで分析してください。")
        st.stop()

    results = st.session_state["results"]
    valid   = [r for r in results if "error" not in r]

    if not valid:
        st.error("有効な分析結果がありません。")
        st.stop()

    seg_counts = {s: 0 for s in SEGMENT_INFO}
    for r in valid:
        seg = r.get("price_segment", "")
        if seg in seg_counts:
            seg_counts[seg] += 1

    st.markdown('<p class="section-title">📊 グラフ分析</p>', unsafe_allow_html=True)

    # 上段：棒グラフ（購買意欲）
    st.plotly_chart(
        make_score_bar_chart(valid),
        use_container_width=True,
    )

    st.markdown("---")

    # 下段：円グラフ＋検索意図グラフ を横並び
    g1, g2 = st.columns(2)

    with g1:
        st.plotly_chart(
            make_segment_pie_chart(seg_counts),
            use_container_width=True,
        )

    with g2:
        st.plotly_chart(
            make_intent_bar_chart(valid),
            use_container_width=True,
        )

    st.markdown("---")

    # グラフの読み方ガイド
    st.markdown('<p class="section-title">💡 グラフの読み方</p>', unsafe_allow_html=True)
    st.markdown("""
| グラフ | 見るべきポイント |
|--------|----------------|
| 📈 購買意欲スコア | スコアが高いほど今すぐ購入につながりやすい。8点以上は入札単価を上げる価値あり |
| 🎯 価格帯別分布 | どの層が多いか把握し、その層向けの広告文を優先的に作成する |
| 🔍 検索意図別件数 | 「購買直前」が多ければ直接訴求型、「比較検討段階」が多ければ比較訴求型が有効 |
""")


# =====================================
# タブ④：使い方ガイド
# =====================================
with tab_guide:
    st.markdown('<p class="section-title">📖 使い方ガイド</p>', unsafe_allow_html=True)
    st.markdown("""
### STEP 1　キーワードを入力する
「🔍 キーワード分析」タブを開き、分析したいキーワードを1行1つで入力します。
最大20件まで一度に分析できます。

---

### STEP 2　分析開始ボタンを押す
AIがキーワードごとに以下を分析します。

| 項目 | 内容 |
|------|------|
| 検索意図 | 比較検討段階 / 購買直前 / 情報収集 / 価格調査 |
| 価格帯層 | Budget / Standard / Premium / Luxury |
| 購買意欲スコア | 1〜10点で評価 |
| 広告文案 | タイトル＋説明文を3パターン生成 |
| アドバイス | 広告改善の最重要ポイント |

---

### STEP 3　グラフで傾向を把握する
「📊 グラフ分析」タブで3つのグラフが確認できます。

- **購買意欲スコア比較**：どのキーワードが最も購買に近いか
- **価格帯別分布**：ターゲット層の内訳
- **検索意図別件数**：ユーザーの行動パターン

---

### STEP 4　広告文をコピーして使う
各広告文の下にある「📋 テキストをコピー」を展開すると、
タイトルと説明文をそのままコピーできます。

---

### 💡 価格帯別の広告戦略

| 価格帯 | 主な訴求軸 | キーワード例 |
|--------|-----------|-------------|
| 💚 Budget | コスパ・割引・最安値 | 格安・安い・お得・割引 |
| 💙 Standard | 機能・信頼性・実績 | おすすめ・人気・比較 |
| 💜 Premium | 品質・体験・専門性 | 高品質・こだわり・プロ |
| 🖤 Luxury | ブランド・希少性・限定 | 高級・限定・ブランド |
""")
