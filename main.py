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
from presets import PERSONALITY_PRESETS

# ライブラリセットアップ
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("設定 - Motivation Mate")
        # サイズを少し大きくする
        self.geometry("480x650")
        self.attributes("-topmost", True)
        
        # フォント設定 (モダンな雰囲気)
        self.font_main = ("Meiryo UI", 12)
        self.font_bold = ("Meiryo UI", 12, "bold")
        self.font_small = ("Meiryo UI", 10)
        
        # 全体を白/明るいテーマに強制 (ユーザー要望)
        ctk.set_appearance_mode("Light") 
        
        self.create_widgets()

    def create_widgets(self):
        # メインコンテナ (パディングで余白確保)
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # タブビュー
        self.tabview = ctk.CTkTabview(main_frame, width=440)
        self.tabview.pack(fill="both", expand=True)
        self.tabview.add("基本設定")      # General
        self.tabview.add("AI設定")        # Intelligence
        self.tabview.add("表示・通知")    # Appearance

        self.setup_general_tab()
        self.setup_intelligence_tab()
        self.setup_appearance_tab()

        # フッター (保存・キャンセル)
        frm_footer = ctk.CTkFrame(main_frame, fg_color="transparent", height=50)
        frm_footer.pack(fill="x", side="bottom", pady=(10, 0))
        
        btn_save = ctk.CTkButton(frm_footer, text="保存して閉じる", command=self.save_and_close, 
                                 font=self.font_bold, fg_color="#4CAF50", hover_color="#45a049", height=40)
        btn_save.pack(side="right", padx=10)
        
        btn_cancel = ctk.CTkButton(frm_footer, text="キャンセル", command=self.destroy,
                                   font=self.font_main, fg_color="#999999", hover_color="#777777", height=40)
        btn_cancel.pack(side="right", padx=0)

    def setup_general_tab(self):
        tab = self.tabview.tab("基本設定")
        
        # 目標設定
        frm_goal = ctk.CTkFrame(tab, fg_color="transparent")
        frm_goal.pack(fill="x", pady=10)
        ctk.CTkLabel(frm_goal, text="現在の目標 (モード):", font=self.font_bold).pack(anchor="w")
        self.entry_mode = ctk.CTkEntry(frm_goal, font=self.font_main, height=35)
        self.entry_mode.pack(fill="x", pady=(5, 0))
        if self.parent.current_mode:
            self.entry_mode.insert(0, self.parent.current_mode)
            
        # タイマー設定 (LabelFrame風)
        frm_timer = ctk.CTkFrame(tab, border_width=1, border_color="#DDDDDD", fg_color="white")
        frm_timer.pack(fill="x", pady=20, padx=5, ipady=10)
        ctk.CTkLabel(frm_timer, text="ポモドーロ設定", font=self.font_bold).pack(anchor="w", padx=10, pady=5)
        
        # 作業時間
        frm_work = ctk.CTkFrame(frm_timer, fg_color="transparent")
        frm_work.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frm_work, text="作業時間 (分):", font=self.font_main, width=100).pack(side="left")
        self.slider_work = ctk.CTkSlider(frm_work, from_=1, to=60, number_of_steps=59, command=lambda v: self.lbl_work_val.configure(text=f"{int(v)}分"))
        self.slider_work.set(self.parent.work_minutes)
        self.slider_work.pack(side="left", fill="x", expand=True, padx=10)
        self.lbl_work_val = ctk.CTkLabel(frm_work, text=f"{int(self.parent.work_minutes)}分", font=self.font_main, width=40)
        self.lbl_work_val.pack(side="left")

        # 休憩時間
        frm_break = ctk.CTkFrame(frm_timer, fg_color="transparent")
        frm_break.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frm_break, text="休憩時間 (分):", font=self.font_main, width=100).pack(side="left")
        self.slider_break = ctk.CTkSlider(frm_break, from_=1, to=30, number_of_steps=29, command=lambda v: self.lbl_break_val.configure(text=f"{int(v)}分"))
        self.slider_break.set(self.parent.break_minutes)
        self.slider_break.pack(side="left", fill="x", expand=True, padx=10)
        self.lbl_break_val = ctk.CTkLabel(frm_break, text=f"{int(self.parent.break_minutes)}分", font=self.font_main, width=40)
        self.lbl_break_val.pack(side="left")
        
        # タイマー操作ボタン
        frm_btns = ctk.CTkFrame(frm_timer, fg_color="transparent")
        frm_btns.pack(fill="x", pady=(10, 5), padx=10)
        ctk.CTkButton(frm_btns, text="開始/停止", command=self.parent.toggle_timer, font=self.font_bold, width=120, height=35).pack(side="left", padx=5, expand=True)
        ctk.CTkButton(frm_btns, text="リセット", command=self.parent.reset_timer, font=self.font_main, fg_color="#777", width=80, height=35).pack(side="left", padx=5)
        
        # AIフィードバック間隔 (Legacy) also helpful
        ctk.CTkLabel(tab, text="※AIは設定された作業/休憩時間に関わらず、\n　アプリ内のインターバル設定に従って定期診断を行います。", font=self.font_small, text_color="#666").pack(pady=10)
        
        self.slider_interval = ctk.CTkSlider(tab, from_=1, to=60, number_of_steps=59, command=lambda v: self.lbl_int_val.configure(text=f"診断間隔: {int(v)}分"))
        self.slider_interval.set(self.parent.interval_minutes)
        self.slider_interval.pack(fill="x", padx=10, pady=(10,0))
        self.lbl_int_val = ctk.CTkLabel(tab, text=f"診断間隔: {int(self.parent.interval_minutes)}分", font=self.font_main)
        self.lbl_int_val.pack()

    def setup_intelligence_tab(self):
        tab = self.tabview.tab("AI設定")
        
        # モデル選択
        ctk.CTkLabel(tab, text="使用モデル:", font=self.font_bold).pack(anchor="w", pady=(10, 5))
        self.combo_model = ctk.CTkComboBox(tab, values=["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"], font=self.font_main)
        self.combo_model.set(self.parent.ai_model)
        self.combo_model.pack(fill="x", pady=5)
        
        # 性格プリセット選択
        ctk.CTkLabel(tab, text="性格・振る舞い (プリセット):", font=self.font_bold).pack(anchor="w", pady=(15, 5))
        
        # ラベルとIDの対応作成
        self.preset_map = {v["label"]: k for k, v in PERSONALITY_PRESETS.items()}
        preset_labels = list(self.preset_map.keys())
        
        # 現在のIDからラベルを逆引き
        current_label = PERSONALITY_PRESETS.get(self.parent.personality_id, PERSONALITY_PRESETS["default"])["label"]
        
        self.combo_preset = ctk.CTkComboBox(tab, values=preset_labels, command=self.update_preset_description, font=self.font_main)
        self.combo_preset.set(current_label)
        self.combo_preset.pack(fill="x", pady=5)
        
        # 説明表示用ラベル
        self.lbl_preset_desc = ctk.CTkLabel(tab, text="", font=self.font_small, text_color="#555", wraplength=400, justify="left")
        self.lbl_preset_desc.pack(fill="x", pady=(0, 10))
        self.update_preset_description(current_label) # 初期表示更新

        # テスト実行
        ctk.CTkButton(tab, text="設定を保存してAI診断テスト", command=self.run_test_analysis, fg_color="#9C27B0", hover_color="#7B1FA2", font=self.font_bold).pack(pady=10)
        
        # ログ表示用
        self.textbox_log = ctk.CTkTextbox(tab, height=80, font=self.font_small)
        self.textbox_log.pack(fill="x", pady=5)
        self.textbox_log.insert("0.0", "ここにテスト結果等が表示されます...")
        self.textbox_log.configure(state="disabled")

    def update_preset_description(self, choice):
        pid = self.preset_map.get(choice, "default")
        desc = PERSONALITY_PRESETS[pid]["description"]
        self.lbl_preset_desc.configure(text=desc)

    def setup_appearance_tab(self):
        tab = self.tabview.tab("表示・通知")

        # 透明度
        ctk.CTkLabel(tab, text="ウィンドウ透明度:", font=self.font_bold).pack(anchor="w", pady=(10, 5))
        self.slider_alpha = ctk.CTkSlider(tab, from_=0.1, to=1.0, number_of_steps=90, command=lambda v: self.lbl_alpha.configure(text=f"{int(v*100)}%"))
        self.slider_alpha.set(self.parent.window_transparency)
        self.slider_alpha.pack(fill="x", pady=5)
        self.lbl_alpha = ctk.CTkLabel(tab, text=f"{int(self.parent.window_transparency*100)}%", font=self.font_main)
        self.lbl_alpha.pack()
        
        # スイッチ類
        self.switch_top = ctk.CTkSwitch(tab, text="常に手前に表示", font=self.font_main)
        if self.parent.always_on_top: self.switch_top.select()
        else: self.switch_top.deselect()
        self.switch_top.pack(anchor="w", pady=10)

        self.switch_notify = ctk.CTkSwitch(tab, text="システム通知を有効化", font=self.font_main)
        if self.parent.enable_notifications: self.switch_notify.select()
        else: self.switch_notify.deselect()
        self.switch_notify.pack(anchor="w", pady=10)
        
        self.switch_show = ctk.CTkSwitch(tab, text="キャラクターを表示する", command=self.toggle_character, font=self.font_main)
        if self.parent.show_character: self.switch_show.select()
        else: self.switch_show.deselect()
        self.switch_show.pack(anchor="w", pady=10)

        # カスタム画像
        frm_img = ctk.CTkFrame(tab, border_width=1, border_color="#DDDDDD", fg_color="white")
        frm_img.pack(fill="x", pady=20, padx=5, ipady=10)
        ctk.CTkLabel(frm_img, text="カスタム画像設定", font=self.font_bold).pack(anchor="w", padx=10)
        
        self.switch_remove_bg = ctk.CTkSwitch(frm_img, text="白背景を透過 (自動修正)", font=self.font_main)
        if self.parent.remove_white_bg: self.switch_remove_bg.select()
        else: self.switch_remove_bg.deselect()
        self.switch_remove_bg.pack(anchor="w", padx=10, pady=5)
        
        btn_img = ctk.CTkButton(frm_img, text="画像ファイルを選択...", command=self.select_image, font=self.font_main, width=150)
        btn_img.pack(padx=10, pady=5, anchor="w")
        
        self.lbl_image_path = ctk.CTkLabel(frm_img, text=os.path.basename(self.parent.custom_image_path) if self.parent.custom_image_path else "未選択", font=self.font_small, text_color="#555")
        self.lbl_image_path.pack(padx=10, anchor="w")
        
        ctk.CTkButton(frm_img, text="リセット", command=self.reset_image, font=self.font_small, fg_color="#777", width=60, height=20).pack(padx=10, pady=5, anchor="w")

    def select_image(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif")])
        if file_path:
            self.parent.custom_image_path = file_path
            self.lbl_image_path.configure(text=os.path.basename(file_path))

    def reset_image(self):
        self.parent.custom_image_path = ""
        self.lbl_image_path.configure(text="未選択")
        self.parent.reset_custom_image()

    def toggle_character(self):
        pass

    def run_test_analysis(self):
        # 設定を一時保存的に適用してテスト
        self.parent.current_mode = self.entry_mode.get().strip()
        self.parent.ai_model = self.combo_model.get()
        
        # 選択中のプリセットからプロンプトを取得して一時適用
        pid = self.preset_map.get(self.combo_preset.get(), "default")
        self.parent.system_prompt = PERSONALITY_PRESETS[pid]["system_prompt"]
        
        def on_complete(emotion, message):
            self.textbox_log.configure(state="normal")
            ts = datetime.now().strftime('%H:%M:%S')
            self.textbox_log.insert("0.0", f"[{ts}] ({emotion})\n{message}\n{'-'*30}\n")
            self.textbox_log.configure(state="disabled")

        threading.Thread(target=self.parent.process_with_ai, args=(on_complete,), daemon=True).start()
        
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("0.0", f"[{datetime.now().strftime('%H:%M:%S')}] テストリクエスト中... ({pid})\n")
        self.textbox_log.configure(state="disabled")

    def save_and_close(self):
        self.parent.current_mode = self.entry_mode.get().strip()
        self.parent.work_minutes = int(self.slider_work.get())
        self.parent.break_minutes = int(self.slider_break.get())
        self.parent.interval_minutes = int(self.slider_interval.get())
        
        self.parent.ai_model = self.combo_model.get()
        
        # プリセットIDを保存
        pid = self.preset_map.get(self.combo_preset.get(), "default")
        self.parent.personality_id = pid
        self.parent.system_prompt = PERSONALITY_PRESETS[pid]["system_prompt"]
        
        self.parent.window_transparency = float(self.slider_alpha.get())
        self.parent.always_on_top = bool(self.switch_top.get())
        self.parent.enable_notifications = bool(self.switch_notify.get())
        self.parent.show_character = bool(self.switch_show.get())
        self.parent.remove_white_bg = bool(self.switch_remove_bg.get())

        settings = {
            "current_mode": self.parent.current_mode,
            "interval_minutes": self.parent.interval_minutes,
            "work_minutes": self.parent.work_minutes,
            "break_minutes": self.parent.break_minutes,
            "ai_model": self.parent.ai_model,
            "personality_id": self.parent.personality_id,
            "window_transparency": self.parent.window_transparency,
            "always_on_top": self.parent.always_on_top,
            "enable_notifications": self.parent.enable_notifications,
            "show_character": self.parent.show_character,
            "remove_white_bg": self.parent.remove_white_bg,
            "custom_image_path": self.parent.custom_image_path
        }
        
        try:
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
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
        # Canvasを使わずFrameとplaceで配置する
        # 全体コンテナ (透明) - corner_radius=0 で四隅の白いアーティファクトを消す
        self.container = ctk.CTkFrame(self, fg_color="#000001", width=400, height=450, corner_radius=0)
        self.container.pack(fill="both", expand=True)

        # キャラクター画像の位置 (少し右に寄せて左に吹き出しスペースを作る)
        self.mascot_x = 160
        self.mascot_y = 150
        
        # 画像のロード
        self.images = {}
        self.load_images()
        self.custom_image = None
        if self.custom_image_path:
            self.load_custom_image()
        
        # 画像ラベル (透明背景)
        self.image_label = ctk.CTkLabel(self.container, text="", fg_color="#000001")
        self.image_label.place(x=self.mascot_x, y=self.mascot_y)
        
        # イベントバインド (画像をクリック・ドラッグの起点にする)
        self.image_label.bind("<Button-1>", self.on_click_start)
        self.image_label.bind("<B1-Motion>", self.on_drag)
        self.image_label.bind("<ButtonRelease-1>", self.on_click_release)
        self.image_label.bind("<Double-Button-1>", self.on_double_click)
        
        # 初期状態
        self.update_character_image("neutral")
        self.monitoring = False
        self.monitor_thread = None
        self.lock = threading.Lock()
        
        # タイマー関連
        self.timer_seconds = 0
        self.timer_running = False
        self.timer_widget = None # Frame
        self.current_bubble = None # Frame

        # クリック管理
        self._click_timer = None
        self._drag_trigger = False

        self.start_positioning()
        self.start_monitoring()

    def start_positioning(self):
        # 画面右下に配置
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
        
        # マスコットの左下寄りに出す
        bx = self.mascot_x - 80
        by = self.mascot_y + 10
        
        self.current_bubble = SpeechBubble(self.container, message, emotion)
        self.current_bubble.place(x=bx, y=by)

    def start_pomodoro(self, minutes):
        if not self.timer_running:
            if self.timer_seconds == 0:
                self.timer_seconds = minutes * 60
            
            self.timer_running = True
            
            if self.timer_widget is None or not self.timer_widget.winfo_exists():
                self.timer_widget = TimerDisplay(self.container)
                # タイマーはマスコットの右側（さらに左上）ヘ
                tx = self.mascot_x + 60
                ty = self.mascot_y + 0
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
        if self.timer_widget:
            self.timer_widget.place_forget()

    def toggle_timer(self):
        if self.timer_running:
            self.pause_pomodoro()
        else:
            self.start_pomodoro(self.work_minutes)

    def reset_timer(self):
        self.reset_pomodoro()
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
            # タイマー終了
            self.timer_running = False
            if self.timer_widget and self.timer_widget.winfo_exists():
                self.timer_widget.update_time("00:00", "red")
            
            self.update_character_image("happy")
            
            msg = "時間だよ！お疲れ様！\n休憩が終わったなら、また頑張ろう！"

            if self.show_character:
                # キャラ表示中は吹き出し
                self.show_bubble("時間だよ！お疲れ様！", "happy")
            else:
                # キャラ非表示 -> Windows通知 (Winotifyを使用)
                try:
                    # Winotify (VerifyNotification) は main.py 冒頭で import 済み
                    # iconは assets/icon.ico または happy.png を使う
                    icon_path = os.path.abspath("assets/icon.ico")
                    if not os.path.exists(icon_path):
                        icon_path = os.path.abspath("assets/happy.png")
                    
                    toast = VerifyNotification(
                        app_id="Moti-Mate",
                        title="Timer Finished",
                        msg=msg,
                        icon=icon_path
                    )
                    toast.show()
                except Exception as e:
                    print(f"Notification failed: {e}")

    def load_custom_image(self):
        if os.path.exists(self.custom_image_path):
            try:
                img = Image.open(self.custom_image_path).convert("RGBA")
                
                # 白背景透過処理 (Flood Fill)
                if self.remove_white_bg:
                    try:
                        from PIL import ImageDraw
                        # 左上(0,0)の色を取得 (これが背景色と仮定)
                        bg_color = img.getpixel((0, 0))
                        
                        # 背景色が白っぽい場合のみ実行 (誤爆防止)
                        # R,G,Bがすべて200以上なら白とみなす
                        if all(c > 200 for c in bg_color[:3]):
                            # ImageDraw.floodfillで (0,0) を起点に透明色(0,0,0,0)で塗りつぶす
                            # threshで多少の色の揺らぎを許容
                            ImageDraw.floodfill(img, xy=(0, 0), value=(0, 0, 0, 0), thresh=50)
                    except Exception as e:
                        print(f"Flood fill transparency failed: {e}")
                        # フォールバック: 単純置換 (旧ロジック)
                        datas = img.getdata()
                        new_data = []
                        threshold = 240
                        for item in datas:
                            if item[0] > threshold and item[1] > threshold and item[2] > threshold:
                                new_data.append((255, 255, 255, 0))
                            else:
                                new_data.append(item)
                        img.putdata(new_data)

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

        # デフォルト設定
        self.current_mode = "作業中"
        self.interval_minutes = 5
        self.show_character = True
        self.remove_white_bg = False
        self.custom_image_path = ""
        
        # UI刷新に伴う新設定
        self.work_minutes = 25
        self.break_minutes = 5
        self.ai_model = "gemini-2.0-flash"
        self.window_transparency = 1.0
        self.always_on_top = True
        self.enable_notifications = True
        
        self.personality_id = "default"
        self.system_prompt = PERSONALITY_PRESETS["default"]["system_prompt"]

        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.current_mode = data.get("current_mode", "作業中")
                    self.interval_minutes = data.get("interval_minutes", 5)
                    self.show_character = data.get("show_character", True)
                    self.remove_white_bg = data.get("remove_white_bg", False)
                    self.custom_image_path = data.get("custom_image_path", "")
                    
                    self.work_minutes = data.get("work_minutes", 25)
                    self.break_minutes = data.get("break_minutes", 5)
                    self.ai_model = data.get("ai_model", "gemini-2.0-flash")
                    self.window_transparency = data.get("window_transparency", 1.0)
                    self.always_on_top = data.get("always_on_top", True)
                    self.enable_notifications = data.get("enable_notifications", True)
                    
                    # 性格プリセット読み込み
                    pid = data.get("personality_id", "default")
                    if pid in PERSONALITY_PRESETS:
                        self.personality_id = pid
                        self.system_prompt = PERSONALITY_PRESETS[pid]["system_prompt"]
                    else:
                        self.personality_id = "default"
                        self.system_prompt = PERSONALITY_PRESETS["default"]["system_prompt"]
            except: pass

    def open_settings(self):
        SettingsWindow(self)

    def apply_settings(self):
        # ウィンドウの透明度
        self.attributes("-alpha", self.window_transparency)
        # 常に手前に表示
        self.attributes("-topmost", self.always_on_top)
            
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

    def toggle_timer(self):
        if self.timer_running:
            self.timer_running = False
        else:
            if self.timer_seconds <= 0:
                self.timer_seconds = self.work_minutes * 60
            self.timer_running = True
            self.update_timer()

    def reset_timer(self):
        self.timer_running = False
        self.timer_seconds = self.work_minutes * 60
        # タイマー表示の更新が必要ならここで行うが、
        # メインループ(update_timer)が止まると更新されない可能性があるため
        # 一度だけ呼び出すか、UI更新ロジックを分離する
        # ここでは簡易的に update_timer を呼ばずに変数だけリセットし、
        # 次回起動時に反映、または update_timer が再帰的に呼ばれるか確認が必要
        # とりあえず変数をリセット。
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

    def process_with_ai(self, on_done=None):
        try:
            img = ImageGrab.grab()
            genai.configure(api_key=self.api_key)
            try:
                model = genai.GenerativeModel(self.ai_model)
            except:
                model = genai.GenerativeModel('gemini-2.0-flash')
            
            # タイマーの状態もコンテキストに追加
            # ユーザー要望: 停止中は催促しない、稼働中は鼓舞する
            if self.timer_running:
                mins = self.timer_seconds // 60
                secs = self.timer_seconds % 60
                timer_status = f"【重要】タイマー稼働中 (残り {mins}分{secs}秒)。\n指示: 残り時間を意識して、ゴールに向けて鼓舞してください。「あと少し！」等の声掛けが有効です。"
            else:
                timer_status = "【重要】タイマー停止中（フリーモード）。\n指示: ユーザーはタイマーを使わずに作業しています。タイマーの使用を強制したり、開始を促す発言は禁止です。純粋に画面の作業内容を見て評価してください。"

            # JSON出力指示 (全プリセット共通)
            json_instruction = """
【出力フォーマット】
以下のJSONフォーマットのみを出力してください。Markdownタグは不要です。
{
    "emotion": "happy", "angry", or "neutral",
    "message": "50文字以内の台詞（タメ口、感情豊かに、パートナーとして）"
}"""

            # システムプロンプトと動的コンテキストの結合
            full_prompt = f"{self.system_prompt}\n\n{json_instruction}\n\n【現在コンテキスト(自動挿入)】\nユーザーの現在の目標: {self.current_mode}\nタイマーの状態: {timer_status}"
            
            response = model.generate_content([full_prompt, img])
            text = response.text.strip()
            
            import re
            # Markdownのコードブロック記法などを削除
            text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
            
            # {} で囲まれた部分を抽出
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)
            
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                # シングルクォート等でPython辞書として返ってきた場合のフォールバック
                try:
                    import ast
                    data = ast.literal_eval(text)
                except:
                    # それでもダメならエラーログを出して終了（元の例外を再送出させてもよいが、ここではsafetyに）
                    print(f"JSON Parse Error. Raw text: {text}")
                    data = {"emotion": "neutral", "message": f"（AI応答の解析に失敗しました…）\n{text[:20]}..."}
            
            emotion = data.get("emotion", "neutral")
            message = data.get("message", "...")
            
            self.after(0, self.update_ui_reaction, emotion, message)
            self.save_log(emotion, message)
            
            if on_done:
                self.after(0, on_done, emotion, message)

        except Exception as e:
            print(f"Error: {e}")
            self.save_log("error", f"エラー発生: {e}")
            self.after(0, self.update_ui_reaction, "neutral", f"エラー: {e}")
            if on_done:
                self.after(0, on_done, "error", f"エラー: {e}")

    def update_ui_reaction(self, emotion, message):
        self.update_character_image(emotion)
        
        if self.show_character:
            self.show_bubble(message, emotion)
        else:
            try:
                # ユーザーが「非表示でも通知」を求めているかは自明だが、
                # インジケーターモードなら通知で知らせる
                
                # iconは assets/icon.ico または happy.png を使う
                icon_path = os.path.abspath("assets/icon.ico")
                if not os.path.exists(icon_path):
                    path_emo = f"assets/{emotion}.png"
                    if os.path.exists(path_emo):
                        icon_path = os.path.abspath(path_emo)
                    else:
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
