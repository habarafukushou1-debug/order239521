# MS研修会 申し込みフォーム（Python 版）

Google Apps Script の `createMSWorkshopForm()` を Python（Google Forms API）に置き換えたものです。

## 事前準備

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成
2. 「APIとサービス」→「ライブラリ」で **Google Forms API** と **Google Sheets API** を有効化
3. 「OAuth 同意画面」を設定し、自分のアカウントをテストユーザーに追加
4. 「認証情報」→「OAuth クライアント ID」→ 種類「デスクトップアプリ」で作成し、
   JSON をダウンロードして `credentials.json` としてこのフォルダに保存
5. ライブラリをインストール

   ```bash
   pip install -r requirements.txt
   ```

## 実行

```bash
python create_ms_workshop_form.py
```

初回はブラウザが開くので Google アカウントでログインして許可します。
フォーム編集URL・回答用URL・回答保存先スプレッドシートURLが表示されます。

## 回答をスプレッドシートへ転記

Forms API には Apps Script の `setDestination()` に相当する機能がないため、
次のどちらかで回答を保存してください。

- **手動で連携（おすすめ・1回だけ）**: フォーム編集画面の「回答」タブ →
  「スプレッドシートにリンク」→ 既存のスプレッドシートを選択
- **スクリプトで転記**: 作成時に表示されたコマンドを実行

  ```bash
  python sync_responses.py <フォームID> <スプレッドシートID>
  ```

`credentials.json` と `token.json` は個人の認証情報なので共有・コミットしないでください。
