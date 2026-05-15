# report.py
# =====================================
# HTMLレポート生成モジュール
# 分析結果を見やすいHTMLファイルとして出力する
# =====================================

import datetime


# =====================================
# 価格帯ごとのスタイル定義
# =====================================
SEGMENT_STYLES = {
    "Budget":   {"color": "#10b981", "bg": "#d1fae5", "text": "#065f46", "label": "💚 Budget（コスパ重視）"},
    "Standard": {"color": "#3b82f6", "bg": "#dbeafe", "text": "#1e40af", "label": "💙 Standard（標準層）"},
    "Premium":  {"color": "#8b5cf6", "bg": "#ede9fe", "text": "#5b21b6", "label": "💜 Premium（品質重視）"},
    "Luxury":   {"color": "#1f2937", "bg": "#1f2937", "text": "#f9fafb", "label": "🖤 Luxury（高級志向）"},
}

INTENT_EMOJI = {
    "比較検討段階": "🔍",
    "購買直前":     "🛒",
    "情報収集":     "📚",
    "価格調査":     "💰",
}


def _score_bar_html(score: int, color: str) -> str:
    """購買意欲スコアバーのHTMLを生成"""
    return f"""
<div style="margin:8px 0;">
  <div style="display:flex;justify-content:space-between;font-size:12px;color:#64748b;margin-bottom:4px;">
    <span>購買意欲スコア</span>
    <span style="font-weight:700;color:{color};">{score} / 10</span>
  </div>
  <div style="background:#e2e8f0;border-radius:99px;height:8px;overflow:hidden;">
    <div style="width:{score * 10}%;background:{color};height:8px;border-radius:99px;"></div>
  </div>
</div>
"""


def _ad_card_html(ad: dict, index: int) -> str:
    """広告文カード1枚のHTMLを生成"""
    title        = ad.get("title", "")
    description  = ad.get("description", "")
    appeal_point = ad.get("appeal_point", "")

    appeal_html = (
        f'<div style="margin-top:8px;font-size:11px;color:#6366f1;font-weight:600;">✨ {appeal_point}</div>'
        if appeal_point else ""
    )

    return f"""
<div style="background:#fafafe;border:1px solid #e0e7ff;border-top:3px solid #6366f1;
border-radius:10px;padding:14px 16px;position:relative;flex:1;min-width:180px;">
  <div style="position:absolute;top:8px;right:10px;font-size:11px;color:#a5b4fc;font-weight:700;">案{index}</div>
  <div style="font-size:14px;font-weight:700;color:#3730a3;margin-bottom:6px;line-height:1.4;">{title}</div>
  <div style="font-size:12px;color:#4b5563;line-height:1.6;">{description}</div>
  {appeal_html}
</div>
"""


def _keyword_section_html(r: dict) -> str:
    """キーワード1件分のセクションHTMLを生成"""
    seg     = r.get("price_segment", "Standard")
    style   = SEGMENT_STYLES.get(seg, SEGMENT_STYLES["Standard"])
    score   = r.get("purchase_score", 0)
    intent  = r.get("search_intent", "")
    ie      = INTENT_EMOJI.get(intent, "🔎")

    # 広告文3案
    ad_cards = ""
    for i, ad in enumerate(r.get("ad_copies", [])[:3], 1):
        ad_cards += _ad_card_html(ad, i)

    # 感情・競合・CTA チップ
    chips = ""
    if r.get("emotion"):
        chips += f'<span style="background:#f1f5f9;border-radius:8px;padding:3px 10px;font-size:12px;color:#475569;margin-right:6px;">😊 感情: {r["emotion"]}</span>'
    if r.get("competitor_position"):
        chips += f'<span style="background:#f1f5f9;border-radius:8px;padding:3px 10px;font-size:12px;color:#475569;margin-right:6px;">⚔️ 差別化: {r["competitor_position"]}</span>'
    if r.get("cta_suggestion"):
        chips += f'<span style="background:#f1f5f9;border-radius:8px;padding:3px 10px;font-size:12px;color:#475569;margin-right:6px;">🖱️ CTA案: {r["cta_suggestion"]}</span>'

    chips_html = (
        f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin:10px 0;">{chips}</div>'
        if chips else ""
    )

    # LP改善提案
    lp_html = ""
    if r.get("lp_advice"):
        lp_html = f"""
<div style="background:#f0fdf4;border:1px solid #86efac;border-left:4px solid #22c55e;
border-radius:10px;padding:10px 16px;font-size:13px;color:#14532d;margin:8px 0;">
  🖥️ LP改善提案：{r['lp_advice']}
</div>
"""

    # アドバイス
    advice_html = ""
    if r.get("advice"):
        advice_html = f"""
<div style="background:linear-gradient(135deg,#fffbeb,#fef3c7);border:1px solid #fcd34d;
border-left:4px solid #f59e0b;border-radius:10px;padding:12px 16px;
font-size:13px;color:#78350f;margin-top:10px;line-height:1.6;">
  💡 アドバイス：{r['advice']}
</div>
"""

    return f"""
<div style="background:white;border-radius:16px;padding:24px;margin-bottom:20px;
border:1px solid #e8eaf0;box-shadow:0 2px 12px rgba(0,0,0,0.06);page-break-inside:avoid;">

  <!-- キーワードタイトル -->
  <div style="font-size:18px;font-weight:700;color:#1e293b;margin-bottom:12px;">
    {style['label'].split('（')[0].split(' ')[0]} {r.get('keyword', '')}
  </div>

  <!-- メタ情報 -->
  <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px;align-items:center;">
    <span style="background:{style['bg']};color:{style['text']};padding:4px 14px;
    border-radius:20px;font-size:12px;font-weight:700;">{style['label']}</span>
    <span style="background:#f1f5f9;border-radius:8px;padding:4px 10px;font-size:12px;color:#475569;">
      {ie} {intent}
    </span>
    <span style="background:#f1f5f9;border-radius:8px;padding:4px 10px;font-size:12px;color:#475569;">
      意図: {r.get('intent_reason', '')}
    </span>
    <span style="background:#f1f5f9;border-radius:8px;padding:4px 10px;font-size:12px;color:#475569;">
      層の理由: {r.get('segment_reason', '')}
    </span>
  </div>

  <!-- スコアバー -->
  {_score_bar_html(score, style['color'])}

  <!-- 広告文3案 -->
  <div style="font-size:13px;font-weight:600;color:#475569;margin:16px 0 10px;">
    📣 広告文案（3パターン）
  </div>
  <div style="display:flex;gap:10px;flex-wrap:wrap;">
    {ad_cards}
  </div>

  <!-- 感情・競合・CTA -->
  {chips_html}

  <!-- LP改善提案 -->
  {lp_html}

  <!-- アドバイス -->
  {advice_html}

</div>
"""


