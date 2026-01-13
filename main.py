import customtkinter as ctk
from PIL import Image, ImageTk, ImageGrab, ImageDraw
import threading
import time
import os
import json
import csv
import sys
from datetime import datetime
import glob
import random

import google.generativeai as genai
import pystray
from pystray import MenuItem as item
from winotify import Notification, audio
import pygetwindow as gw
from presets import PERSONALITY_PRESETS
from locales import TRANSLATIONS

# ライブラリセットアップ
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

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

    def tr(self, key):
        lang = getattr(self.parent, "language", "ja")
        return TRANSLATIONS.get(lang, TRANSLATIONS["ja"]).get(key, key)

    def create_widgets(self):
        # UI構築時の言語を記録 (リフレッシュ判定用)
        self.current_ui_lang = getattr(self.parent, "language", "ja")

        # メインコンテナ (パディングで余白確保)
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # タブビュー
        self.tabview = ctk.CTkTabview(main_frame, width=440)
        self.tabview.pack(fill="both", expand=True)
        self.tabview.add(self.tr("tab_general"))
        self.tabview.add(self.tr("tab_ai"))
        self.tabview.add(self.tr("tab_appearance"))

        self.setup_general_tab()
        self.setup_intelligence_tab()
        self.setup_appearance_tab()

        # フッター (保存・キャンセル)
        frm_footer = ctk.CTkFrame(main_frame, fg_color="transparent", height=50)
        frm_footer.pack(fill="x", side="bottom", pady=(10, 0))
        
        btn_save_close = ctk.CTkButton(frm_footer, text=self.tr("btn_save_close"), command=self.save_and_close, 
                                 font=self.font_bold, fg_color="#4CAF50", hover_color="#45a049", height=40)
        btn_save_close.pack(side="right", padx=10)

        btn_apply = ctk.CTkButton(frm_footer, text=self.tr("btn_save"), command=self.save_only, 
                                 font=self.font_bold, fg_color="#2196F3", hover_color="#1E88E5", height=40)
        btn_apply.pack(side="right", padx=10)
        
        btn_cancel = ctk.CTkButton(frm_footer, text=self.tr("btn_cancel"), command=self.destroy,
                                   font=self.font_main, fg_color="#999999", hover_color="#777777", height=40)
        btn_cancel.pack(side="right", padx=0)

    def change_language(self, choice):
        lang_code = "en" if "English" in choice else "ja"
        self.parent.language = lang_code
        # 言語切り替え時は即座に保存して再起動を促すのが親切かもしれないが
        # ここでは変数更新のみ行い、保存時に確定させる。
        # UIリフレッシュは閉じて開くまで反映されない。

    def setup_general_tab(self):
        tab = self.tabview.tab(self.tr("tab_general"))
        
        # Language Selector
        frm_lang = ctk.CTkFrame(tab, fg_color="transparent")
        frm_lang.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(frm_lang, text=self.tr("lbl_language"), font=self.font_bold).pack(anchor="w")
        self.combo_lang = ctk.CTkComboBox(frm_lang, values=["Japanese (ja)", "English (en)"], 
                                          command=self.change_language, font=self.font_main)
        
        current_lang = getattr(self.parent, "language", "ja")
        if current_lang == "en": self.combo_lang.set("English (en)")
        else: self.combo_lang.set("Japanese (ja)")
        
        self.combo_lang.pack(fill="x", pady=(5, 0))
        
        # 目標設定
        frm_goal = ctk.CTkFrame(tab, fg_color="transparent")
        frm_goal.pack(fill="x", pady=10)
        ctk.CTkLabel(frm_goal, text=self.tr("lbl_goal"), font=self.font_bold).pack(anchor="w")
        self.entry_mode = ctk.CTkEntry(frm_goal, font=self.font_main, height=35)
        self.entry_mode.pack(fill="x", pady=(5, 0))
        if self.parent.current_mode:
            self.entry_mode.insert(0, self.parent.current_mode)
            
        # タイマー設定 (LabelFrame風)
        frm_timer = ctk.CTkFrame(tab, border_width=1, border_color="#DDDDDD", fg_color="white")
        frm_timer.pack(fill="x", pady=20, padx=5, ipady=10)
        ctk.CTkLabel(frm_timer, text=self.tr("lbl_timer_settings"), font=self.font_bold).pack(anchor="w", padx=10, pady=5)
        
        # 作業時間
        frm_work = ctk.CTkFrame(frm_timer, fg_color="transparent")
        frm_work.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frm_work, text=self.tr("lbl_work_time"), font=self.font_main, width=100).pack(side="left")
        self.slider_work = ctk.CTkSlider(frm_work, from_=1, to=60, number_of_steps=59, command=lambda v: self.lbl_work_val.configure(text=f"{int(v)}分"))
        self.slider_work.set(self.parent.work_minutes)
        self.slider_work.pack(side="left", fill="x", expand=True, padx=10)
        self.lbl_work_val = ctk.CTkLabel(frm_work, text=f"{int(self.parent.work_minutes)}分", font=self.font_main, width=40)
        self.lbl_work_val.pack(side="left")

        # 休憩時間
        frm_break = ctk.CTkFrame(frm_timer, fg_color="transparent")
        frm_break.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frm_break, text=self.tr("lbl_break_time"), font=self.font_main, width=100).pack(side="left")
        self.slider_break = ctk.CTkSlider(frm_break, from_=1, to=30, number_of_steps=29, command=lambda v: self.lbl_break_val.configure(text=f"{int(v)}分"))
        self.slider_break.set(self.parent.break_minutes)
        self.slider_break.pack(side="left", fill="x", expand=True, padx=10)
        self.lbl_break_val = ctk.CTkLabel(frm_break, text=f"{int(self.parent.break_minutes)}分", font=self.font_main, width=40)
        self.lbl_break_val.pack(side="left")
        
        # タイマー操作ボタン
        frm_btns = ctk.CTkFrame(frm_timer, fg_color="transparent")
        frm_btns.pack(fill="x", pady=(10, 5), padx=10)
        ctk.CTkButton(frm_btns, text=self.tr("btn_start"), command=lambda: self.parent.start_pomodoro(int(self.slider_work.get())), font=self.font_bold, width=80, height=35, fg_color="#4CAF50", hover_color="#388E3C").pack(side="left", padx=5, expand=True)
        ctk.CTkButton(frm_btns, text=self.tr("btn_pause"), command=self.parent.pause_pomodoro, font=self.font_bold, width=80, height=35, fg_color="#FF9800", hover_color="#F57C00").pack(side="left", padx=5, expand=True)
        ctk.CTkButton(frm_btns, text=self.tr("btn_end"), command=self.parent.reset_timer, font=self.font_main, fg_color="#D32F2F", hover_color="#B71C1C", width=70, height=35).pack(side="left", padx=5)
        
        # AIフィードバック間隔 (Legacy) also helpful
        ctk.CTkLabel(tab, text=self.tr("lbl_ai_interval_desc"), font=self.font_small, text_color="#666").pack(pady=10)
        
        self.slider_interval = ctk.CTkSlider(tab, from_=1, to=60, number_of_steps=59, command=lambda v: self.lbl_int_val.configure(text=self.tr("lbl_ai_interval").format(int(v))))
        self.slider_interval.set(self.parent.interval_minutes)
        self.slider_interval.pack(fill="x", padx=10, pady=(10,0))
        self.lbl_int_val = ctk.CTkLabel(tab, text=self.tr("lbl_ai_interval").format(int(self.parent.interval_minutes)), font=self.font_main)
        self.lbl_int_val.pack()

    def setup_intelligence_tab(self):
        tab = self.tabview.tab(self.tr("tab_ai"))
        lang = getattr(self.parent, "language", "ja")
        # プリセット辞書を取得
        presets = PERSONALITY_PRESETS.get(lang, PERSONALITY_PRESETS["ja"])
        
        # API Key Input
        ctk.CTkLabel(tab, text=self.tr("lbl_api_key"), font=("Meiryo UI", 16, "bold"), text_color="#E0E0E0").pack(pady=(15, 5))
        
        self.api_key_entry = ctk.CTkEntry(tab, width=350, placeholder_text=self.tr("placeholder_api_key"), show="*")
        self.api_key_entry.pack(pady=5)
        if hasattr(self.parent, 'api_key') and self.parent.api_key:
            self.api_key_entry.insert(0, self.parent.api_key)

        # Save Button
        ctk.CTkButton(tab, text=self.tr("btn_save_key"), command=self.save_single_api_key, 
                      font=("Meiryo UI", 11), fg_color="#009688", hover_color="#00796B", 
                      width=120, height=28).pack(pady=(2, 10))

        def open_url(event):
            import webbrowser
            webbrowser.open("https://aistudio.google.com/app/apikey")

        link = ctk.CTkLabel(tab, text=self.tr("link_get_key"), text_color="#64B5F6", cursor="hand2")
        link.pack(pady=2)
        link.bind("<Button-1>", open_url)

        def open_guide(event):
            import webbrowser
            # GitHub上のガイドページを開く
            webbrowser.open("https://github.com/Naoki-kubo64/Moti-Mate--Motivation-Mate-/blob/main/docs/api_key_guide.md")

        link_guide = ctk.CTkLabel(tab, text=self.tr("link_help_key"), text_color="#64B5F6", cursor="hand2", font=("Meiryo UI", 11, "underline"))
        link_guide.pack(pady=(0, 10))
        link_guide.bind("<Button-1>", open_guide)

        ctk.CTkLabel(tab, text=self.tr("lbl_model_settings"), font=("Meiryo UI", 14, "bold"), text_color="#E0E0E0").pack(pady=(20, 5))
        
        # 性格プリセット選択
        ctk.CTkLabel(tab, text=self.tr("lbl_personality"), font=self.font_bold).pack(anchor="w", pady=(15, 5))
        
        # ラベルとIDの対応作成
        self.preset_map = {v["label"]: k for k, v in presets.items()}
        preset_labels = list(self.preset_map.keys())
        
        # 現在のIDからラベルを逆引き
        current_id = self.parent.personality_id
        if current_id not in presets: current_id = "default"
        
        current_label = presets[current_id]["label"]
        
        self.combo_preset = ctk.CTkComboBox(tab, values=preset_labels, command=self.update_preset_description, font=self.font_main)
        self.combo_preset.set(current_label)
        self.combo_preset.pack(fill="x", pady=5)
        
        # 説明表示用ラベル
        self.lbl_preset_desc = ctk.CTkLabel(tab, text="", font=self.font_small, text_color="#555", wraplength=400, justify="left")
        self.lbl_preset_desc.pack(fill="x", pady=(0, 10))
        self.update_preset_description(current_label) # 初期表示更新

        # テスト実行
        ctk.CTkButton(tab, text=self.tr("btn_test_run"), command=self.run_test_analysis, fg_color="#9C27B0", hover_color="#7B1FA2", font=self.font_bold).pack(pady=10)
        
        # ログ表示用
        self.textbox_log = ctk.CTkTextbox(tab, height=80, font=self.font_small)
        self.textbox_log.pack(fill="x", pady=5)
        self.textbox_log.insert("0.0", self.tr("log_placeholder"))
        self.textbox_log.configure(state="disabled")

    def update_preset_description(self, choice):
        lang = getattr(self.parent, "language", "ja")
        presets = PERSONALITY_PRESETS.get(lang, PERSONALITY_PRESETS["ja"])
        
        pid = self.preset_map.get(choice, "default")
        desc = presets[pid]["description"]
        self.lbl_preset_desc.configure(text=desc)

    def setup_appearance_tab(self):
        tab = self.tabview.tab(self.tr("tab_appearance"))

        # 透明度
        ctk.CTkLabel(tab, text=self.tr("lbl_transparency"), font=self.font_bold).pack(anchor="w", pady=(10, 5))
        self.slider_alpha = ctk.CTkSlider(tab, from_=0.1, to=1.0, number_of_steps=90, command=lambda v: self.lbl_alpha.configure(text=f"{int(v*100)}%"))
        self.slider_alpha.set(self.parent.window_transparency)
        self.slider_alpha.pack(fill="x", pady=5)
        self.lbl_alpha = ctk.CTkLabel(tab, text=f"{int(self.parent.window_transparency*100)}%", font=self.font_main)
        self.lbl_alpha.pack()
        
        # スイッチ類
        self.switch_top = ctk.CTkSwitch(tab, text=self.tr("switch_param_top"), font=self.font_main)
        if self.parent.always_on_top: self.switch_top.select()
        else: self.switch_top.deselect()
        self.switch_top.pack(anchor="w", pady=10)

        self.switch_notify = ctk.CTkSwitch(tab, text=self.tr("switch_param_notify"), font=self.font_main)
        if self.parent.enable_notifications: self.switch_notify.select()
        else: self.switch_notify.deselect()
        self.switch_notify.pack(anchor="w", pady=10)
        
        self.switch_show = ctk.CTkSwitch(tab, text=self.tr("switch_param_show"), command=self.toggle_character, font=self.font_main)
        if self.parent.show_character: self.switch_show.select()
        else: self.switch_show.deselect()
        self.switch_show.pack(anchor="w", pady=10)

        # カスタム画像
        frm_img = ctk.CTkFrame(tab, border_width=1, border_color="#DDDDDD", fg_color="white")
        frm_img.pack(fill="x", pady=20, padx=5, ipady=10)
        ctk.CTkLabel(frm_img, text=self.tr("lbl_custom_image"), font=self.font_bold).pack(anchor="w", padx=10)
        
        self.switch_remove_bg = ctk.CTkSwitch(frm_img, text=self.tr("switch_param_bg"), font=self.font_main)
        if self.parent.remove_white_bg: self.switch_remove_bg.select()
        else: self.switch_remove_bg.deselect()
        self.switch_remove_bg.pack(anchor="w", padx=10, pady=5)
        
        btn_img = ctk.CTkButton(frm_img, text=self.tr("btn_select_image"), command=self.select_image, font=self.font_main, width=150)
        btn_img.pack(padx=10, pady=5, anchor="w")
        
        img_text = self.tr("lbl_no_image")
        if self.parent.custom_image_path:
            img_text = os.path.basename(self.parent.custom_image_path)
        
        self.lbl_image_path = ctk.CTkLabel(frm_img, text=img_text, font=self.font_small, text_color="#555")
        self.lbl_image_path.pack(padx=10, anchor="w")
        
        ctk.CTkButton(frm_img, text=self.tr("btn_reset_image"), command=self.reset_image, font=self.font_small, fg_color="#777", width=60, height=20).pack(padx=10, pady=5, anchor="w")

    def select_image(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif")])
        if file_path:
            self.parent.custom_image_path = file_path
            self.lbl_image_path.configure(text=os.path.basename(file_path))

    def reset_image(self):
        self.parent.custom_image_path = ""
        self.lbl_image_path.configure(text=self.tr("lbl_no_image"))
        self.parent.reset_custom_image()

    def toggle_character(self):
        pass

    def run_test_analysis(self):
        # 設定を一時保存的に適用してテスト
        self.parent.current_mode = self.entry_mode.get().strip()
        self.parent.ai_model = "gemini-2.0-flash"
        
        # 選択中のプリセットからプロンプトを取得して一時適用
        pid = self.preset_map.get(self.combo_preset.get(), "default")
        
        lang = getattr(self.parent, "language", "ja")
        presets = PERSONALITY_PRESETS.get(lang, PERSONALITY_PRESETS["ja"])
        
        self.parent.system_prompt = presets.get(pid, presets["default"])["system_prompt"]
        
        def on_complete(emotion, message):
            self.textbox_log.configure(state="normal")
            ts = datetime.now().strftime('%H:%M:%S')
            self.textbox_log.insert("0.0", f"[{ts}] ({emotion})\n{message}\n{'-'*30}\n")
            self.textbox_log.configure(state="disabled")

        threading.Thread(target=self.parent.process_with_ai, args=(on_complete,), daemon=True).start()
        
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("0.0", f"[{datetime.now().strftime('%H:%M:%S')}] テストリクエスト中... ({pid})\n")
        self.textbox_log.configure(state="disabled")

    def save_single_api_key(self):
        new_key = self.api_key_entry.get().strip()
        self.parent.api_key = new_key
        
        # 現在の設定をすべて取得して保存
        try:
            settings = {}
            if os.path.exists("settings.json"):
                with open("settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
            
            settings["api_key"] = new_key
            
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            # 保存完了通知
            self.focus() # 枠にフォーカス戻す
            
        except Exception as e:
            print(f"Key save error: {e}")

    
    def refresh_ui(self):
        # 既存のウィジェットを全て削除
        for widget in self.winfo_children():
            widget.destroy()
        
        # UI再構築
        self.create_widgets()

    def save_settings(self, close=True):
        # API Key
        self.parent.api_key = self.api_key_entry.get().strip()

        self.parent.current_mode = self.entry_mode.get().strip()
        self.parent.work_minutes = int(self.slider_work.get())
        self.parent.break_minutes = int(self.slider_break.get())
        self.parent.interval_minutes = int(self.slider_interval.get())
        
        self.parent.ai_model = "gemini-2.0-flash"
        
        # プリセットIDを保存
        pid = self.preset_map.get(self.combo_preset.get(), "default")
        self.parent.personality_id = pid
        
        lang = self.parent.language
        presets = PERSONALITY_PRESETS.get(lang, PERSONALITY_PRESETS["ja"])
        if pid not in presets: pid = "default"
        self.parent.system_prompt = presets[pid]["system_prompt"]
        
        self.parent.window_transparency = float(self.slider_alpha.get())
        self.parent.always_on_top = bool(self.switch_top.get())
        self.parent.enable_notifications = bool(self.switch_notify.get())
        self.parent.show_character = bool(self.switch_show.get())
        self.parent.remove_white_bg = bool(self.switch_remove_bg.get())

        settings = {
            "api_key": self.parent.api_key,
            "language": self.parent.language,
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
        
        if close:
            self.destroy()
        else:
            # 言語が変更されていたらUIをリフレッシュ
            # current_ui_lang は create_widgets で設定される
            current_ui_lang = getattr(self, "current_ui_lang", "ja")
            if current_ui_lang != self.parent.language:
                self.refresh_ui()

    def save_and_close(self):
        self.save_settings(close=True)
        
    def save_only(self):
        self.save_settings(close=False)

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
        self.timer_mode = "work"
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

    def tr(self, key):
        lang = getattr(self, "language", "ja")
        return TRANSLATIONS.get(lang, TRANSLATIONS["ja"]).get(key, key)
    
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

    def start_pomodoro(self, minutes, mode="work"):
        self.timer_mode = mode
        
        # 既存タイマーが走ってない、あるいはゼロの場合にセット (Breakへの切り替え時は走っていても強制セットしたいので条件調整)
        if (not self.timer_running) or mode == "break":
            self.timer_seconds = minutes * 60
            self.timer_running = True
            
            if self.timer_widget is None or not self.timer_widget.winfo_exists():
                self.timer_widget = TimerDisplay(self.container)
                # タイマーはマスコットの頭上へ
                tx = self.mascot_x + 40
                ty = self.mascot_y - 30
                self.timer_widget.place(x=tx, y=ty)
                
            self.timer_widget.lift()
            self.update_timer()
            
            # 開始時メッセージ
            if mode == "work":
                msg = self.tr("msg_work_start")
                self.show_bubble(msg, "happy")
                self.update_character_image("happy")
            else:
                msg = self.tr("msg_rest_start")
                self.show_bubble(msg, "neutral")
                self.update_character_image("neutral")

    def pause_pomodoro(self):
        self.timer_running = False
        self.show_bubble("一時停止中...", "neutral")

    def reset_pomodoro(self):
        self.timer_running = False
        self.timer_seconds = 0
        if self.timer_widget:
            self.timer_widget.place_forget()
        # 吹き出しも消す
        if self.current_bubble and self.current_bubble.winfo_exists():
            self.current_bubble.destroy()
            self.current_bubble = None

    def start_monitoring(self):
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitor_thread.start()

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
                # モードによる色分け
                if self.timer_mode == "break":
                    color = "#69F0AE" # パステルグリーン (休憩)
                elif self.timer_seconds < 60: 
                    color = "#FF5252" # 赤 (作業ラスト1分)
                
                self.timer_widget.update_time(time_str, color)
            self.after(1000, self.update_timer)
        else:
            # タイマー終了時の処理
            
            # Work -> Break (自動移行)
            if self.timer_mode == "work":
                # 先に通知を出してからタイマー切り替え
                msg = self.tr("msg_break_start")
                if self.show_character:
                    self.show_bubble(msg, "happy")
                else:
                    self.send_notification("Break Started", msg)
                
                self.update_character_image("happy")
                
                # 休憩タイマー開始
                self.start_pomodoro(self.break_minutes, mode="break")

            # Break -> Finish (停止)
            else:
                self.timer_running = False
                if self.timer_widget and self.timer_widget.winfo_exists():
                    self.timer_widget.update_time("00:00", "white")
                
                self.update_character_image("happy")
                
                msg = self.tr("msg_break_finished")
                if self.show_character:
                    self.show_bubble(msg, "happy")
                else:
                    self.send_notification("Break Finished", msg)
    
    def send_notification(self, title, msg):
        try:
            icon_path = resource_path("assets/icon.ico")
            if not os.path.exists(icon_path):
                icon_path = resource_path("assets/happy.png")
            
            toast = VerifyNotification(
                app_id="Moti-Mate",
                title=title,
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
            path = resource_path(f"assets/{emotion}.png")
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
        # 1. Initialize Default Settings
        self.api_key = ""
        self.current_mode = "作業中"
        self.language = "ja"
        self.interval_minutes = 5
        self.show_character = True
        self.remove_white_bg = False
        self.custom_image_path = ""
        self.work_minutes = 25
        self.break_minutes = 5
        self.long_break_minutes = 15
        self.ai_model = "gemini-1.5-flash"
        self.window_transparency = 1.0
        self.always_on_top = True
        self.enable_notifications = True
        self.personality_id = "default"
        
        # Initial system prompt (fallback)
        presets_fallback = PERSONALITY_PRESETS.get(self.language, PERSONALITY_PRESETS["ja"])
        self.system_prompt = presets_fallback["default"]["system_prompt"]
        
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    
                    self.api_key = settings.get("api_key", self.api_key)
                    self.language = settings.get("language", self.language)
                    
                    self.work_minutes = settings.get("work_minutes", self.work_minutes)
                    self.break_minutes = settings.get("break_minutes", self.break_minutes)
                    self.long_break_minutes = settings.get("long_break_minutes", self.long_break_minutes)
                    self.ai_model = settings.get("ai_model", self.ai_model)
                    self.remove_white_bg = settings.get("remove_white_bg", self.remove_white_bg)
                    self.show_character = settings.get("show_character", self.show_character)
                    self.custom_image_path = settings.get("custom_image_path", self.custom_image_path)
                    self.interval_minutes = settings.get("interval_minutes", self.interval_minutes)
                    self.window_transparency = settings.get("window_transparency", self.window_transparency)
                    self.always_on_top = settings.get("always_on_top", self.always_on_top)
                    self.enable_notifications = settings.get("enable_notifications", self.enable_notifications)
                    self.personality_id = settings.get("personality_id", self.personality_id)
                    
                    # Update system prompt based on loaded language/personality
                    presets = PERSONALITY_PRESETS.get(self.language, PERSONALITY_PRESETS["ja"])
                    
                    # Validate personality_id exists in the current language preset
                    if self.personality_id not in presets:
                        self.personality_id = "default"
                        
                    default_prompt = presets[self.personality_id]["system_prompt"]
                    self.system_prompt = settings.get("system_prompt", default_prompt)
                    
        except Exception as e:
            print(f"Setting load error: {e}")



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
            
            # Load待ちなどは不要になったので即座に実行
            self.process_with_ai()

    def process_with_ai(self, on_done=None):
        if not self.api_key:
            self.after(0, self.update_ui_reaction, "neutral", "設定からAPIキーを入れてね！")
            return

        try:
            # アクティブウィンドウ取得
            active_window_title = "不明"
            try:
                window = gw.getActiveWindow()
                if window:
                    active_window_title = window.title.strip()
            except: pass

            # 画面キャプチャ (Vision復活)
            img = ImageGrab.grab()

            genai.configure(api_key=self.api_key)
            try:
                model = genai.GenerativeModel(self.ai_model)
            except:
                model = genai.GenerativeModel('gemini-1.5-flash')

            # コンテキスト作成
            if self.timer_running:
                mins = self.timer_seconds // 60
                secs = self.timer_seconds % 60
                timer_status = f"【現在: タイマー稼働中】残り {mins}分{secs}秒。"
            else:
                timer_status = "【現在: タイマー停止中】フリーモード。"

            # プロンプト構築
            system_msg = (
                f"{self.system_prompt}\n\n"
                f"【現在状況】\n"
                f"目標: {self.current_mode}\n"
                f"アクティブウィンドウ: {active_window_title}\n"
                f"タイマー: {timer_status}\n\n"
                "あなたの役割: 上記の状況と添付画像を元に、ユーザーに声をかけてください。\n"
                "・目標と関係ない娯楽(YouTube等)をしていたら、厳しく叱ってください(angry)。\n"
                "・作業中なら、褒めたり励ましてください(happy)。\n"
            )
            
            json_instruction = """
出力は以下のJSON形式のみ:
{
    "emotion": "happy", "angry", or "neutral",
    "message": "短いセリフ(50文字以内)"
}"""
            full_prompt = f"{system_msg}\n{json_instruction}"

            response = model.generate_content([full_prompt, img])
            text = response.text.strip()
            
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)
            
            try:
                data = json.loads(text)
            except:
                data = {"emotion": "neutral", "message": text[:50]}

            emotion = data.get("emotion", "neutral")
            message = data.get("message", "...")
            
            self.after(0, self.update_ui_reaction, emotion, message)
            self.save_log(emotion, message)
            if on_done:
                self.after(0, on_done, emotion, message)

        except Exception as e:
            print(f"GenAI Error: {e}")
            self.save_log("error", str(e))
            if "403" in str(e):
                self.after(0, self.update_ui_reaction, "neutral", "APIキーエラー(403)。設定を確認してね")

    def update_ui_reaction(self, emotion, message):
        self.update_character_image(emotion)
        
        if self.show_character:
            self.show_bubble(message, emotion)
        else:
            try:
                # ユーザーが「非表示でも通知」を求めているかは自明だが、
                # インジケーターモードなら通知で知らせる
                
                # iconは assets/icon.ico または happy.png を使う
                icon_path = resource_path("assets/icon.ico")
                if not os.path.exists(icon_path):
                    path_emo = resource_path(f"assets/{emotion}.png")
                    if os.path.exists(path_emo):
                        icon_path = path_emo
                    else:
                        icon_path = resource_path("assets/neutral.png")
                
                toast = Notification(
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
    try:
        # User requested ICO preference
        icon_path = resource_path("assets/icon.ico")
        if not os.path.exists(icon_path):
            icon_path = resource_path("assets/icon.png")
            
        image = Image.open(icon_path)
    except Exception as e:
        print(f"Tray icon load failed: {e}")
        image = Image.new('RGB', (64, 64), color = (73, 109, 137))
    
    def tr(key):
        lang = getattr(app, "language", "ja")
        return TRANSLATIONS.get(lang, TRANSLATIONS["ja"]).get(key, key)

    def on_start(icon, item):
        # メインスレッドで実行
        app.after(0, lambda: app.start_pomodoro(app.work_minutes))

    def on_stop(icon, item):
        app.after(0, app.pause_pomodoro)

    def on_end(icon, item):
        app.after(0, app.reset_timer)

    def on_settings(icon, item):
        app.after(0, app.open_settings)

    def on_exit(icon, item):
        icon.stop()
        app.after(0, app.quit_app)

    # Windowsの仕様上、左クリックでメニューを出すのは標準外だが、
    # default=Trueを設定することで左クリック(またはダブルクリック)で「設定」を開くようにする
    menu = pystray.Menu(
        item(tr('tray_start'), on_start),
        item(tr('tray_pause'), on_stop),
        item(tr('tray_end'), on_end),
        pystray.Menu.SEPARATOR,
        item(tr('tray_settings'), on_settings, default=True),
        item(tr('tray_exit'), on_exit)
    )

    icon = pystray.Icon("MotiMate", image, "Motivation Mate", menu)
    icon.run()

if __name__ == "__main__":
    app = MascotApp()
    tray_thread = threading.Thread(target=run_tray, args=(app,), daemon=True)
    tray_thread.start()
    app.mainloop()
