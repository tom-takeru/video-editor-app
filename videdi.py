import os
import sys
import subprocess
import threading
import io
import shutil
import re
import tkinter as tk
from tkinter import font
from tkinter import filedialog
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

# 自作モジュール
import video_audio_player
import videdi_log
import videdi_util
import videdi_colorchooser
import questionnaire


# 出力のエンコードをUTF-8に設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    FFMPEG_PATH = sys._MEIPASS + '/ffmpeg'
    FFPROBE_PATH = sys._MEIPASS + '/ffprobe'
except AttributeError:
    FFMPEG_PATH = '/usr/local/bin/ffmpeg'
    FFPROBE_PATH = '/usr/local/bin/ffprobe'

WINDOW_WIDTH = 700
WINDOW_HEIGHT = 600


class Videdi:

    def __init__(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT):
        # tk.Tkクラスをインスタンス化
        self.main_window = tk.Tk()
        
        # ウィンドウのタイトルを設定
        self.main_window.title('VIDEDI')
        
        # ウィンドウの大きさ
        self.window_width = width
        self.window_height = height
        
        # ウィンドウの位置(中心)
        # self.window_pos_x = (self.main_window.winfo_screenwidth() - self.window_width) // 2
        # self.window_pos_y = (self.main_window.winfo_screenheight() - self.window_height) // 2
        # ウィンドウの位置(左上)
        self.window_pos_x = 0
        self.window_pos_y = 0
        
        # ウィンドウの大きさと位置を設定
        self.main_window.geometry(str(self.window_width) + 'x' + str(self.window_height)
                           + '+' + str(self.window_pos_x) + '+' + str(self.window_pos_y))
    
        # ウィンドウの大きさを固定
        self.main_window.resizable(False, False)
        
        # ウィンドウの背景の色を設定
        self.window_bg = '#ececec'
        self.main_window.configure(bg=self.window_bg)

        # ウィンドウの枠を指定
        self.main_window.configure(borderwidth=10, relief='ridge')

        # フォントを指定
        bold_font = font.Font(self.main_window, size=16, weight='bold')
        button_font = font.Font(self.main_window, size=14)
        self.button_background = self.window_bg

        # タイトルラベル
        widget_pos_y = 0
        widget_height = 100
        title_font = font.Font(self.main_window, family='impact', size=widget_height, weight='bold')
        self.title_lab = tk.Label(text='VIDEDI', font=title_font, foreground='lightgray', bg='black')
        self.title_lab.place(x=0, y=widget_pos_y, relwidth=1.0, height=widget_height)

        # 現在選択中フォルダラベル
        widget_pos_y += widget_height
        widget_height = 20

        # 処理するフォルダを指定
        # self.process_dir = ''
        self.process_dir = '/Users/takeruyoshimura/Documents/test2/' #テスト用に初期値を設定
        self.dir_name_min = 40
        self.current_dir_var = tk.StringVar()
        self.current_dir_var.set('編集したい動画のあるフォルダを選択してください')
        self.current_dir_lab = tk.Label(textvariable=self.current_dir_var, font=bold_font, bg=self.window_bg)
        self.current_dir_lab.place(x=0, y=widget_pos_y, relwidth=1.0, height=widget_height)

        # フォルダ選択ボタン
        # self.dir_is_available = False
        self.dir_is_available = True #テスト用に初期値を設定
        pos_y = widget_pos_y + widget_height
        self.sd_button_height = 25
        self.sd_button_relwidth = 0.2
        self.select_dir_button = tk.Button(text='フォルダの選択', command=self.select_dir, font=button_font,
                                           highlightbackground=self.window_bg, fg='black', highlightthickness=0)
        self.select_dir_button.place(relx=(1 - self.sd_button_relwidth) / 2, y=pos_y,
                                     relwidth=self.sd_button_relwidth, height=self.sd_button_height)
        # スクロール式のログラベル
        self.scroll_pos_y = widget_pos_y + self.sd_button_height + 30
        self.scroll_height = 200
        self.log_max = 100
        self.log_frame = videdi_log.LogFrame(master=self.main_window, log_max=self.log_max, bg=self.window_bg,
                                             width=self.window_width, height=self.window_height)
        self.log_frame.place(x=0, y=self.scroll_pos_y, relwidth=1.0, height=self.scroll_height)
        self.log_frame.interior.bind('<ButtonPress-1>', self.move_start)
        self.log_frame.interior.bind('<B1-Motion>', self.move_move)
        self.log_frame.interior.bind('<MouseWheel>', self.mouse_y_scroll)
        # ログリセットボタン
        self.lr_button_relx = 0.85
        self.lr_button_pos_y = widget_pos_y + 15
        self.lr_button_height = 25
        self.lr_button_relwidth = 0.15
        self.log_reset_button = tk.Button(text='ログリセット', command=self.log_frame.reset_all_logs,
                                          font=button_font,
                                          highlightbackground=self.window_bg, fg='black', highlightthickness=0)
        self.log_reset_button.place(relx=self.lr_button_relx, y=self.lr_button_pos_y,
                                    relwidth=self.lr_button_relwidth, height=self.lr_button_height)
        #アンケートボタン
        self.questionnaire_button = questionnaire.Questionnaire(self.main_window)
        self.questionnaire_button.place(relx=0, y=self.lr_button_pos_y)
        # 処理選択ラベル
        self.run_choices_pos_y = self.scroll_pos_y + self.scroll_height + 10
        self.run_choices_lab = tk.Label(text='処理内容', font=bold_font)
        self.run_choices_lab.place(relx=0.05, y=self.run_choices_pos_y)

        # 自動ジャンプカットチェックボックス
        self.jumpcut_bln = tk.BooleanVar()
        self.jumpcut_bln.set(True)
        self.jumpcut_chk = tk.Checkbutton(self.main_window, variable=self.jumpcut_bln, text='自動ジャンプカット', command=self.set_options)
        self.jumpcut_chk.place(relx=0.2, y=self.run_choices_pos_y)

        # 字幕修正チェックボックス
        self.subtitle_bln = tk.BooleanVar()
        self.subtitle_bln.set(True)
        self.subtitle_chk = tk.Checkbutton(self.main_window, variable=self.subtitle_bln, text='自動字幕付け', command=self.set_options)
        self.subtitle_chk.place(relx=0.45, y=self.run_choices_pos_y)

        # オプションの列
        self.option_lien1_pos_y = self.run_choices_pos_y + 30
        self.option_lien2_pos_y = self.option_lien1_pos_y + 30
        self.option_lien3_pos_y = self.option_lien2_pos_y + 30

        # オプション選択ラベル
        self.option_lab = tk.Label(text='オプション', font=bold_font)
        self.option_lab.place(relx=0.05, y=self.option_lien1_pos_y)

        # 修正チェックボックス
        self.fix_bln = tk.BooleanVar()
        self.fix_bln.set(True)
        self.fix_chk = tk.Checkbutton(self.main_window, variable=self.fix_bln, text='修正')
        self.fix_chk.place(relx=0.2, y=self.option_lien1_pos_y)

        # 有音部分の最小時間を設定(単位:秒)
        self.min_time_lab = tk.Label(self.main_window, text='有音部分の最小時間')
        self.min_time_unit_lab = tk.Label(self.main_window, text='(秒)')
        self.min_time = tk.StringVar()
        self.min_time.set('0.5')
        self.min_time_spinbox = tk.Spinbox(self.main_window, format='%1.1f', textvariable=self.min_time, from_=0, to=1.0,
                                           increment=0.1, state='readonly')

        # 有音部分の前後の余裕を設定(単位:秒)
        self.margin_time_lab = tk.Label(text='有音部分の前後の余裕')
        self.margin_time_unit_lab = tk.Label(self.main_window, text='(秒)')
        self.margin_time = tk.StringVar()
        self.margin_time.set('0.1')
        self.margin_time_spinbox = tk.Spinbox(self.main_window, format='%1.2f', textvariable=self.margin_time, from_=0, to=1.0,
                                              increment=0.01, state='readonly')
        # 字幕の色選択ボタン
        self.sutitle_font_color_lab = tk.Label(self.main_window, text='字幕の色')
        self.sutitle_font_color_chooser = videdi_colorchooser.ColorSelectButton(self.main_window)
        # 字幕の大きさ選択ボタン
        self.sutitle_font_size_lab = tk.Label(self.main_window, text='字幕の大きさ')
        self.font_size = tk.StringVar()
        self.font_size.set('15')
        self.sutitle_font_size_spinbox = tk.Spinbox(self.main_window, format='%2.f', textvariable=self.font_size, from_=5,
                                                    to=30, increment=1, state='readonly', width=3)
        # 実行ボタン
        self.run_button_pos_y = self.option_lien3_pos_y + 40
        self.run_button_height = 25
        self.run_button_relwidth = 0.1
        self.run_button = tk.Button(text='実行', state='disable', command=self.run_button_process, font=button_font,
                                    highlightbackground=self.window_bg, fg='red',
                                    highlightthickness=0)
        self.run_button.place(relx=(1-self.run_button_relwidth)/2, y=self.run_button_pos_y,
                              relwidth=self.run_button_relwidth, height=self.run_button_height)
        self.thread_event = None
        self.next_action = ''
        self.decided = False
        self.player = video_audio_player.Video_Audio_player()
        self.cut_bln = tk.BooleanVar()

        # オプションをセット
        self.set_options()

        # メインループでイベント待ち
        if __name__ == '__main__':
            self.main_window.mainloop()

    def move_start(self, event):
        self.log_frame.canvas.scan_mark(event.x, event.y)

    def move_move(self, event):
        self.log_frame.canvas.scan_dragto(event.x, event.y, gain=1)

    def mouse_y_scroll(self, event):
        if event.delta > 0:
            self.log_frame.canvas.yview_scroll(-1, 'units')
        elif event.delta < 0:
            self.log_frame.canvas.yview_scroll(1, 'units')

    # フォルダ選択処理
    def select_dir(self):
        # 現在選択中のフォルダがある場合はそこから探す
        current_dir_path = self.process_dir
        if len(current_dir_path) == 0:
            idir = os.path.abspath(os.path.dirname(__file__))
        else:
            idir = os.path.abspath(os.path.dirname(current_dir_path))
        # フォルダ選択済みフラグをおろす
        self.dir_is_available = False
        # 実行系ボタン無効化
        self.disable_all_button()
        # フォルダを選択する
        self.process_dir = filedialog.askdirectory(initialdir=idir)
        # フォルダが選択されなかった場合、直前に選択していたフォルダを選択
        if len(self.process_dir) == 0:
            self.process_dir = current_dir_path[0:-1]
        # 選択されたフォルダが存在する場合
        if os.path.exists(self.process_dir):
            self.process_dir += '/'
            # フォルダの絶対パスが設定より長い場合
            if len(self.process_dir) > self.dir_name_min:
                # 表示するフォルダ名を絶対パスのフォルダ名の部分だけにする
                dir_name = self.process_dir.split('/')[-2]
            # フォルダの絶対パスが設定より短い場合
            else:
                # 表示するフォルダ名を絶対パスにする
                dir_name = self.process_dir
            # 選択されたフォルダの中に動画がある場合
            if len(videdi_util.search_videos(self.process_dir)) != 0:
                self.current_dir_var.set(dir_name + 'フォルダを選択中')
                # フォルダ選択済みフラグを立てる
                self.dir_is_available = True
                # 処理のボタン有効化
                self.enable_all_button()
                # オプション表示
                self.set_options()
                return
            # 選択されたフォルダ内に動画がない場合
            else:
                self.current_dir_var.set(dir_name + 'フォルダには処理できる動画ファイルがありません。')
        # 選択されたフォルダが存在しない場合
        else:
            self.current_dir_var.set('編集したい動画のあるフォルダを選択してください')
        self.select_dir_button.configure(state='normal')
        self.log_reset_button.configure(state='normal')
        return

    # ボタン無効化
    def disable_all_button(self):
        self.select_dir_button.configure(state='disabled')
        self.log_reset_button.configure(state='disabled')
        self.jumpcut_chk.configure(state='disable')
        self.subtitle_chk.configure(state='disable')
        self.fix_chk.configure(state='disable')
        self.min_time_lab.configure(foreground='#aaa')
        self.min_time_spinbox.configure(state='disable')
        self.min_time_unit_lab.configure(foreground='#aaa')
        self.margin_time_lab.configure(foreground='#aaa')
        self.margin_time_spinbox.configure(state='disable')
        self.margin_time_unit_lab.configure(foreground='#aaa')
        self.sutitle_font_color_lab.configure(foreground='#aaa')
        self.sutitle_font_color_chooser.configure(state='disable')
        self.sutitle_font_size_lab.configure(foreground='#aaa')
        self.sutitle_font_size_spinbox.configure(state='disable')
        self.run_button.configure(state='disable')

    # ボタン有効化
    def enable_all_button(self):
        self.select_dir_button.configure(state='normal')
        self.log_reset_button.configure(state='normal')
        self.jumpcut_chk.configure(state='normal')
        self.subtitle_chk.configure(state='normal')
        self.fix_chk.configure(state='normal')
        self.min_time_lab.configure(foreground='black')
        self.min_time_spinbox.configure(state='readonly')
        self.min_time_unit_lab.configure(foreground='black')
        self.margin_time_lab.configure(foreground='black')
        self.margin_time_spinbox.configure(state='readonly')
        self.margin_time_unit_lab.configure(foreground='black')
        self.sutitle_font_color_lab.configure(foreground='black')
        self.sutitle_font_color_chooser.configure(state='normal')
        self.sutitle_font_size_lab.configure(foreground='black')
        self.sutitle_font_size_spinbox.configure(state='readonly')
        self.run_button.configure(state='normal')

    # 処理の内容からオプションを表示
    def set_options(self, *args):
        # 動画が入ったフォルダが選択されていたら、ウィジェットを有効化する
        widget_state = 'disable'
        spinbox_state = 'disable'
        text_color = '#aaa'
        run_button_state = 'disable'
        if self.dir_is_available:
            widget_state = 'normal'
            spinbox_state = 'readonly'
            text_color = 'black'
            run_button_state = 'normal'
        # 処理のチェックボタンをセット
        self.jumpcut_chk.configure(state=widget_state)
        self.subtitle_chk.configure(state=widget_state)
        # オプションのチェックボタンをセット
        self.fix_chk.configure(state=widget_state)
        # ボタンをセット
        self.sutitle_font_color_chooser.configure(state=run_button_state)
        # ジャンプカットのオプションをセット
        self.min_time_lab.place(relx=0.2, y=self.option_lien2_pos_y)
        self.min_time_spinbox.place(relx=0.385, y=self.option_lien2_pos_y, width=60)
        self.min_time_unit_lab.place(relx=0.47, y=self.option_lien2_pos_y)
        self.min_time_lab.configure(foreground=text_color)
        self.min_time_spinbox.configure(state=spinbox_state)
        self.min_time_unit_lab.configure(foreground=text_color)
        self.margin_time_lab.place(relx=0.2, y=self.option_lien3_pos_y)
        self.margin_time_spinbox.place(relx=0.385, y=self.option_lien3_pos_y, width=60)
        self.margin_time_unit_lab.place(relx=0.47, y=self.option_lien3_pos_y)
        self.margin_time_lab.configure(foreground=text_color)
        self.margin_time_spinbox.configure(state=spinbox_state)
        self.margin_time_unit_lab.configure(foreground=text_color)
        self.sutitle_font_size_lab.place(relx=0.52, y=self.option_lien2_pos_y)
        self.sutitle_font_size_spinbox.place(relx=0.64, y=self.option_lien2_pos_y)
        self.sutitle_font_size_lab.configure(foreground=text_color)
        self.sutitle_font_size_spinbox.configure(state=spinbox_state)
        self.sutitle_font_color_lab.place(relx=0.55, y=self.option_lien3_pos_y)
        self.sutitle_font_color_chooser.place(relx=0.64, y=self.option_lien3_pos_y)
        self.sutitle_font_color_lab.configure(foreground=text_color)
        self.sutitle_font_color_chooser.configure(state=widget_state)
        # 実行ボタンをセット
        self.run_button.configure(state=run_button_state)
        return

    # 処理実行ボタンの処理
    def run_button_process(self):
        if not (self.jumpcut_bln.get() or self.subtitle_bln.get()):
            self.log_frame.set_log('処理を選択してください')
        else:
            # ボタン無効化
            self.disable_all_button()
            # スレッディング処理
            thread = threading.Thread(target=self.edit_video)
            thread.start()
        return

    # ジャンプカットして字幕を付ける処理
    def edit_video(self):
        # 音声テキスト作成開始ログ
        self.log_frame.set_big_log(self.process_dir.split('/')[-2] + 'フォルダ内の動画を編集します')
        video_list = videdi_util.search_videos(self.process_dir)
        try:
            shutil.rmtree(self.process_dir + '.tmp/')
        except OSError:
            pass
        os.mkdir(self.process_dir + '.tmp/')
        for i, video in enumerate(video_list):
            video_name = os.path.split(video)[1]
            self.log_frame.set_log(video_name + 'の無音部分を検知します')
            cut_sections = videdi_util.silence_sections(video)
            if len(cut_sections) == 0:
                self.log_frame.set_log('無音部分がありませんでした')
                continue
            video_sections = videdi_util.video_sections(cut_sections, video)
            video_sections = videdi_util.arrange_sections(video_sections, float(self.min_time.get()),
                                                          float(self.margin_time.get()))
            video_sections = videdi_util.all_sections(video_sections, video)
            self.log_frame.set_log(video_name + 'をカットします')
            jumpcut_dir = self.process_dir + '.tmp/.tmp_' + os.path.splitext(video_name)[0] + '_jumpcut/'
            os.mkdir(jumpcut_dir)
            text_dir = self.process_dir + '.tmp/.tmp_' + video_name.split('.')[0] + '_text/'
            os.mkdir(text_dir)
            srt_dir = self.process_dir + '.tmp/.tmp_' + video_name.split('.')[0] + '_srt/'
            os.mkdir(srt_dir)
            subtitle_dir = self.process_dir + '.tmp/.tmp_' + video_name.split('.')[0] + '_subtitle/'
            os.mkdir(subtitle_dir)
            self.divide_video_into_sections(video, video_sections, jumpcut_dir)
            jumpcut_video_list = videdi_util.search_videos(jumpcut_dir)
            digit = len(str(len(jumpcut_video_list)))
            if self.subtitle_bln.get():
                # 自動字幕付けが選択されていた場合
                self.log_frame.set_log(video_name + 'の音声部分をテキスト化します')
                for j, jumpcut_video in enumerate(jumpcut_video_list):
                    jumpcut_video_name = os.path.split(jumpcut_video)[1]
                    text_file = text_dir + os.path.splitext(jumpcut_video_name)[0] + '.txt'
                    if videdi_util.speech_recognize(jumpcut_video, text_file):
                        # インターネット接続あり
                        self.log_frame.set_progress_log('音声テキスト化', j + 1, len(jumpcut_video_list))
                        continue
                    else:
                        # インターネット接続なし
                        with open(text_file, mode='w', encoding='utf8') as f:
                            f.write('')
                        self.log_frame.set_log('インターネット接続がないため、音声を認識をスキップします')
                self.log_frame.set_log(video_name + 'の字幕を動画に焼き付けます')
            else:
                # 自動字幕付けが選択されていない場合
                for jumpcut_video in jumpcut_video_list:
                    jumpcut_video_name = os.path.split(jumpcut_video)[1]
                    text_file = os.path.splitext(jumpcut_video_name)[0] + '.txt'
                    with open(text_dir + text_file, mode='w', encoding='utf8') as f:
                        f.write('')
            subtitle_colors = []
            subtitle_sizes = []
            for j in range(len(jumpcut_video_list)):
                jumpcut_video_file = os.path.split(jumpcut_video_list[j])[1]
                text_file = text_dir + os.path.splitext(jumpcut_video_file)[0] + '.txt'
                srt_file = videdi_util.make_srt(srt_dir + os.path.splitext(jumpcut_video_file)[0] + '.srt',
                                                [text_file, ],
                                                [[0.0, video_sections[j][1]
                                                  - video_sections[j][0]], ])
                with open(text_file, mode='r', encoding='utf8') as f:
                    text = f.read()
                if text == '':
                    shutil.copy(jumpcut_video_list[j], subtitle_dir + os.path.splitext(jumpcut_video_file)[0]
                                + '_subtitle.mp4')
                    self.log_frame.set_progress_log('字幕付け', j + 1, len(jumpcut_video_list))
                else:
                    videdi_util.print_subtitle(jumpcut_video_list[j], srt_file, self.font_size.get(), self.sutitle_font_color_chooser.bg_color, subtitle_dir
                                               + os.path.splitext(jumpcut_video_file)[0] + '_subtitle.mp4')
                    self.log_frame.set_progress_log('字幕付け', j + 1, len(jumpcut_video_list))
                subtitle_colors.append(self.sutitle_font_color_chooser.bg_color)
                subtitle_sizes.append(self.font_size.get())
            if not self.jumpcut_bln.get():
                # 自動ジャンプカットが選択されていない場合
                for j in range(len(video_sections)):
                    video_sections [j][2] = False
            if self.fix_bln.get():
                fix_window = tk.Toplevel()
                fix_window.configure(borderwidth=10, relief=tk.RIDGE)
                fix_window.geometry(str(WINDOW_WIDTH+100) + 'x' + str(WINDOW_HEIGHT+100)
                                    + '+' + str(self.window_width) + '+0')
                fix_window.resizable(False, False)
                fix_window.bind('<Key>', self.fix_win_keyboard)
                fix_window.title('修正')
                frame = tk.Frame(fix_window)
                frame.pack()
                line1_rel_y = 0.72
                line2_rel_y = 0.78
                line3_rel_y = 0.82
                line4_rel_y = 0.86
                last_line_rel_y = 0.96
                scale_var_relx = 0.02
                scale_var_relwidth = 0.96
                button_height = 25
                button_relwidth = 0.06
                # 再生バー
                video_scale_var = tk.DoubleVar()
                fix_window.video_scale = tk.Scale(fix_window, variable=video_scale_var, orient=tk.HORIZONTAL,
                                                  from_=1, to=len(jumpcut_video_list), activebackground='red', width=10,
                                                  bd=0, cursor="sb_h_double_arrow")
                fix_window.video_scale.place(relx=scale_var_relx, rely=line1_rel_y, relwidth=scale_var_relwidth)
                # 再生ボタン
                fix_window.preview_button = tk.Button(fix_window, text='▶︎', command=self.fix_win_preview,
                                                      highlightbackground=self.window_bg, fg='red',
                                                      font=('', 27),
                                                      highlightthickness=0)
                fix_window.preview_button.place(relx=0.47, rely=line2_rel_y, relwidth=button_relwidth,
                                                height=button_height)
                # 前へボタン
                fix_window.back_button = tk.Button(fix_window, text='＜', command=self.fix_win_back, font=('', 27),
                                                   highlightbackground=self.window_bg, fg='black',
                                                   highlightthickness=0)
                fix_window.back_button.place(relx=0.39, rely=line2_rel_y, relwidth=button_relwidth,
                                             height=button_height)
                # 次へボタン
                fix_window.go_button = tk.Button(fix_window, text='＞', command=self.fix_win_go, font=('', 27),
                                                 highlightbackground=self.window_bg, fg='black',
                                                 highlightthickness=0)
                fix_window.go_button.place(relx=0.55, rely=line2_rel_y, relwidth=button_relwidth,
                                           height=button_height)
                # カット選択チェックボックス
                fix_window.cut_chk = tk.Checkbutton(fix_window, variable=self.cut_bln, text='カットする')
                fix_window.cut_chk.place(relx=0.62, rely=line2_rel_y)
                # 字幕変更ボタン
                fix_window.apply_changes_button = tk.Button(fix_window, text='字幕変更︎', command=self.fix_win_preview,
                                                      highlightbackground=self.window_bg, fg='black',highlightthickness=0)
                fix_window.apply_changes_button.place(relx=0.8, rely=line2_rel_y, relwidth=0.1, height=button_height)
                # 字幕修正テキストボックス
                fix_window.subtitle_text_box = ScrolledText(fix_window, font=("", 15), height=5, width=57)
                fix_window.subtitle_text_box.place(relx=0.01, rely=line3_rel_y)
                fix_window.subtitle_text_box.bind('<Shift-Key>', self.fix_win_keyboard2)

                # 字幕の色選択ボタン
                fix_window.sutitle_font_color_lab = tk.Label(fix_window, text='字幕の色')
                fix_window.sutitle_font_color_lab.place(relx=0.8, rely=line4_rel_y)
                fix_window.sutitle_font_color_chooser = videdi_colorchooser.ColorSelectButton(fix_window,
                                                                                              self.sutitle_font_color_chooser.bg_color,
                                                                                              self.fix_win_preview)
                fix_window.sutitle_font_color_chooser.place(relx=0.89, rely=line4_rel_y)
                # 字幕の大きさ選択ボタン
                fix_window.sutitle_font_size_lab = tk.Label(fix_window, text='字幕の大きさ')
                fix_window.sutitle_font_size_lab.place(relx=0.77, rely=line3_rel_y)
                fix_window.font_size = tk.StringVar()
                fix_window.font_size.set(self.font_size.get())
                fix_window.sutitle_font_size_spinbox = tk.Spinbox(fix_window, format='%2.f', textvariable=fix_window.font_size,
                                                                  from_=5, to=30, increment=1, state='readonly', width=3)
                fix_window.sutitle_font_size_spinbox.place(relx=0.89, rely=line3_rel_y)
                fix_window.finish_button = tk.Button(fix_window, text='編集完了', command=self.fix_win_finish,
                                                     highlightbackground=self.window_bg, fg='black',
                                                     highlightthickness=0)
                fix_window.finish_button.place(relx=0.89, rely=last_line_rel_y, relwidth=0.1, height=button_height)
                fix_window.protocol("WM_DELETE_WINDOW", self.fix_win_finish)
                current_video_scale_var = 1
                while True:
                    fix_window.focus_set()
                    jumpcut_video = jumpcut_video_list[current_video_scale_var-1]
                    jumpcut_video_file = os.path.split(jumpcut_video)[1]
                    subtitle_video = subtitle_dir + os.path.splitext(jumpcut_video_file)[0] + '_subtitle.mp4'
                    text_file = text_dir + os.path.splitext(jumpcut_video_file)[0] + '.txt'
                    with open(text_file, mode='r', encoding='utf8') as rf:
                        current_subtitle_text = rf.read()
                    fix_window.sutitle_font_color_chooser.set_color(subtitle_colors[current_video_scale_var-1])
                    fix_window.font_size.set(subtitle_sizes[current_video_scale_var-1])
                    fix_window.subtitle_text_box.delete('1.0', 'end')
                    fix_window.subtitle_text_box.insert('1.0', current_subtitle_text)
                    self.cut_bln.set(video_sections[current_video_scale_var - 1][2])
                    self.thread_event = threading.Event()
                    self.player.__init__()
                    frame.video_label = tk.Label(fix_window)
                    frame.video_label.pack()
                    self.player.openfile(subtitle_video, frame.video_label)
                    fix_window.back_button.configure(state='normal')
                    fix_window.go_button.configure(state='normal')
                    fix_window.preview_button.configure(state='normal')
                    fix_window.apply_changes_button.configure(state='normal')
                    fix_window.finish_button.configure(state='normal')
                    self.player.play()
                    self.thread_event.wait()
                    fix_window.back_button.configure(state='disable')
                    fix_window.go_button.configure(state='disable')
                    fix_window.preview_button.configure(state='disable')
                    fix_window.apply_changes_button.configure(state='disable')
                    fix_window.finish_button.configure(state='disable')
                    new_subtitle_text = fix_window.subtitle_text_box.get('1.0', 'end -1c')
                    if new_subtitle_text != current_subtitle_text or \
                        subtitle_colors[current_video_scale_var-1] != fix_window.sutitle_font_color_chooser.bg_color or \
                        subtitle_sizes[current_video_scale_var-1] != fix_window.font_size.get():
                        subtitle_colors[current_video_scale_var-1] = fix_window.sutitle_font_color_chooser.bg_color
                        subtitle_sizes[current_video_scale_var-1] = fix_window.font_size.get()
                        with open(text_file, mode='w', encoding='utf8') as wf:
                            wf.write(new_subtitle_text)
                        srt_file = videdi_util.make_srt(srt_dir + os.path.splitext(jumpcut_video_file)[0] + '.srt',
                                                        [text_file, ],
                                                        [[0.0, video_sections[current_video_scale_var-1][1]
                                                          - video_sections[current_video_scale_var-1][0]], ])
                        os.remove(subtitle_video)
                        videdi_util.print_subtitle(jumpcut_video, srt_file, subtitle_sizes[current_video_scale_var-1], subtitle_colors[current_video_scale_var-1],
                                                   subtitle_dir + os.path.splitext(jumpcut_video_file)[0]
                                                   + '_subtitle.mp4')
                    video_sections[current_video_scale_var - 1][2] = self.cut_bln.get()
                    frame.video_label.destroy()
                    current_video_scale_var = int(video_scale_var.get())
                    if self.next_action == 'finish':
                        if messagebox.askyesno(title='編集完了', message='編集を終了しますか？'):
                            fix_window.destroy()
                            break
                        else:
                            continue
                    elif self.next_action == 'preview':
                        continue
                    elif self.next_action == 'back':
                        if current_video_scale_var != 1:
                            current_video_scale_var -= 1
                            video_scale_var.set(current_video_scale_var)
                    elif self.next_action == 'go':
                        if current_video_scale_var != len(jumpcut_video_list):
                            current_video_scale_var += 1
                            video_scale_var.set(current_video_scale_var)
            # フォルダ名を変更
            new_text_dir = self.process_dir + '.tmp/' + os.path.splitext(video_name)[0] + '_text/'
            os.rename(text_dir, new_text_dir)
            text_dir = new_text_dir
            new_srt_dir = self.process_dir + '.tmp/' + os.path.splitext(video_name)[0] + '_srt/'
            os.rename(srt_dir, new_srt_dir)
            srt_dir = new_srt_dir
            new_jumpcut_dir = self.process_dir + '.tmp/' + os.path.splitext(video_name)[0] + '_jumpcut/'
            os.rename(jumpcut_dir, new_jumpcut_dir)
            jumpcut_dir = new_jumpcut_dir
            new_subtitle_dir = self.process_dir + '.tmp/' + os.path.splitext(video_name)[0] + '_subtitle/'
            os.rename(subtitle_dir, new_subtitle_dir)
            subtitle_dir = new_subtitle_dir
            subtitle_video_list = videdi_util.search_videos(subtitle_dir)
            jumpcut_video_list = videdi_util.search_videos(jumpcut_dir)
            video_num = 1
            new_sections = []
            for j in range(len(subtitle_video_list)):
                text_file = text_dir + os.path.splitext(video_name)[0] + '_' + format(j+1, '0>' + str(digit)) + '.txt'
                srt_file = srt_dir + os.path.splitext(video_name)[0] + '_' + format(j+1, '0>' + str(digit)) + '.srt'
                if video_sections[j][2]:
                    os.remove(text_file)
                    os.remove(srt_file)
                    os.remove(jumpcut_video_list[j])
                    os.remove(subtitle_video_list[j])
                else:
                    os.rename(text_file, text_dir + os.path.splitext(video_name)[0] + '_' + format(video_num, '0>' + str(digit)) + '.txt')
                    os.rename(srt_file, srt_dir + os.path.splitext(video_name)[0] + '_' + format(video_num, '0>' + str(digit)) + '.srt')
                    os.rename(jumpcut_video_list[j],
                              jumpcut_dir + os.path.splitext(video_name)[0] + '_' + format(video_num, '0>' + str(digit)) + '.mp4')
                    os.rename(subtitle_video_list[j],
                              subtitle_dir + os.path.splitext(video_name)[0] + '_' + format(video_num, '0>' + str(digit)) + '_subtitle.mp4')
                    video_num += 1
                    new_sections.append(video_sections[j])
            # 動画を結合
            jumpcut_subtitle_video = videdi_util.check_path(os.path.splitext(video)[0] + '_jumpcut_subtitle.mp4')
            videdi_util.combine_video(subtitle_dir, jumpcut_subtitle_video)
            self.log_frame.set_log(video_name + 'を編集しました')
            new_text_dir = self.process_dir + '.tmp/' + os.path.splitext(video_name)[0] + '_text/'
            os.rename(text_dir, new_text_dir)
        # 一時的なフォルダを削除
        shutil.rmtree(self.process_dir + '.tmp/')
        # ボタン有効化
        self.enable_all_button()
        # 音声テキスト作成完了ログ
        self.log_frame.set_big_log(self.process_dir.split('/')[-2] + 'フォルダ内の動画を編集しました')
        return

    def divide_video_into_sections(self, video, sections, output_dir):
        digit = len(str(len(sections)))
        video_name = os.path.split(video)[1]
        # sectionsにしたがって動画をカット
        for i in range(len(sections)):
            split_file = output_dir + os.path.splitext(video_name)[0] + '_' + format(i+1, '0>' + str(digit)) + '.mp4'
            command = [FFMPEG_PATH, '-i', video, '-ss', str(sections[i][0]), '-t',
                       str(sections[i][1] - sections[i][0]), split_file]
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # 進捗をパーセントで表示
            self.log_frame.set_progress_log('カット処理', i + 1, len(sections))
        return output_dir

    def fix_win_end_process(self):
        self.player.stop()
        self.thread_event.set()
        return

    def fix_win_preview(self):
        self.next_action = 'preview'
        self.fix_win_end_process()
        return

    def fix_win_back(self):
        self.next_action = 'back'
        self.fix_win_end_process()
        return

    def fix_win_go(self):
        self.next_action = 'go'
        self.fix_win_end_process()
        return

    def fix_win_finish(self):
        self.next_action = 'finish'
        self.fix_win_end_process()
        return

    def fix_win_keyboard(self, event):
        pressed_key = str(event.char)
        self.log_frame.set_log('\'' + repr(event.char) + '\'')
        if 'frame' in str(event.widget):
            return
        if pressed_key == ' ' or pressed_key == '　':
            self.fix_win_preview()
        elif pressed_key == '\uf703':
            self.fix_win_go()
        elif pressed_key == '\uf702':
            self.fix_win_back()
        elif pressed_key == '\uf700':
            self.cut_bln.set(True)
        elif pressed_key == '\uf701':
            self.cut_bln.set(False)
        return
    def fix_win_keyboard2(self, event):
        if str(event.char) == '\r':
            self.fix_win_preview()



def main():
    Videdi()


if __name__ == '__main__':
    main()
