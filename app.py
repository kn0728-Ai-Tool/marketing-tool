# app.py
# AIマーケティングキーワード分析ツール

import streamlit as st
import pandas as pd
import datetime
import json
import os
from analyzer import get_client, analyze_keyword_structured

# =====================================
# ページ設定
# =====================================
st.set_page_config(
    page_title="AIキーワード分析ツール",
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
    font-family: 'Hiragino Sans', 'Yu Gothic', sans-serif;
  }
  .card {
    background: #ffffff;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
    border: 1px solid #e8eaf0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }
  .badge-budget   { background:#d1fae5; color:#065f46; padding:3px 10px; border-radius:20px; font-size:13px; font-weight:600; }
  .badge-standard { background:#dbeafe; color:#1e40af; padding:3px 10px; border-radius:20px; font-size:13px; font-weight:600; }
  .badge-premium  { background:#ede9fe; color:#5b21b6; padding:3px 10px; border-radius:20px; font-size:13px; font-weight:600; }
  .badge-luxury   { background:#1f2937; color:#f9fafb; padding:3px 10px; border-radius:20px; font-size:13px; font-weight:600; }
  .ad-card {
    background: #f8fafc;
    border-left: 4px solid #6366f1;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin-bottom: 10px;
  }
  .ad-title { font-size:15px; font-weight:700; color:#1e293b; margin-bottom:4px; }
  .ad-desc  { font-size:13px; color:#475569; }
  .score-bar-bg { background:#e2e8f0; border-radius:8px; height:10px; width:100%; }
  .score-bar    { border-radius:8px; height:10px; }
  .section-title { font-size:20px; font-weight:700; color:#1e293b; margin:24px 0 12px; }
  .advice-box {
    background: #fffbeb;
    border: 1px solid #fcd34d;
    border-radius: 8px;
    padding: 10px 16px;
    font-size:13px;
    color:#92400e;
  }
</style>
""", unsafe_allow_html=True)

# =====================================
# 価格帯の定義
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
# Streamlit CloudのSecretsから取得。
# なければサイドバーの入力欄から取得。
# =====================================
api_key = st.secrets.get("OPENAI_API_KEY", "") if hasattr(st, "secrets") else ""

# =====================================
# サイドバー
# =====================================
with st.sidebar:
    st.markdown("## ⚙️ 設定")

    if not api_key:
        api_key = st.text_input(
            "OpenAI APIキー",
            type="password",
            placeholder="sk-proj-...",
            help="Secretsに設定するか、ここに直接入力",
        )
    else:
        st.success("✅ APIキー設定済み")

    st.markdown("---")
    st.markdown("## 📋 使い方")
    st.markdown("""
1. APIキーを設定（Secrets推奨）
2. キーワードを入力（1行1つ）
3. 「分析開始」をクリック
4. 結果を確認・CSVで保存
""")
    st.markdown("---")
    st.markdown("## 💡 価格帯の目安")
    for seg, info in SEGMENT_INFO.items():
        st.markdown(f"{info['emoji']} **{seg}**: {info['strategy']}")

# =====================================
# メインエリア
# =====================================
st.markdown("# 🎯 AIキーワード分析ツール")
st.markdown("キーワードを入力するだけで、検索意図・価格帯・広告文案をAIが自動生成します。")
st.markdown("---")

col1, col2 = st.columns([3, 1])

with col1:
    keywords_input = st.text_area(
        "🔑 分析したいキーワードを入力（1行に1つ）",
        height=160,
        placeholder="格安スマホ 乗り換え おすすめ\niPhone 最新 購入\nスマホ 高級 おすすめ",
        help="最大20キーワードまで分析できます",
    )

with col2:
    st.markdown("<br><br>", unsafe_allow_html=True)
    run_button = st.button("🚀 分析開始", use_container_width=True, type="primary")
    kw_count = len([k for k in keywords_input.strip().splitlines() if k.strip()])
    st.info(f"入力キーワード数：**{kw_count}件**")

# =====================================
# 分析実行
# =====================================
if run_button:
    if not api_key:
        st.error("⚠️ APIキーを設定してください。")
        st.stop()

    keywords = [k.strip() for k in keywords_input.strip().splitlines() if k.strip()]
    if not keywords:
        st.warning("⚠️ キーワードを1つ以上入力してください。")
        st.stop()
    if len(keywords) > 20:
        st.warning("⚠️ 最初の20件を分析します。")
        keywords = keywords[:20]

    client  = get_client(api_key)
    results = []
    progress_bar = st.progress(0)
    status_text  = st.empty()

    for i, kw in enumerate(keywords):
        status_text.markdown(f"⏳ 分析中... **{kw}** ({i+1}/{len(keywords)})")
        progress_bar.progress((i + 1) / len(keywords))
        try:
            data = analyze_keyword_structured(client, kw)
            results.append(data)
        except Exception as e:
            results.append({"keyword": kw, "error": str(e)})
        import time; time.sleep(0.5)

    progress_bar.empty()
    status_text.success(f"✅ {len(keywords)}件の分析が完了しました！")
    st.session_state["results"] = results

# =====================================
# 結果表示
# =====================================
if "results" in st.session_state:
    results = st.session_state["results"]
    valid   = [r for r in results if "error" not in r]

    if not valid:
        st.error("分析結果がありません。APIキーとキーワードを確認してください。")
        st.stop()

    # サマリー
    st.markdown('<p class="section-title">📊 分析サマリー</p>', unsafe_allow_html=True)
    seg_counts = {s: 0 for s in SEGMENT_INFO}
    for r in valid:
        seg = r.get("price_segment", "")
        if seg in seg_counts:
            seg_counts[seg] += 1
    avg_score = sum(r.get("purchase_score", 0) for r in valid) / len(valid)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("分析件数",     f"{len(valid)}件")
    c2.metric("平均購買意欲", f"{avg_score:.1f} / 10")
    c3.metric("💚 Budget",   f"{seg_counts['Budget']}件")
    c4.metric("💜 Premium",  f"{seg_counts['Premium']}件")
    c5.metric("🖤 Luxury",   f"{seg_counts['Luxury']}件")

    st.markdown("---")

    # フィルター
    st.markdown('<p class="section-title">🔍 絞り込み</p>', unsafe_allow_html=True)
    f1, f2 = st.columns(2)
    with f1:
        seg_filter = st.multiselect(
            "価格帯で絞り込む",
            options=list(SEGMENT_INFO.keys()),
            default=list(SEGMENT_INFO.keys()),
        )
    with f2:
        intent_options = list({r.get("search_intent","") for r in valid if r.get("search_intent")})
        intent_filter  = st.multiselect(
            "検索意図で絞り込む",
            options=intent_options,
            default=intent_options,
        )

    filtered = [
        r for r in valid
        if r.get("price_segment") in seg_filter
        and r.get("search_intent") in intent_filter
    ]
    st.markdown(f"**表示中: {len(filtered)}件**")
    st.markdown("---")

    # キーワード別カード
    st.markdown('<p class="section-title">📝 キーワード別 詳細分析</p>', unsafe_allow_html=True)

    for r in filtered:
        seg   = r.get("price_segment", "Standard")
        info  = SEGMENT_INFO.get(seg, SEGMENT_INFO["Standard"])
        score = r.get("purchase_score", 0)
        intent = r.get("search_intent", "")
        intent_emoji = INTENT_EMOJI.get(intent, "🔎")

        with st.expander(
            f"{info['emoji']} {r['keyword']}　｜　{intent_emoji} {intent}　｜　購買意欲 {'⭐' * score}",
            expanded=True,
        ):
            left, right = st.columns([1, 2])

            with left:
                st.markdown(f"""
<div class="card">
  <div style="margin-bottom:10px;">
    <span class="{info['badge']}">{info['label']}</span>
  </div>
  <div style="font-size:13px;color:#64748b;margin-bottom:6px;">戦略: {info['strategy']}</div>
  <div style="font-size:13px;color:#64748b;margin-bottom:4px;">意図: {intent}（{r.get('intent_reason','')}）</div>
  <div style="font-size:13px;color:#64748b;">層の理由: {r.get('segment_reason','')}</div>
  <br>
  <div style="font-size:13px;font-weight:600;margin-bottom:6px;">購買意欲スコア: {score}/10</div>
  <div class="score-bar-bg">
    <div class="score-bar" style="width:{score*10}%;background:{info['color']};"></div>
  </div>
</div>
<div class="advice-box">💡 {r.get('advice','')}</div>
""", unsafe_allow_html=True)

            with right:
                st.markdown("**広告文案（3パターン）**")
                for i, ad in enumerate(r.get("ad_copies", []), 1):
                    st.markdown(f"""
<div class="ad-card">
  <div class="ad-title">案{i}：{ad.get('title','')}</div>
  <div class="ad-desc">{ad.get('description','')}</div>
</div>
""", unsafe_allow_html=True)

    # 比較表
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
    now      = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_data = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
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