def _summary_table_html(valid: list) -> str:
    """一覧比較表のHTMLを生成"""
    rows_html = ""
    for r in valid:
        seg   = r.get("price_segment", "")
        style = SEGMENT_STYLES.get(seg, SEGMENT_STYLES["Standard"])
        ad1   = r.get("ad_copies", [{}])[0]
        score = r.get("purchase_score", 0)

        # スコアに応じた色
        score_color = "#10b981" if score >= 8 else "#f59e0b" if score >= 5 else "#ef4444"

        rows_html += f"""
<tr>
  <td style="padding:10px 12px;border-bottom:1px solid #f1f5f9;font-weight:600;color:#1e293b;">
    {r.get('keyword', '')}
  </td>
  <td style="padding:10px 12px;border-bottom:1px solid #f1f5f9;">
    <span style="background:{style['bg']};color:{style['text']};padding:2px 10px;
    border-radius:20px;font-size:11px;font-weight:700;">{seg}</span>
  </td>
  <td style="padding:10px 12px;border-bottom:1px solid #f1f5f9;font-size:13px;color:#475569;">
    {r.get('search_intent', '')}
  </td>
  <td style="padding:10px 12px;border-bottom:1px solid #f1f5f9;text-align:center;">
    <span style="font-weight:700;color:{score_color};">{score}</span>
    <span style="font-size:11px;color:#94a3b8;">/10</span>
  </td>
  <td style="padding:10px 12px;border-bottom:1px solid #f1f5f9;font-size:12px;color:#3730a3;font-weight:600;">
    {ad1.get('title', '')}
  </td>
  <td style="padding:10px 12px;border-bottom:1px solid #f1f5f9;font-size:12px;color:#4b5563;">
    {ad1.get('description', '')}
  </td>
</tr>
"""

    return f"""
<table style="width:100%;border-collapse:collapse;font-size:13px;">
  <thead>
    <tr style="background:#f8fafc;">
      <th style="padding:10px 12px;text-align:left;color:#64748b;font-weight:600;border-bottom:2px solid #e2e8f0;">キーワード</th>
      <th style="padding:10px 12px;text-align:left;color:#64748b;font-weight:600;border-bottom:2px solid #e2e8f0;">価格帯層</th>
      <th style="padding:10px 12px;text-align:left;color:#64748b;font-weight:600;border-bottom:2px solid #e2e8f0;">検索意図</th>
      <th style="padding:10px 12px;text-align:center;color:#64748b;font-weight:600;border-bottom:2px solid #e2e8f0;">購買意欲</th>
      <th style="padding:10px 12px;text-align:left;color:#64748b;font-weight:600;border-bottom:2px solid #e2e8f0;">広告タイトル案1</th>
      <th style="padding:10px 12px;text-align:left;color:#64748b;font-weight:600;border-bottom:2px solid #e2e8f0;">広告説明文案1</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>
"""


