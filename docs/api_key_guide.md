# Google Gemini API キーの取得方法 / How to Get Google Gemini API Key

本アプリ「Motivation Mate」は、Google の Gemini API を使用しています。
利用には Google の無料 API キーが必要です。
**「新しいプロジェクトで作成」ボタンが表示されない場合**は、以下の手順で Google Cloud プロジェクトを作成してからキーを取得してください。

---

## 🇯🇵 日本語ガイド (Japanese)

### ステップ 1: Google Cloud プロジェクトを作成する

Google AI Studio で直接プロジェクトが作れない場合は、先に「Google Cloud Console」でプロジェクトを用意します。

1. **Google Cloud Console にアクセス**
   - 以下のリンクを開きます。
   - **[Google Cloud Console (プロジェクト作成)](https://console.cloud.google.com/projectcreate)**
   - Google アカウントでログインしてください。
2. **プロジェクト情報の入力**
   - **プロジェクト名**: 好きな名前を入力します（例: `My Gemini App`）。
   - **場所**: 「組織なし」のままで OK です。
3. **作成ボタンを押す**
   - 「作成」をクリックします。
   - 数秒〜数十秒待つと、右上の通知ベルアイコンに「プロジェクトを作成しました」と表示されます。

### ステップ 2: Google AI Studio でキーを取得する

プロジェクトができたら、AI Studio に戻ってキーを発行します。

1. **Google AI Studio にアクセス**
   - 以下のリンクを開きます。
   - **[Google AI Studio: API キーの取得](https://aistudio.google.com/app/apikey)**
2. **API キーの作成**
   - 青い **「Create API key」** ボタンをクリックします。
3. **プロジェクトの選択**
   - キー作成画面で、入力欄の下にある **「プロジェクトをインポート」**（または検索ボックス）をクリックします。
   - 先ほど作成したプロジェクト（例: `My Gemini App`）が表示されるので、それを選択します。
   - ※もし表示されない場合は、ページを再読み込みしてからもう一度試してください。
4. **キーの確定**
   - プロジェクトを選択した状態で **「Create API key in existing project」**（または決定ボタン）を押します。

### ステップ 3: キーをコピーしてアプリに登録

1. **キーのコピー**
   - `AIzaSy...` で始まる API キーが表示されます。
   - 横にある **コピーボタン** を押してコピーします。
2. **Motivation Mate に設定**
   - アプリの「設定」→「AI 設定」を開きます。
   - 「Gemini API Key」欄に貼り付けて、「API キーを保存」を押します。

---

## 🇺🇸 English Guide

### Step 1: Create a Google Cloud Project

If you cannot create a project directly in AI Studio, please create one in Google Cloud Console first.

1. **Go to Google Cloud Console**
   - Open: **[Google Cloud Console (Create Project)](https://console.cloud.google.com/projectcreate)**
   - Sign in with your Google Account.
2. **Enter Project Details**
   - **Project Name**: Enter any name (e.g., `My Gemini App`).
   - **Location**: Leave as "No organization".
3. **Click Create**
   - Click "Create" and wait a few seconds until you get a notification that the project is ready.

### Step 2: Generate API Key in AI Studio

1. **Go to Google AI Studio**
   - Open: **[Google AI Studio: Get API Key](https://aistudio.google.com/app/apikey)**
2. **Create API Key**
   - Click the blue **"Create API key"** button.
3. **Select Your Project**
   - Click the project selection dropdown (or "Import project").
   - Select the project you just created (e.g., `My Gemini App`).
   - _If it doesn't appear, try refreshing the page._
4. **Generate**
   - Click to generate the key for the selected project.

### Step 3: Configure Motivation Mate

1. **Copy Key**: Copy the `AIzaSy...` key string.
2. **Paste**: Open Motivation Mate Settings -> Intelligence tab.
3. **Save**: Paste the key and click "Save Key".
