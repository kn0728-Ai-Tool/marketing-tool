# app.py  v2.0
# UIフルリニューアル：ヘッダー・ダークモード・カード強化

import streamlit as st
import pandas as pd
import datetime
import json
import time
from analyzer import get_client, analyze_keyword_structured

# =====================================
# ページ設定（必ず最初に書く）
# =====================================
st.set_page_config(
    page_title="🎯 AIキーワード分析ツール",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================
# カスタムCSS（全デザインの核心）
# =====================================
st.markdown("""
<style>
/* =====================
   基本リセット・フォント
   ===================== */
html, body, [class*="css"] {
  font-family: 'Hiragino Sans', 'Yu Gothic UI', 'Meiryo', sans-serif;
}

/* =====================
   ヘッダーバナー
   ===================== */
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
.hero-banner::after {
  content: '';
  position: absolute;
  bottom: -60px; left: 30%;
  width: 280px; height: 280px;
  background: rgba(255,255,255,0.05);
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
  backdrop-filter: blur(4px);
}

/* =====================
   タブナビゲーション
   ===================== */
.stTabs [data-baseweb="tab-list"] {
  gap: 8px;
  background: transparent;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 0;
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
  border-color: #e2e8f0 !important;
}

/* =====================
   メトリクスカード
   ===================== */
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
[data-testid="metric-container"] [data-testid="stMetricValue"] {
  font-size: 26px;
  font-weight: 800;
  color: #1e293b;
}

/* =====================
   価格帯バッジ
   ===================== */
.badge {
  display: inline-block;
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.3px;
}
.badge-budget   { background:#d1fae5; color:#065f46; }
.badge-standard { background:#dbeafe; color:#1e40af; }
.badge-premium  { background:#ede9fe; color:#5b21b6; }
.badge-luxury   { background:#1f2937; color:#f9fafb; }

/* =====================
   キーワードカード
   ===================== */
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
  display: flex;
  align-items: center;
  gap: 8px;
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

/* =====================
   購買意欲スコアバー
   ===================== */
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
  transition: width 0.6s ease;
}

/* =====================
   広告文カード
   ===================== */
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

/* =====================
   アドバイスボックス
   ===================== */
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

/* =====================
   セクション見出し
   ===================== */
.section-title {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin: 32px 0 16px;
  padding-left: 12px;
  border-left: 4px solid #6366f1;
}

/* =====================
   サイドバー
   ===================== */
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
[data-testid="stSidebar"] hr {
  border-color: #334155 !important;
}

/* =====================
   ダウンロードボタン
   ===================== */
.stDownloadButton button {
  border-radius: 10px !important;
  font-weight: 600 !important;
  padding: 10px 20px !important;
  transition: all 0.2s !important;
}

/* =====================
   スマホ対応
   ===================== */
@media (max-width: 768px) {
  .hero-title { font-size: 20px; }
  .hero-banner { padding: 24px 20px; }
  .ad-grid { grid-template-columns: 1fr; }
}
</style>
""", unsafe_allow_html=True)


# =====================================
# 定数定義
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
3. 結果を確認・絞り込み
4. CSVでダウンロード
""")
    st.markdown("---")
    st.markdown("**💡 価格帯の目安**")
    for seg, info in SEGMENT_INFO.items():
        st.markdown(f"{info['emoji']} **{seg}**  \n{info['strategy']}")
        st.markdown("")

    st.markdown("---")
    st.caption("v2.0 | Powered by OpenAI")


# =====================================
# ヒーローバナー（ヘッダー）
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
# タブナビゲーション
# =====================================
tab_analyze, tab_result, tab_guide = st.tabs([
    "🔍 キーワード分析",
    "📊 分析結果",
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

    # ---- 分析実行 ----
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
        status.success(f"✅ {len(kw_list)}件の分析が完了！「📊 分析結果」タブを確認してください。")
        st.session_state["results"] = results


# =====================================
# タブ②：分析結果
# =====================================
with tab_result:

    if "results" not in st.session_state:
        st.info("👈 「🔍 キーワード分析」タブでキーワードを入力して分析してください。")
        st.stop()

    results = st.session_state["results"]
    valid   = [r for r in results if "error" not in r]

    if not valid:
        st.error("有効な分析結果がありません。")
        st.stop()

    # ---- サマリーメトリクス ----
    st.markdown('<p class="section-title">📊 分析サマリー</p>', unsafe_allow_html=True)

    seg_counts = {s: 0 for s in SEGMENT_INFO}
    for r in valid:
        seg = r.get("price_segment", "")
        if seg in seg_counts:
            seg_counts[seg] += 1

    avg_score  = sum(r.get("purchase_score", 0) for r in valid) / len(valid)
    top_intent = max(
        set(r.get("search_intent","") for r in valid),
        key=lambda x: sum(1 for r in valid if r.get("search_intent") == x)
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("分析件数",     f"{len(valid)}件")
    c2.metric("平均購買意欲", f"{avg_score:.1f}/10")
    c3.metric("💚 Budget",   f"{seg_counts['Budget']}件")
    c4.metric("💙 Standard", f"{seg_counts['Standard']}件")
    c5.metric("💜 Premium",  f"{seg_counts['Premium']}件")
    c6.metric("🖤 Luxury",   f"{seg_counts['Luxury']}件")

    st.markdown("---")

    # ---- フィルター ----
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

    # ---- キーワード別カード ----
    st.markdown('<p class="section-title">📝 キーワード別 詳細分析</p>', unsafe_allow_html=True)

    for r in filtered:
        seg    = r.get("price_segment", "Standard")
        info   = SEGMENT_INFO.get(seg, SEGMENT_INFO["Standard"])
        score  = r.get("purchase_score", 0)
        intent = r.get("search_intent", "")
        ie     = INTENT_EMOJI.get(intent, "🔎")

        # スコアバーの色
        score_color = info["color"]

        st.markdown(f"""
<div class="kw-card">
  <div class="kw-title">
    {info['emoji']} {r['keyword']}
  </div>
  <div class="kw-meta">
    <span class="badge {info['badge']}">{info['label']}</span>
    <span class="meta-chip">{ie} {intent}</span>
    <span class="meta-chip">意図: {r.get('intent_reason','')}</span>
    <span class="meta-chip">層の理由: {r.get('segment_reason','')}</span>
  </div>

  <div class="score-wrap">
    <div class="score-label">
      <span>購買意欲スコア</span>
      <span style="font-weight:700;color:{score_color};">{score} / 10</span>
    </div>
    <div class="score-bg">
      <div class="score-fill" style="width:{score*10}%;background:{score_color};"></div>
    </div>
  </div>

  <div style="margin-top:16px;">
    <div style="font-size:13px;font-weight:600;color:#475569;margin-bottom:8px;">📣 広告文案（3パターン）</div>
    <div class="ad-grid">
""", unsafe_allow_html=True)

        for i, ad in enumerate(r.get("ad_copies", []), 1):
            st.markdown(f"""
      <div class="ad-card">
        <div class="ad-num">案{i}</div>
        <div class="ad-title-text">{ad.get('title','')}</div>
        <div class="ad-desc-text">{ad.get('description','')}</div>
      </div>
""", unsafe_allow_html=True)

        st.markdown(f"""
    </div>
  </div>
  <div class="advice-box">💡 アドバイス：{r.get('advice','')}</div>
</div>
""", unsafe_allow_html=True)

    # ---- 一覧表 ----
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

    # ---- ダウンロード ----
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
# タブ③：使い方ガイド
# =====================================
with tab_guide:
    st.markdown('<p class="section-title">📖 使い方ガイド</p>', unsafe_allow_html=True)

    st.markdown("""
### STEP 1　キーワードを入力する
「🔍 キーワード分析」タブを開き、分析したいキーワードを1行1つで入力します。
最大20件まで一度に分析できます。

---

### STEP 2　分析開始ボタンを押す
「🚀 分析開始」ボタンをクリックすると、AIがキーワードごとに以下を分析します。

| 項目 | 内容 |
|------|------|
| 検索意図 | 比較検討段階 / 購買直前 / 情報収集 / 価格調査 |
| 価格帯層 | Budget / Standard / Premium / Luxury |
| 購買意欲スコア | 1〜10点で評価 |
| 広告文案 | タイトル＋説明文を3パターン生成 |
| アドバイス | 広告改善の最重要ポイント |

---

### STEP 3　結果を確認・絞り込む
「📊 分析結果」タブで結果を確認できます。
価格帯・検索意図・購買意欲スコアで絞り込みができます。

---

### STEP 4　CSVでダウンロード
結果をCSV形式でダウンロードしてExcelで活用できます。

---

### 💡 価格帯別の広告戦略

| 価格帯 | 主な訴求軸 | キーワード例 |
|--------|-----------|-------------|
| 💚 Budget | コスパ・割引・最安値 | 格安・安い・お得・割引 |
| 💙 Standard | 機能・信頼性・実績 | おすすめ・人気・比較 |
| 💜 Premium | 品質・体験・専門性 | 高品質・こだわり・プロ |
| 🖤 Luxury | ブランド・希少性・限定 | 高級・限定・ブランド |
""")
