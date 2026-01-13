# Google Gemini API キーの取得方法 / How to Get Google Gemini API Key

本アプリ「Motivation Mate」は、Google の Gemini API を使用しています。
利用するには、Google が提供する無料の API キーを取得して設定する必要があります。
手順はとても簡単です。クレジットカードの登録も不要で、無料で利用できます。

---

## 🇯🇵 日本語ガイド (Japanese)

### ステップ 1: Google AI Studio にアクセスする

1. 以下のリンクをクリックして、Google AI Studio の API キー管理ページを開きます。
   - **[Google AI Studio: API キーの取得](https://aistudio.google.com/app/apikey)**
2. Google アカウントでのログインを求められた場合は、普段お使いの Google アカウントでログインしてください。
   - ※ 初回アクセス時は、利用規約への同意画面が表示される場合があります。チェックを入れて「Continue」などを押して進んでください。

### ステップ 2: API キーを作成する

1. 画面の左上（または中央）にある、青い **「Create API key」** というボタンをクリックします。
2. 小さなウィンドウが表示されます。以下の 2 つのパターンのどちらかで作成します。

   - **パターン A（推奨）**: **「Create API key in new project」** をクリックします。

     - これを選択すると、自動的に専用の「プロジェクト」が作成され、すぐにキーが発行されます。一番簡単です。

   - **パターン B**: 既存の Google Cloud プロジェクトがある場合
     - 「Create API key in existing project」を選び、リストからプロジェクトを選択します。
     - ※ よく分からない場合は、パターン A（新しいプロジェクト）を選んでください。

### ステップ 3: キーをコピーする

1. **「API key created」** という画面が表示され、`AIzaSy...` で始まる長い文字列が表示されます。
2. 文字列の横にある **コピーボタン**（四角が重なったアイコン）をクリックして、キーをコピーします。
   - **注意**: このキーはパスワードのようなものです。他人に教えたり、公開したりしないでください。

### ステップ 4: アプリに設定する

1. Motivation Mate アプリを開きます。
2. **「設定 (Settings)」** ボタン（歯車アイコン）を押します。
3. **「AI 設定 (Intelligence)」** タブを開きます。
4. **「Gemini API Key」** という入力欄をクリックし、先ほどコピーしたキーを貼り付けます（Ctrl+V または 右クリック → 貼り付け）。
5. **「API キーを保存 (Save Key)」** ボタンを押します。

これで設定は完了です！アプリが AI と連携して喋り始めます。

---

## 🇺🇸 English Guide

### Step 1: Access Google AI Studio

1. Click the link below to open the Google AI Studio API key management page.
   - **[Google AI Studio: Get API Key](https://aistudio.google.com/app/apikey)**
2. Sign in with your Google Account if prompted.
   - _Note: If this is your first time, you may need to accept the Terms of Service._

### Step 2: Create API Key

1. Click the blue **"Create API key"** button (usually at the top left).
2. A modal window will appear. Choose one of the following options:

   - **Option A (Recommended)**: Click **"Create API key in new project"**.

     - This will automatically create a Google Cloud project for you and generate the key immediately. This is the easiest method.

   - **Option B**: If you already have a Google Cloud project
     - Click "Create API key in existing project" and select your project from the list.
     - _If you are unsure, choose Option A._

### Step 3: Copy the Key

1. You will see an **"API key created"** screen with a long string starting with `AIzaSy...`.
2. Click the **Copy** button (icon with two overlapping squares) next to the key.
   - **Warning**: Treat this key like a password. Do not share it with anyone.

### Step 4: Configure the App

1. Open the **Motivation Mate** application.
2. Click the **"Settings"** button (Gear icon).
3. Go to the **"Intelligence"** tab.
4. Paste the copied key into the **"Gemini API Key"** field.
5. Click the **"Save Key"** button.

You are all set! The mascot will now be able to interact with you using AI.
