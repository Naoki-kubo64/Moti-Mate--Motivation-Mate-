import warnings
warnings.filterwarnings("ignore")
import customtkinter as ctk
import threading
import time
import os
import json
import csv
import sys
from PIL import Image, ImageGrab, ImageTk
import pystray
from pystray import MenuItem as item
from win10toast import ToastNotifier
import google.generativeai as genai
from datetime import datetime

# ライブラリセットアップ
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("設定 - Motivation Mate")
        self.geometry("400x500")
        self.attributes("-topmost", True)
        
        self.create_widgets()

    def create_widgets(self):
        # タブ作成
        self.tabview = ctk.CTkTabview(self, width=380, height=480)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.tab_settings = self.tabview.add("設定")
        self.tab_history = self.tabview.add("履歴")
        
        # --- 設定タブ ---
        # API Key
        ctk.CTkLabel(self.tab_settings, text="Gemini API Key:").pack(pady=(10, 5))
        self.entry_api = ctk.CTkEntry(self.tab_settings, width=300, show="*")
        self.entry_api.pack()
        if self.parent.api_key:
            self.entry_api.insert(0, self.parent.api_key)

        # Mode
        ctk.CTkLabel(self.tab_settings, text="現在のモード (目標):").pack(pady=(10, 5))
        self.entry_mode = ctk.CTkEntry(self.tab_settings, width=300)
        self.entry_mode.pack()
        if self.parent.current_mode:
            self.entry_mode.insert(0, self.parent.current_mode)

        # Interval
        ctk.CTkLabel(self.tab_settings, text="フィードバック間隔 (分):").pack(pady=(10, 5))
        self.slider_interval = ctk.CTkSlider(self.tab_settings, from_=1, to=60, number_of_steps=59, command=self.update_interval_label)
        self.slider_interval.set(self.parent.interval_minutes)
        self.slider_interval.pack()
        self.label_interval_val = ctk.CTkLabel(self.tab_settings, text=f"{int(self.parent.interval_minutes)}分")
        self.label_interval_val.pack()

        # Show Character Switch
        self.switch_show = ctk.CTkSwitch(self.tab_settings, text="デスクトップにキャラを表示する", command=self.toggle_character)
        if self.parent.show_character:
            self.switch_show.select()
        else:
            self.switch_show.deselect()
        self.switch_show.pack(pady=20)

        # Test Run Button
        ctk.CTkButton(self.tab_settings, text="今すぐAI診断を実行", command=self.run_test_analysis, fg_color="purple", hover_color="darkmagenta").pack(pady=5)

        # Save Button
        # Save Button
        ctk.CTkButton(self.tab_settings, text="保存して閉じる", command=self.save_and_close).pack(pady=20)

        # --- 履歴タブ ---
        self.textbox_log = ctk.CTkTextbox(self.tab_history, width=350, height=400)
        self.textbox_log.pack(fill="both", expand=True, padx=5, pady=5)
        self.load_history()

    def run_test_analysis(self):
        # 設定を一時保存してから実行
        self.parent.api_key = self.entry_api.get().strip()
        self.parent.current_mode = self.entry_mode.get().strip()
        
        # 別スレッドで実行
        threading.Thread(target=self.parent.process_with_ai, daemon=True).start()
        
        # ログにも案内
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("0.0", f"[{datetime.now().strftime('%H:%M:%S')}] テスト実行リクエスト送信...\n")
        self.textbox_log.configure(state="disabled")

    def load_history(self):
        if os.path.exists("activity_log.csv"):
            try:
                with open("activity_log.csv", "r", encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    next(reader, None) # ヘッダー読み飛ばし
                    logs = list(reader)
                    
                    text = ""
                    for row in reversed(logs[-20:]): # 直近20件を新しい順に
                        if len(row) >= 4:
                            ts, mode, emo, msg = row
                            text += f"[{ts}] ({emo})\n{msg}\n{'-'*30}\n"
                    
                    self.textbox_log.insert("0.0", text)
            except Exception as e:
                self.textbox_log.insert("0.0", f"ログ読み込みエラー: {e}")
        else:
            self.textbox_log.insert("0.0", "履歴はまだありません。")
        
        self.textbox_log.configure(state="disabled")

    def update_interval_label(self, value):
        self.label_interval_val.configure(text=f"{int(value)}分")

    def toggle_character(self):
        pass # 保存時に適用

    def save_and_close(self):
        self.parent.api_key = self.entry_api.get().strip()
        self.parent.current_mode = self.entry_mode.get().strip()
        self.parent.interval_minutes = int(self.slider_interval.get())
        self.parent.show_character = bool(self.switch_show.get())
        
        # APIキー保存
        with open("api_key.txt", "w") as f:
            f.write(self.parent.api_key)
            
        self.parent.apply_settings()
        self.destroy()

class SpeechBubble(ctk.CTkToplevel):
    def __init__(self, parent, text, emotion="neutral"):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        # 背景色（透過用）
        bg_color = "#FFFFE0" # 淡い黄色
        if emotion == "angry":
            bg_color = "#FFCCCC" # 赤っぽく
        elif emotion == "happy":
            bg_color = "#E0FFFF" # 青っぽく

        self.configure(fg_color=bg_color)
        
        # ラベル (横幅を小さく)
        label = ctk.CTkLabel(self, text=text, text_color="black", wraplength=120, padx=10, pady=8, font=("Meiryo", 11))
        label.pack()
        
        # 位置調整 (親ウィンドウの左上)
        self.update_idletasks()
        try:
            # 自分のサイズ取得
            w = self.winfo_width()
            h = self.winfo_height()
            
            # 親の左上あたりに配置 (少し左へ調整)
            x = parent.winfo_x() - w + 190
            y = parent.winfo_y() - h + 190
            
            if x < 0: x = 0
            if y < 0: y = 0
            
            self.geometry(f"+{x}+{y}")
        except:
            pass

        # 自動消滅
        self.after(8000, self.destroy)

class MascotApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 設定のロード
        self.load_settings()
        
        # ウィンドウ設定
        self.title("Moti-Mate Mascot")
        self.geometry("200x250+100+100") # 初期サイズ
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.wm_attributes("-transparentcolor", "#000001") # 透過色設定 (黒に近い色)
        self.config(background="#000001") # 背景を透過色にする

        # 画像のロード
        self.images = {}
        self.load_images()
        
        # ウィジェッ (画像表示用)
        self.image_label = ctk.CTkLabel(self, text="", fg_color="#000001", bg_color="#000001") # bg必須
        self.image_label.pack(fill="both", expand=True)
        
        # イベントバインド
        self.image_label.bind("<Button-1>", self.on_click)
        self.image_label.bind("<B1-Motion>", self.on_drag)
        self.image_label.bind("<ButtonRelease-1>", self.on_drop) # ドラッグ用
        
        # 初期状態
        self.update_character_image("neutral")
        self.monitoring = False
        self.monitor_thread = None
        self.lock = threading.Lock()
        
        # トースト通知
        self.toaster = ToastNotifier()

        # スタートアップ処理
        self.start_positioning()
        
        if self.show_character:
            self.deiconify()
        else:
            self.withdraw()

        # 監視開始
        self.start_monitoring()

    def load_images(self):
        size = (180, 240) # マスコットサイズ
        emotions = ["neutral", "happy", "angry"]
        for emotion in emotions:
            path = f"assets/{emotion}.png"
            if os.path.exists(path):
                try:
                    # 背景透過のためにRGBA変換
                    pil_img = Image.open(path).convert("RGBA")
                    # リサイズ
                    pil_img = pil_img.resize(size, Image.Resampling.LANCZOS)
                    self.images[emotion] = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
                except:
                    self.images[emotion] = None
            else:
                self.images[emotion] = None

    def load_settings(self):
        self.api_key = ""
        self.current_mode = "作業中"
        self.interval_minutes = 5
        self.show_character = True
        
        if os.path.exists("api_key.txt"):
            try:
                with open("api_key.txt", "r") as f:
                    self.api_key = f.read().strip()
            except: pass

    def start_positioning(self):
        # 画面右下に配置
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = screen_width - 220
        y = screen_height - 300
        self.geometry(f"+{x}+{y}")
        self._drag_start_x = 0
        self._drag_start_y = 0

    def on_click(self, event):
        # ドラッグ開始位置記録
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        # シングルクリック判定は難しいが、ドラッグ移動しなければクリックとみなすロジックが必要
        # 簡易的に設定画面を開く機能は右クリックメニュー等にする手もあるが、
        # ここでは「離した位置が変わってなければクリック」とする
        self._click_start_pos = (self.winfo_x(), self.winfo_y())

    def on_drag(self, event):
        x = self.winfo_x() - self._drag_start_x + event.x
        y = self.winfo_y() - self._drag_start_y + event.y
        self.geometry(f"+{x}+{y}")

    def on_drop(self, event):
        cur_pos = (self.winfo_x(), self.winfo_y())
        if cur_pos == self._click_start_pos:
            self.open_settings()

    def open_settings(self):
        SettingsWindow(self)

    def apply_settings(self):
        if self.show_character:
            self.deiconify()
        else:
            self.withdraw()
        # 監視再起動などはループ内で変数を参照しているので自動適用される

    def update_character_image(self, emotion):
        img = self.images.get(emotion)
        if img:
            self.image_label.configure(image=img)
        else:
            self.image_label.configure(image=None, text=f"({emotion})")

    def start_monitoring(self):
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitor_thread.start()

    def monitoring_loop(self):
        # 起動直後にも一回実行する（ただしAPIキーがある場合）
        if self.api_key:
             self.process_with_ai()

        while self.monitoring:
            interval_sec = self.interval_minutes * 60
            next_time = time.time() + interval_sec
            
            # 待機
            while time.time() < next_time:
                if not self.monitoring: return
                time.sleep(1)
            
            if not self.api_key:
                continue

            # 実行
            self.process_with_ai()

    def process_with_ai(self):
        try:
            # スクショ
            img = ImageGrab.grab()
            
            # API
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            prompt = f"""
            ユーザーのPC画面を分析してください。目標: {self.current_mode}
            以下のJSONフォーマットのみを出力してください。Markdownタグは不要です。
            {{
                "emotion": "happy", "angry", or "neutral",
                "message": "短い日本語メッセージ(50文字以内)"
            }}
            """
            
            response = model.generate_content([prompt, img])
            text = response.text.strip()
            
            # JSON抽出 (Markdownタグ除去を強化)
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)
            
            data = json.loads(text)
            
            emotion = data.get("emotion", "neutral")
            message = data.get("message", "...")
            
            # メインスレッドでUI更新
            self.after(0, self.update_ui_reaction, emotion, message)
            
            # ログ保存
            self.save_log(emotion, message)

        except Exception as e:
            print(f"Error: {e}")
            self.save_log("error", f"エラー発生: {e}")
            # エラー時も通知を出す（ユーザーが気づけるように）
            self.after(0, self.update_ui_reaction, "neutral", f"エラー: {e}")

    def update_ui_reaction(self, emotion, message):
        self.update_character_image(emotion)
        
        if self.show_character:
            # 吹き出し表示
            SpeechBubble(self, message, emotion)
        else:
            # トースト通知
            try:
                self.toaster.show_toast("Motivation Mate", f"({emotion}) {message}", duration=5, icon_path="assets/icon.ico" if os.path.exists("assets/icon.ico") else None, threaded=True)
            except: pass

    def save_log(self, emotion, message):
        try:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("activity_log.csv", "a", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([ts, self.current_mode, emotion, message])
        except: pass

    def quit_app(self):
        self.monitoring = False
        self.quit()

# --- Tray Icon Setups ---
def run_tray(app):
    image = Image.open("assets/icon.png")
    
    def on_settings(icon, item):
        app.after(0, app.open_settings)

    def on_exit(icon, item):
        icon.stop()
        app.after(0, app.quit_app)

    menu = pystray.Menu(
        item('Settings', on_settings),
        item('Exit', on_exit)
    )

    icon = pystray.Icon("MotiMate", image, "Motivation Mate", menu)
    icon.run()

if __name__ == "__main__":
    app = MascotApp()
    
    # トレイアイコンを別スレッドで起動
    tray_thread = threading.Thread(target=run_tray, args=(app,), daemon=True)
    tray_thread.start()
    
    app.mainloop()
