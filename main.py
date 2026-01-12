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
from winotify import Notification as VerifyNotification

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
        self.geometry("420x600")
        self.attributes("-topmost", True)
        
        self.create_widgets()

    def create_widgets(self):
        # メインのスクロールフレーム作成
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=400, height=580)
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # --- 全体設定 ---
        # API Key is now managed via secrets.py (embedded), so no UI needed.

        # タブビュー作成 (スクロールフレームの中に入れる)
        self.tabview = ctk.CTkTabview(self.scroll_frame, width=360)
        self.tabview.pack(pady=10)
        
        self.tab_settings = self.tabview.add("設定")
        self.tab_timer = self.tabview.add("タイマー")
        self.tab_history = self.tabview.add("履歴")
        
        # --- [タブ] 設定 ---
        ctk.CTkLabel(self.tab_settings, text="現在のモード (目標/作業内容):").pack(pady=(10, 5))
        self.entry_mode = ctk.CTkEntry(self.tab_settings, width=250)
        self.entry_mode.pack(pady=5)
        if self.parent.current_mode:
            self.entry_mode.insert(0, self.parent.current_mode)
        
        ctk.CTkLabel(self.tab_settings, text="AIフィードバック間隔 (分):").pack(pady=(10, 5))
        self.slider_interval = ctk.CTkSlider(self.tab_settings, from_=1, to=60, number_of_steps=59, command=self.update_interval_label)
        self.slider_interval.set(self.parent.interval_minutes)
        self.slider_interval.pack(pady=5)
        self.label_interval_val = ctk.CTkLabel(self.tab_settings, text=f"{int(self.parent.interval_minutes)}分")
        self.label_interval_val.pack()

        # Custom Image Picker
        ctk.CTkLabel(self.tab_settings, text="カスタム画像 (推し画像):").pack(pady=(10, 5))
        frm_img = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        frm_img.pack()
        self.btn_image = ctk.CTkButton(frm_img, text="画像を選択...", command=self.select_image, width=120)
        self.btn_image.pack(side="left", padx=5)
        self.btn_reset_img = ctk.CTkButton(frm_img, text="リセット", command=self.reset_image, width=80, fg_color="#555")
        self.btn_reset_img.pack(side="left", padx=5)
        self.lbl_image_path = ctk.CTkLabel(self.tab_settings, text=os.path.basename(self.parent.custom_image_path) if self.parent.custom_image_path else "未選択", font=("Meiryo", 10))
        self.lbl_image_path.pack()

        # Show Character Switch
        self.switch_show = ctk.CTkSwitch(self.tab_settings, text="デスクトップにキャラを表示", command=self.toggle_character)
        if self.parent.show_character:
            self.switch_show.select()
        else:
            self.switch_show.deselect()
        self.switch_show.pack(pady=20)
        
        # Test Run Action
        ctk.CTkButton(self.tab_settings, text="今すぐAI診断を実行", command=self.run_test_analysis, fg_color="purple", hover_color="darkmagenta").pack(pady=10)

        # --- [タブ] タイマー ---
        self.timer_mode_var = ctk.StringVar(value="work")
        frm_timer_mode = ctk.CTkFrame(self.tab_timer, fg_color="transparent")
        frm_timer_mode.pack(pady=10)
        ctk.CTkRadioButton(frm_timer_mode, text="作業 (25分)", variable=self.timer_mode_var, value="work", command=self.update_timer_display_preview).pack(side="left", padx=10)
        ctk.CTkRadioButton(frm_timer_mode, text="休憩 (5分)", variable=self.timer_mode_var, value="break", command=self.update_timer_display_preview).pack(side="left", padx=10)
        
        self.lbl_timer_preview = ctk.CTkLabel(self.tab_timer, text="25:00", font=("Arial", 40, "bold"))
        self.lbl_timer_preview.pack(pady=20)
        
        frm_controls = ctk.CTkFrame(self.tab_timer, fg_color="transparent")
        frm_controls.pack(pady=10)
        ctk.CTkButton(frm_controls, text="スタート", command=self.start_timer, width=80, fg_color="#4CAF50").pack(side="left", padx=5)
        ctk.CTkButton(frm_controls, text="一時停止", command=self.pause_timer, width=80, fg_color="#FFC107").pack(side="left", padx=5)
        ctk.CTkButton(frm_controls, text="リセット", command=self.reset_timer, width=80, fg_color="#F44336").pack(side="left", padx=5)

        # --- [タブ] 履歴 ---
        self.textbox_log = ctk.CTkTextbox(self.tab_history, width=300, height=300)
        self.textbox_log.pack(fill="both", expand=True, padx=5, pady=5)
        self.load_history()

        # --- 保存ボタン (スクロール内下部) ---
        ctk.CTkButton(self.scroll_frame, text="保存して閉じる", command=self.save_and_close).pack(pady=20)

    def select_image(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif")])
        if file_path:
            self.parent.custom_image_path = file_path
            self.lbl_image_path.configure(text=os.path.basename(file_path))

    def reset_image(self):
        self.parent.custom_image_path = ""
        self.lbl_image_path.configure(text="未選択")
        self.parent.reset_custom_image()

    def update_timer_display_preview(self):
        mode = self.timer_mode_var.get()
        if mode == "work":
            self.lbl_timer_preview.configure(text="25:00")
        else:
            self.lbl_timer_preview.configure(text="05:00")
            
    def start_timer(self):
        mode = self.timer_mode_var.get()
        minutes = 25 if mode == "work" else 5
        self.parent.start_pomodoro(minutes)
        
    def pause_timer(self):
        self.parent.pause_pomodoro()
        
    def reset_timer(self):
        self.parent.reset_pomodoro()
        self.update_timer_display_preview()

    def run_test_analysis(self):
        self.parent.current_mode = self.entry_mode.get().strip()
        threading.Thread(target=self.parent.process_with_ai, daemon=True).start()
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("0.0", f"[{datetime.now().strftime('%H:%M:%S')}] テスト実行リクエスト送信...\n")
        self.textbox_log.configure(state="disabled")

    def load_history(self):
        if os.path.exists("activity_log.csv"):
            try:
                with open("activity_log.csv", "r", encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    next(reader, None)
                    logs = list(reader)
                    text = ""
                    for row in reversed(logs[-20:]):
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
        pass

    def save_and_close(self):
        # APIキーは secrets.py 管理
        self.parent.current_mode = self.entry_mode.get().strip()
        self.parent.interval_minutes = int(self.slider_interval.get())
        self.parent.show_character = bool(self.switch_show.get())
        
        settings = {
            "current_mode": self.parent.current_mode,
            "interval_minutes": self.parent.interval_minutes,
            "show_character": self.parent.show_character,
            "custom_image_path": self.parent.custom_image_path
        }
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
            
        self.parent.apply_settings()
        self.destroy()

class SpeechBubble(ctk.CTkFrame):
    def __init__(self, parent, text, emotion="neutral"):
        super().__init__(parent)
        self.parent = parent
        
        bg_color = "#FFFFE0"
        if emotion == "angry":
            bg_color = "#FFCCCC"
        elif emotion == "happy":
            bg_color = "#E0FFFF"

        self.configure(fg_color=bg_color, corner_radius=10)
        
        self.label = ctk.CTkLabel(self, text=text, text_color="black", wraplength=120, padx=10, pady=8, font=("Meiryo", 11))
        self.label.pack()
        
        self.after(8000, self.destroy)

class HeartWindow(ctk.CTkToplevel):
    def __init__(self, parent, start_x, start_y):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.wm_attributes("-transparentcolor", "#000001")
        self.config(background="#000001")
        
        self.label = ctk.CTkLabel(self, text="❤", font=("Arial", 24), text_color="#ff5e62", fg_color="#000001")
        self.label.pack()
        
        self.x = start_x
        self.y = start_y
        self.geometry(f"+{int(self.x)}+{int(self.y)}")
        
        self.steps = 0
        self.animate()
        
    def animate(self):
        if self.steps > 20: 
            self.destroy()
            return
        self.y -= 2
        self.geometry(f"+{int(self.x)}+{int(self.y)}")
        self.steps += 1
        self.after(50, self.animate)

class TimerDisplay(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(fg_color="#333333", corner_radius=8)
        self.label = ctk.CTkLabel(self, text="25:00", font=("Arial", 28, "bold"), text_color="white")
        self.label.pack(padx=10, pady=5)

    def update_time(self, text, color="white"):
        self.label.configure(text=text, text_color=color)

class MascotApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.load_settings()
        
        self.title("Moti-Mate Mascot")
        self.geometry("400x450+100+100") 
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.wm_attributes("-transparentcolor", "#000001") 
        self.config(background="#000001") 

        self.container = ctk.CTkFrame(self, fg_color="#000001", width=400, height=450)
        self.container.pack(fill="both", expand=True)

        self.mascot_x = 100
        self.mascot_y = 150
        
        self.images = {}
        self.load_images()
        self.custom_image = None
        if self.custom_image_path:
            self.load_custom_image()
        
        self.image_label = ctk.CTkLabel(self.container, text="", fg_color="#000001")
        self.image_label.place(x=self.mascot_x, y=self.mascot_y)
        
        self.image_label.bind("<Button-1>", self.on_click_start)
        self.image_label.bind("<B1-Motion>", self.on_drag)
        self.image_label.bind("<ButtonRelease-1>", self.on_click_release)
        self.image_label.bind("<Double-Button-1>", self.on_double_click)
        
        self.update_character_image("neutral")
        self.monitoring = False
        self.monitor_thread = None
        self.lock = threading.Lock()
        
        self.timer_seconds = 0
        self.timer_running = False
        self.timer_widget = None
        self.current_bubble = None

        self._click_timer = None
        self._drag_trigger = False

        self.start_positioning()
        self.start_monitoring()

    def start_positioning(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = screen_width - 450
        y = screen_height - 500
        self.geometry(f"+{x}+{y}")
        self._drag_start_x = 0
        self._drag_start_y = 0
    
    def on_click_start(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self._drag_trigger = False
        # アニメーション試行 (エラーハンドリング付き)
        try:
            self.animate_petting_start()
        except Exception as e:
            print(f"Animation Exception: {e}")

    def on_drag(self, event):
        self._drag_trigger = True
        win_x = self.winfo_x()
        win_y = self.winfo_y()
        new_x = win_x + (event.x - self._drag_start_x)
        new_y = win_y + (event.y - self._drag_start_y)
        self.geometry(f"+{new_x}+{new_y}")

    def on_click_release(self, event):
        # 戻す
        self.image_label.place(x=self.mascot_x, y=self.mascot_y)
        
        if self._drag_trigger:
            return 

        if self._click_timer:
            self.after_cancel(self._click_timer)
        self._click_timer = self.after(300, self.perform_single_click)

    def on_double_click(self, event):
        if self._click_timer:
            self.after_cancel(self._click_timer)
            self._click_timer = None
        self.open_settings()

    def perform_single_click(self):
        self.spawn_hearts()
        self._click_timer = None
    
    def animate_petting_start(self):
        x = self.winfo_x()
        y = self.winfo_y() + 3
        self.geometry(f"+{x}+{y}")

    def spawn_hearts(self):
        import random
        base_x = self.winfo_x() + self.mascot_x + 90
        base_y = self.winfo_y() + self.mascot_y + 50
        
        for _ in range(3):
            off_x = random.randint(-40, 40)
            off_y = random.randint(-10, 10)
            HeartWindow(self, base_x + off_x, base_y + off_y)

    def show_bubble(self, message, emotion="neutral"):
        if self.current_bubble and self.current_bubble.winfo_exists():
            self.current_bubble.destroy()
        
        bx = self.mascot_x + 120
        by = self.mascot_y - 60
        self.current_bubble = SpeechBubble(self.container, message, emotion)
        self.current_bubble.place(x=bx, y=by)

    def start_pomodoro(self, minutes):
        if not self.timer_running:
            if self.timer_seconds == 0:
                self.timer_seconds = minutes * 60
            
            self.timer_running = True
            
            if self.timer_widget is None or not self.timer_widget.winfo_exists():
                self.timer_widget = TimerDisplay(self.container)
                tx = self.mascot_x + 20
                ty = self.mascot_y - 50
                self.timer_widget.place(x=tx, y=ty)
                
            self.timer_widget.lift()
            self.update_timer()
            
            msg = "よし、集中しよう！" if minutes > 10 else "少し休もう！"
            self.show_bubble(msg, "happy")
            self.update_character_image("happy")

    def pause_pomodoro(self):
        self.timer_running = False
        self.show_bubble("一時停止中...", "neutral")

    def reset_pomodoro(self):
        self.timer_running = False
        self.timer_seconds = 0
        if self.timer_widget and self.timer_widget.winfo_exists():
            self.timer_widget.destroy()
            self.timer_widget = None
            
    def update_timer(self):
        if not self.timer_running:
            return
            
        if self.timer_seconds > 0:
            self.timer_seconds -= 1
            mins = self.timer_seconds // 60
            secs = self.timer_seconds % 60
            time_str = f"{mins:02}:{secs:02}"
            if self.timer_widget and self.timer_widget.winfo_exists():
                color = "white"
                if self.timer_seconds < 60: color = "#ff5e62"
                self.timer_widget.update_time(time_str, color)
            self.after(1000, self.update_timer)
        else:
            self.timer_running = False
            if self.timer_widget and self.timer_widget.winfo_exists():
                self.timer_widget.update_time("00:00", "red")
            self.show_bubble("時間だよ！お疲れ様！", "happy")
            self.update_character_image("happy")
            try:
                VerifyNotification(app_id="Moti-Mate", title="Timer Finished", msg="時間になりました！", icon=os.path.abspath("assets/happy.png")).show()
            except: pass

    def load_custom_image(self):
        if os.path.exists(self.custom_image_path):
            try:
                img = Image.open(self.custom_image_path).convert("RGBA")
                img.thumbnail((180, 240), Image.Resampling.LANCZOS)
                self.custom_image = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            except Exception as e:
                print(f"Failed to load custom image: {e}")
                self.custom_image = None
                
    def reset_custom_image(self):
        self.custom_image_path = ""
        self.custom_image = None
        self.update_character_image("neutral")

    def load_images(self):
        size = (180, 240)
        emotions = ["neutral", "happy", "angry"]
        for emotion in emotions:
            path = f"assets/{emotion}.png"
            if os.path.exists(path):
                try:
                    pil_img = Image.open(path).convert("RGBA")
                    pil_img = pil_img.resize(size, Image.Resampling.LANCZOS)
                    self.images[emotion] = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
                except:
                    self.images[emotion] = None
            else:
                self.images[emotion] = None

    def load_settings(self):
        try:
            import secrets
            self.api_key = secrets.GEMINI_API_KEY
        except ImportError:
            self.api_key = ""
            print("Warning: secrets.py not found. API functionality will be limited.")

        self.current_mode = "作業中"
        self.interval_minutes = 5
        self.show_character = True
        self.custom_image_path = ""
        
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.current_mode = data.get("current_mode", "作業中")
                    self.interval_minutes = data.get("interval_minutes", 5)
                    self.show_character = data.get("show_character", True)
                    self.custom_image_path = data.get("custom_image_path", "")
            except: pass

    def open_settings(self):
        SettingsWindow(self)

    def apply_settings(self):
        if self.custom_image_path:
            self.load_custom_image()
            
        if self.show_character:
            self.deiconify()
        else:
            self.withdraw()
            
        self.update_character_image("neutral")

    def update_character_image(self, emotion):
        if self.custom_image:
            self.image_label.configure(image=self.custom_image, text="")
        else:
            img = self.images.get(emotion)
            if img:
                self.image_label.configure(image=img, text="")
            else:
                self.image_label.configure(image=None, text=f"({emotion})")

    def start_monitoring(self):
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitor_thread.start()

    def log_debug(self, msg):
        try:
            with open("debug.log", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        except: pass

    def monitoring_loop(self):
        self.log_debug("Monitoring loop started.")
        if self.api_key:
             self.process_with_ai()

        while self.monitoring:
            interval_sec = self.interval_minutes * 60
            slept = 0
            while slept < interval_sec:
                if not self.monitoring: 
                    return
                
                current_interval_sec = self.interval_minutes * 60
                if current_interval_sec != interval_sec:
                    interval_sec = current_interval_sec
                    slept = 0 
                
                time.sleep(1)
                slept += 1
            
            if not self.api_key:
                continue

            self.process_with_ai()

    def process_with_ai(self):
        try:
            img = ImageGrab.grab()
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
            
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)
            
            data = json.loads(text)
            
            emotion = data.get("emotion", "neutral")
            message = data.get("message", "...")
            
            self.after(0, self.update_ui_reaction, emotion, message)
            self.save_log(emotion, message)

        except Exception as e:
            print(f"Error: {e}")
            self.save_log("error", f"エラー発生: {e}")
            self.after(0, self.update_ui_reaction, "neutral", f"エラー: {e}")

    def update_ui_reaction(self, emotion, message):
        self.update_character_image(emotion)
        
        if self.show_character:
            self.show_bubble(message, emotion)
        else:
            try:
                icon_path = os.path.abspath(f"assets/{emotion}.png")
                if not os.path.exists(icon_path):
                    icon_path = os.path.abspath("assets/neutral.png")
                
                toast = VerifyNotification(
                    app_id="Moti-Mate",
                    title="Motivation Mate",
                    msg=message,
                    icon=icon_path
                )
                toast.show()
            except Exception as e:
                print(f"Notification error: {e}")

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
    tray_thread = threading.Thread(target=run_tray, args=(app,), daemon=True)
    tray_thread.start()
    app.mainloop()
