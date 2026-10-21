# marketing-tool
AIキーワード分析ツール（Streamlit）

- 本番：Streamlit Cloud（`main` ブランチへ push すると自動反映）
- 開発ルール：[`CLAUDE.md`](CLAUDE.md) を参照（Claude Code はこれを自動で読み込みます）

## ローカル / Claude Code での起動
```bash
pip install -r requirements.txt
streamlit run app.py
```
APIキーは環境変数 `OPENAI_API_KEY`、または `.streamlit/secrets.toml`（`secrets.toml.example` をコピー）で設定。未設定でも画面は開き、サイドバーで入力できます。