def generate_html_report(
    results: list,
    title:   str = "AIキーワード分析レポート",
    memo:    str = "",
) -> str:
    """
    分析結果からHTMLレポートを生成して文字列で返す。
    この文字列をそのまま .html ファイルとして保存・ダウンロードできる。
    """
    valid      = [r for r in results if "error" not in r]
    now        = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M")
    kw_count   = len(valid)

    # サマリー集計
    seg_counts  = {"Budget": 0, "Standard": 0, "Premium": 0, "Luxury": 0}
    total_score = 0
    for r in valid:
        seg = r.get("price_segment", "")
        if seg in seg_counts:
            seg_counts[seg] += 1
        total_score += r.get("purchase_score", 0)
    avg_score = total_score / kw_count if kw_count else 0

    # サマリーカードHTML
    summary_cards = ""
    metrics = [
        ("分析件数",     f"{kw_count}件",          "#6366f1"),
        ("平均購買意欲", f"{avg_score:.1f} / 10",  "#f59e0b"),
        ("💚 Budget",   f"{seg_counts['Budget']}件",   "#10b981"),
        ("💙 Standard", f"{seg_counts['Standard']}件", "#3b82f6"),
        ("💜 Premium",  f"{seg_counts['Premium']}件",  "#8b5cf6"),
        ("🖤 Luxury",   f"{seg_counts['Luxury']}件",   "#1f2937"),
    ]
    for label, value, color in metrics:
        summary_cards += f"""
<div style="background:white;border-radius:12px;padding:16px 20px;
border:1px solid #e8eaf0;box-shadow:0 2px 8px rgba(0,0,0,0.05);text-align:center;flex:1;min-width:100px;">
  <div style="font-size:12px;color:#64748b;margin-bottom:6px;">{label}</div>
  <div style="font-size:22px;font-weight:800;color:{color};">{value}</div>
</div>
"""

    # キーワード別セクション
    keyword_sections = "".join(_keyword_section_html(r) for r in valid)

    # 一覧表
    summary_table = _summary_table_html(valid)

    # メモ表示
    memo_html = (
        f'<div style="margin-top:8px;font-size:14px;opacity:0.85;">📝 {memo}</div>'
        if memo else ""
    )

    # HTML全体を組み立てる
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Hiragino Sans', 'Yu Gothic UI', 'Meiryo', sans-serif;
      background: #f8fafc;
      color: #1e293b;
      line-height: 1.6;
    }}
    .container {{ max-width: 960px; margin: 0 auto; padding: 32px 20px; }}
    .section-title {{
      font-size: 18px;
      font-weight: 700;
      color: #1e293b;
      margin: 36px 0 16px;
      padding-left: 12px;
      border-left: 4px solid #6366f1;
    }}
    @media print {{
      body {{ background: white; }}
      .no-print {{ display: none; }}
      .container {{ padding: 16px; }}
    }}
    @media (max-width: 600px) {{
      .summary-grid {{ flex-direction: column; }}
    }}
  </style>
</head>
<body>
<div class="container">

  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,#6366f1 0%,#8b5cf6 50%,#06b6d4 100%);
  border-radius:16px;padding:36px 40px;margin-bottom:32px;color:white;position:relative;overflow:hidden;">
    <div style="position:absolute;top:-40px;right:-40px;width:200px;height:200px;
    background:rgba(255,255,255,0.08);border-radius:50%;"></div>
    <div style="display:inline-block;background:rgba(255,255,255,0.2);border:1px solid rgba(255,255,255,0.3);
    border-radius:20px;padding:3px 12px;font-size:12px;margin-bottom:12px;">
      ✨ AI Powered Marketing Report
    </div>
    <div style="font-size:26px;font-weight:800;margin-bottom:8px;">🎯 {title}</div>
    <div style="font-size:14px;opacity:0.85;">生成日時: {now}</div>
    {memo_html}
  </div>

  <!-- サマリー -->
  <div class="section-title">📊 分析サマリー</div>
  <div class="summary-grid" style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:8px;">
    {summary_cards}
  </div>

  <!-- 一覧比較表 -->
  <div class="section-title">📋 キーワード一覧</div>
  <div style="background:white;border-radius:16px;padding:8px;border:1px solid #e8eaf0;
  box-shadow:0 2px 12px rgba(0,0,0,0.06);overflow-x:auto;margin-bottom:8px;">
    {summary_table}
  </div>

  <!-- キーワード別詳細 -->
  <div class="section-title">📝 キーワード別 詳細分析</div>
  {keyword_sections}

  <!-- フッター -->
  <div style="text-align:center;margin-top:40px;padding-top:20px;
  border-top:1px solid #e2e8f0;font-size:12px;color:#94a3b8;">
    Generated by AIキーワード分析ツール | Powered by OpenAI | {now}
  </div>

</div>
</body>
</html>
"""
    return html
