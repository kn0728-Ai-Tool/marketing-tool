# CLAUDE.md — AIキーワード分析ツール

Claude Code がこのリポジトリで作業するときに最初に読む「作業ルール」です。

## 1. プロジェクト概要
- Streamlit 製の「AIキーワード分析ツール」。GitHub `main` ブランチ → Streamlit Cloud に自動デプロイ。
- **`main` に push した瞬間に本番へ反映される**ので、push 前に必ず動作確認すること。
- 利用者（オーナー）は非エンジニア。Windows / GitHub Web版（github.com）で運用。

## 2. 技術スタック
- Python 3.11 / Streamlit / Plotly / pandas / SQLite
- OpenAI API（`gpt-4o-mini`）
- Google Trends（pytrends）/ Google News RSS
- python-pptx / openpyxl / python-docx / pypdf

## 3. ファイル構成
| ファイル | 役割 |
|---|---|
| `app.py` | メインUI（9タブ）。CSSもこの中の `st.markdown("<style>…")` に集約 |
| `analyzer.py` | キーワード分析（価格帯別広告文生成） |
| `csv_analyzer.py` | CSV自動列認識・AI分析・**Excel集計出力（`export_to_excel`）** |
| `trend_analyzer.py` | トレンド予測・ヒートマップ・年代別AI分析 |
| `market_trend.py` | Google Trends / News 取得（JST対応） |
| `database.py` | SQLite（`/tmp` に保存 → Streamlit Cloud再起動で消える） |
| `report.py` | HTMLレポート生成 |
| `digest_creator.py` | 複数資料 → PPTX/XLSX ダイジェスト |

タブ: キーワード分析 / 分析結果 / グラフ分析 / トレンド分析 / CSV分析 & 集計 / 文章要約・整形 / ダイジェスト & プレゼン / 分析履歴 / 使い方ガイド

## 4. 必ず守るルール
1. **既存コードを壊さない。変更は最小限。** 既存関数のシグネチャ・戻り値は変えない（他ファイルから import されている）。
2. **日時はすべて日本時間（JST）。** `datetime.datetime.now(JST)`（`JST = ZoneInfo("Asia/Tokyo")`）を使う。`datetime.now()` 単体は禁止。
3. **UI・コメント・説明はすべて日本語。**
4. **APIキーをコードやコミットに書かない。** 読み込み順は `st.secrets` → 環境変数 `OPENAI_API_KEY` → サイドバー入力。
5. 新しいライブラリを使ったら `requirements.txt` に追記する。
6. オーナーへの説明は初心者向けに丁寧に。コードを提示する場合は**ファイル全文**で渡す。

## 5. ローカルで起動・確認する方法
```bash
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."      # 任意（無くても画面は開く）
streamlit run app.py --server.port 8501
```
ブラウザで http://localhost:8501 を開く。

## 6. 変更後のチェック（push前に必須）
```bash
# 構文チェック
python -m py_compile *.py
# 画面を最後まで実行してエラーが出ないか確認（APIキー不要）
python -c "from streamlit.testing.v1 import AppTest; at=AppTest.from_file('app.py',default_timeout=90).run(); print('例外:', [e.value for e in at.exception]); print('タブ数:', len(at.tabs))"
```
`例外: []` かつ `タブ数: 9` ならOK。

## 7. 過去の決定事項（やり直さないこと）
- タブの左右移動は **タブ下のスクロールバー（インディゴ色・6px）** で行う。固定位置のJS注入ボタンは「邪魔」と不評だったため廃止済み。
- CSV分析タブの Excel 出力は「項目ごとに別シート」構成（クリーニングレポート / サマリー / クリーニング済みデータ / 列別詳細 / AI分析結果）。
