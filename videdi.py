import tkinter as tk
from tkinter import *
import tkinter.font as font
from tkinter import Frame
from tkinter import filedialog
import os
import subprocess
import threading
import shutil
import speech_recognition as sr
import time
import imageio
from PIL import ImageTk, Image
from imageio.plugins.ffmpeg import FfmpegFormat
import simpleaudio

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

APP_PATH = '/'.join(sys.argv[0].split('/')[:-3])
# python videdi.pyで実行する時のため
if APP_PATH == '':
    APP_PATH = '/Applications/videdi.app'
FFMPEG_PATH = APP_PATH + '/Contents/MacOS/ffmpeg'
FFPROBE_PATH = APP_PATH + '/Contents/MacOS/ffprobe'

# ----------------------ファイル分割できそう(ここから)------------------------
# 音楽を再生する
class Audio_player():
    def __init__(self):
        pass
    def __del__(self):
        try:
            os.remove(self.audio)
        except:
            pass
    def openfile(self, file_path):
        self.audio = file_path.split('.')[0] + '.wav'
        if os.path.exists(self.audio):
            os.remove(self.audio)
        try:
            command = [FFMPEG_PATH, '-i', file_path, self.audio]
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print(e)
    def play(self):
        wav_obj = simpleaudio.WaveObject.from_wave_file(self.audio)
        self.play_obj = wav_obj.play()
        self.play_obj.wait_done()
    def stop(self):
        try:
            self.play_obj.stop()
        except:
            pass

class Video_player():
    def __init__(self):
        format = FfmpegFormat(
            "ffmpeg",
            "Many video formats and cameras (via ffmpeg)",
            ".mov .avi .mpg .mpeg .mp4 .mkv .wmv .webm",
            "I",
            )
        imageio.formats.add_format(format,True)
        self.stop_bln = False
    def openfile(self, file_path,frame):
        self.frame = frame
        try:
            self.video = imageio.get_reader(file_path)
        except imageio.core.fetching.NeedDownloadError:
            imageio.plugins.avbin.download()
            self.video = imageio.get_reader(file_path)
    def play(self):
        self.video_thread = threading.Thread(target=self._stream)
        self.video_thread.start()
    def stop(self):
        try:
            self.stop_bln = True
        except Exception as e:
            print('error:Video_player.stop method')
            print(e)
            pass
        return
    def _stream(self):
        # print(self.video.get_meta_data())
        start_time=time.time()
        sleeptime = 1/self.video.get_meta_data()["fps"]
        frame_now = 0
        for image in self.video.iter_data():
            if self.stop_bln:
                break
            try:
                frame_now = frame_now + 1
                if frame_now * sleeptime >= time.time() - start_time:
                    img = Image.fromarray(image).resize((670, 490))
                    frame_image = ImageTk.PhotoImage(img)
                    self.frame.config(image=frame_image)
                    self.frame.image = frame_image
                    time.sleep(sleeptime)
                else:
                    pass
            except:
                pass
        return

class Video_Audio_player():
    def __init__(self):
        self.video_player = Video_player()
        self.audio_player = Audio_player()
    def openfile(self, file_path, frame):
        self.video_player.openfile(file_path, frame)
        self.audio_player.openfile(file_path)
    def play(self):
        self.video_player.play()
        self.audio_player.play()
    def stop(self):
        self.video_player.stop()
        self.audio_player.stop()

# ---------------------------ファイル分割できそう(ここまで)------------------------

class ClassFrame(Frame):
    def __init__(self, master, bg=None, width=None, height=None):
        super().__init__(master, bg=bg, width=width, height=height)

class ScrollFrame(ClassFrame):
    def __init__(self, master, log_max, bg=None, width=None, height=None):
        super(ScrollFrame, self).__init__(master, bg=bg, width=width, height=height)

        self.height = height
        self.width = width
        self.bg = bg

        # スクロールバーの作成
        self.scroll_bar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.scroll_bar.pack(fill=tk.Y, side=tk.RIGHT, expand=False)
        self.canvas = tk.Canvas(self, bg=self.bg, yscrollcommand=self.scroll_bar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll_bar.config(command=self.canvas.yview)

        # ビューをリセット
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        self.interior = Frame(self.canvas, bg=self.bg, borderwidth=10)
        self.interior_id = self.canvas.create_window(0, 0, window=self.interior, anchor=tk.NW)

        self.interior.bind('<Configure>', self.configure_interior)
        self.canvas.bind('<Configure>', self.configure_canvas)

        # ログを初期化
        self.log_max = log_max
        self.log_vars = []
        self.log_labels = []
        self.log_color = 0
        self.reset_all_logs()

    def configure_interior(self, event=None):
        size = (self.interior.winfo_reqwidth(), self.interior.winfo_reqheight())
        self.canvas.config(scrollregion='0 0 %s %s' % size)
        if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
            self.canvas.config(width=self.interior.winfo_reqwidth())

    def configure_canvas(self, event=None):
        if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
            self.canvas.itemconfigure(self.interior_id, width=self.canvas.winfo_width())

    def mouse_y_scroll(self, event):
        if event.delta > 0:
            self.canvas.yview_scroll(-1, 'units')
        elif event.delta < 0:
            self.canvas.yview_scroll(1, 'units')

    # ログのセット
    def set_log(self, s):
        if len(self.log_vars) < self.log_max:
            self.log_vars.append(tk.StringVar())
            for i in range(len(self.log_vars)-1, 0, -1):
                self.log_vars[i].set(self.log_vars[i-1].get())
            self.log_labels.append(tk.Label(self.interior, textvariable=self.log_vars[len(self.log_vars) - 1],
                                            foreground='#' + format(self.log_color, '02x')*3, bg=self.bg))
            self.log_color += int(255 / self.log_max - 1)
            self.log_labels[len(self.log_vars)-1].pack(anchor=tk.S, fill=tk.X, padx=0, pady=0, ipadx=0, ipady=0)
            self.log_labels[len(self.log_vars)-1].bind('<MouseWheel>', self.mouse_y_scroll)
            self.log_vars[0].set(s)
        else:
            for i in range(len(self.log_vars)-1, 0, -1):
                self.log_vars[i].set(self.log_vars[i-1].get())
            self.log_vars[0].set(s)
        return

    # 大きいログのセット
    def set_big_log(self, s):
        self.set_log('')
        self.set_log('----------------------------------------------------------')
        self.set_log(s)
        self.set_log('----------------------------------------------------------')
        return

    # ログのリセット
    def reset_all_logs(self):
        for i in range(len(self.log_labels)):
            self.log_labels[i].destroy()
        self.log_vars = []
        self.log_labels = []
        self.log_color = 0
        # --       --     ----     ----      -----    ----     ----
        #  \\     //     -  -    ||   \\    ||---    ||   \\   _  _
        #   \\   //      | |     ||   ||    ||__|    ||   ||   ||
        #    \\ //      -  -     ||  //     ||___    ||  //   _  _
        #     \_/      ----     ----       -----    ----     ----
        for i in range(2):
            self.set_log('')
        self.set_log(r'       \_/          ----      ----        -----      ----          ----')
        self.set_log(r'     \ \ / /         _  _     | |___/ /     | |___     | |___/ /       _  _')
        self.set_log(r'   \ \     / /        | |      | |      | |   | |___|     | |      | |      | |')
        self.set_log(r' \ \        / /      -  -     | |---\ \    | |---     | |--- \ \     -  -')
        self.set_log(r'--          --     ----     ----        -----     ----          ----')
        self.set_log('')
        return


class Videdi:
    def __init__(self, width=700, height=550):
        # TKクラスをインスタンス化
        self.root = tk.Tk()
        # ウィンドウのタイトルを設定
        self.root.title('VIDEDI')
        # ウィンドウの大きさを設定
        self.window_width = width
        self.window_height = height

        # ウィンドウをど真ん中に設定
        # self.window_pos_x = (self.root.winfo_screenwidth() - self.window_width) // 2
        # self.window_pos_y = (self.root.winfo_screenheight() - self.window_height) // 2

        # ウィンドウを左上に設定
        self.window_pos_x = 0
        self.window_pos_y = 0

        # ウィンドウの大きさを指定
        self.root.geometry(str(self.window_width) + 'x' + str(self.window_height)
                           + '+' + str(self.window_pos_x) + '+' + str(self.window_pos_y))

        # ウィンドウの背景の色を設定
        window_bg = '#ececec'
        self.root.configure(bg=window_bg)
        # ウィンドウの枠を指定
        self.root.configure(borderwidth=10, relief=RIDGE)

        # フォントを指定
        bold_font = font.Font(self.root, size=16, weight='bold')
        button_font = font.Font(self.root, size=14)
        process_button_fg = 'red'
        self.button_background = window_bg

        # タイトルラベル
        pos_y = 0
        self.title_height = 100
        title_font = font.Font(self.root, family='impact', size=self.title_height, weight='bold')
        self.title_lab = tk.Label(text='VIDEDI', font=title_font, foreground='lightgray', bg='black')
        self.title_lab.place(x=0, y=pos_y, relwidth=1.0, height=self.title_height)

        # 現在選択中フォルダラベル
        pos_y += self.title_height + 15
        height = 20
        self.process_dir_path = ''
        self.dir_name_min = 40
        self.current_dir_var = tk.StringVar()
        self.current_dir_var.set('編集したい動画のあるフォルダを選択してください')
        self.current_dir_lab = tk.Label(textvariable=self.current_dir_var, font=bold_font, bg=window_bg)
        self.current_dir_lab.place(x=0, y=pos_y, relwidth=1.0, height=height)

        # フォルダ選択ボタン
        self.dir_is_available = False
        self.sd_button_pos_y = pos_y + height + 15
        self.sd_button_height = 25
        self.sd_button_relwidth = 0.2
        self.select_dir_button = tk.Button(text='フォルダの選択', command=self.select_dir,
                                              font=button_font,
                                              highlightbackground=self.button_background, fg='black', highlightthickness=0)
        self.select_dir_button.place(relx=(1 - self.sd_button_relwidth) / 2, y=self.sd_button_pos_y,
                                        relwidth=self.sd_button_relwidth, height=self.sd_button_height)

        # スクロール式のログラベル
        self.scroll_pos_y = self.sd_button_pos_y + self.sd_button_height + 15
        self.scroll_height = 200
        self.log_max = 100
        self.log_frame = ScrollFrame(master=self.root, log_max=self.log_max, bg=window_bg,
                                 width=self.window_width, height=self.window_height)
        self.log_frame.place(x=0, y=self.scroll_pos_y, relwidth=1.0, height=self.scroll_height)
        self.log_frame.interior.bind('<ButtonPress-1>', self.move_start)
        self.log_frame.interior.bind('<B1-Motion>', self.move_move)
        self.log_frame.interior.bind('<MouseWheel>', self.mouse_y_scroll)

        # ログリセットボタン
        self.lr_button_relx = 0.85
        self.lr_button_pos_y = self.sd_button_pos_y + 15
        self.lr_button_height = 25
        self.lr_button_relwidth = 0.15
        self.log_reset_button = tk.Button(text='ログリセット', command=self.log_frame.reset_all_logs,
                                          font=button_font,
                                          highlightbackground=self.button_background, fg='black', highlightthickness=0)
        self.log_reset_button.place(relx=self.lr_button_relx, y=self.lr_button_pos_y,
                                    relwidth=self.lr_button_relwidth, height=self.lr_button_height)

        # 処理選択ラベル
        self.run_choices_pos_y = self.scroll_pos_y + self.scroll_height + 20
        self.run_choices_lab = tk.Label(text='処理選択', font=bold_font)
        self.run_choices_lab.place(relx=0.05, y=self.run_choices_pos_y)

        # 処理のドロップダウンメニュー
        self.process_list = ['ジャンプカット', '字幕を付ける', 'ジャンプカットして字幕を付ける']
        self.current_process = tk.StringVar(self.root)
        self.current_process.set(self.process_list[0])
        self.current_process.trace("w", self.put_options)
        self.process_opt = tk.OptionMenu(self.root, self.current_process, *self.process_list)
        self.process_opt.config(width=19)
        self.process_opt.place(relx=0.2, y=self.run_choices_pos_y)
        self.process_opt.config(state='disable')

        # オプション選択ラベル
        self.option_pos_y = self.run_choices_pos_y + 30
        self.option_lab = tk.Label(text='オプション', font=bold_font)
        self.option_lab.place(relx=0.05, y=self.option_pos_y)

        # ジャンプカット修正チェックボックス
        self.jumpcut_fix_bln = tk.BooleanVar()
        self.jumpcut_fix_bln.set(False)
        self.jumpcut_fix_chk = tk.Checkbutton(self.root, variable=self.jumpcut_fix_bln, text='ジャンプカット修正')

        # ジャンプカット動画の最小時間を設定(単位:秒)
        self.min_time = 0.5
        # ジャンプカット動画の前後の余裕を設定(単位:秒)
        self.margin_time = 0.1

        # 字幕修正チェックボックス
        self.subtitle_fix_bln = tk.BooleanVar()
        self.subtitle_fix_bln.set(False)
        self.subtitle_fix_chk = tk.Checkbutton(self.root, variable=self.subtitle_fix_bln, text='字幕修正')

        self.put_options()

        # 実行ボタン
        self.run_button_pos_y = self.option_pos_y + 30
        self.run_button_height = 25
        self.run_button_relwidth = 0.1
        self.run_button = tk.Button(text='実行', state='disable', command=self.run_button, font=button_font,
                                    highlightbackground=self.button_background, fg=process_button_fg, highlightthickness=0)
        self.run_button.place(relx=(1-self.run_button_relwidth)/2, y=self.run_button_pos_y,
                                  relwidth=self.run_button_relwidth, height=self.run_button_height)

        self.cut = False
        self.thread_event = None

        # メインループでイベント待ち
        if __name__ == '__main__':
            self.root.mainloop()

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
        dir = self.process_dir_path
        if len(dir) == 0:
            idir = os.path.abspath(os.path.dirname(__file__))
        else:
            idir = os.path.abspath(os.path.dirname(dir))
        # フォルダ選択済みフラグをおろす
        self.dir_is_available = False
        # 実行系ボタン無効化
        self.process_opt.configure(state='disable')
        self.jumpcut_fix_chk.configure(state='disable')
        self.subtitle_fix_chk.configure(state='disable')
        self.run_button.configure(state='disabled')
        # フォルダを選択する
        self.process_dir_path = filedialog.askdirectory(initialdir=idir)
        # フォルダが選択されなかった場合、直前に選択していたフォルダを選択
        if len(self.process_dir_path) == 0:
            self.process_dir_path = dir
        # 選択されたフォルダが存在する場合
        if os.path.exists(self.process_dir_path):
            # フォルダの絶対パスが設定より長い場合
            if len(self.process_dir_path) > self.dir_name_min:
                # 表示するフォルダ名を絶対パスのフォルダ名の部分だけにする
                s = self.process_dir_path.split('/')
                dir_name = s[-1]
            # フォルダの絶対パスが設定より短い場合
            else:
                # 表示するフォルダ名を絶対パスにする
                dir_name = self.process_dir_path
            # 選択されたフォルダの中に動画がある場合
            if self.search_videos(self.process_dir_path) != []:
                self.current_dir_var.set(dir_name + 'フォルダを選択中')
                # フォルダ選択済みフラグを立てる
                self.dir_is_available = True
                # 処理のボタン有効化
                self.process_opt.configure(state='normal')
                self.run_button.configure(state='normal')
                # オプション表示
                self.put_options()
            # 選択されたフォルダ内に動画がない場合
            else:
                self.current_dir_var.set(dir_name + 'フォルダには処理できる動画ファイルがありません。')
        # 選択されたフォルダが存在しない場合
        else:
            self.current_dir_var.set('編集したい動画のあるフォルダを選択してください')
        return

# ---------------------------ファイル分割できそう(ここから) ---------------------

    # フォルダ内のvideoファイル名取得
    def search_videos(self, search_dir):
        # フォルダ内のファイルやディレクトリ名を取得
        files = os.listdir(search_dir)
        # フォルダ内の動画ファイル名を取得
        files = [i for i in files if i[-4:].lower() == '.mov' or i[-4:].lower() == '.mp4']
        # 動画ファイル名を名前順で返す
        return sorted(files)

    # 現在のフォルダ内に新しいフォルダを作る
    def make_dir(self, new_dir_path):
        # そのフォルダが既に存在する場合
        if os.path.exists(new_dir_path):
            try:
                i = 2
                while True:
                    if not (os.path.exists(new_dir_path + str(i))):
                        new_dir_path = new_dir_path + str(i)
                        os.mkdir(new_dir_path)
                        break
                    i += 1
            except Exception as e:
                print('error:make_dir method')
                print(e)
                self.log_frame.set_log('error:make_dir method')
                return
        else:
            os.mkdir(new_dir_path)
        return new_dir_path

# ---------------------------ファイル分割できそう(ここまで)----------------------------

    # ボタン無効化
    def disable_all_button(self):
        self.select_dir_button.configure(state='disabled')
        self.log_reset_button.configure(state='disabled')
        self.process_opt.configure(state='disable')
        self.jumpcut_fix_chk.configure(state='disable')
        self.subtitle_fix_chk.configure(state='disable')
        self.run_button.configure(state='disable')
        return

    # ボタン有効化
    def enable_all_button(self):
        self.select_dir_button.configure(state='normal')
        self.log_reset_button.configure(state='normal')
        self.process_opt.configure(state='normal')
        self.jumpcut_fix_chk.configure(state='normal')
        self.subtitle_fix_chk.configure(state='normal')
        self.run_button.configure(state='normal')
        return

    # 処理の内容からオプションを表示
    def put_options(self, *args):
        # オプションを初期化
        self.jumpcut_fix_bln.set(False)
        self.subtitle_fix_bln.set(False)
        # オプションを非表示にする
        self.jumpcut_fix_chk.place_forget()
        self.subtitle_fix_chk.place_forget()
        process = self.current_process.get()
        # 動画が入ったフォルダが選択されていたら、ウィジェットを有効化する
        widget_state = 'disable'
        if self.dir_is_available:
            widget_state = 'normal'
        # 処理ごとにオプションの表示を変える
        if process == 'ジャンプカット':
            self.jumpcut_fix_chk.place(relx=0.2, y=self.option_pos_y)
            self.jumpcut_fix_chk.configure(state=widget_state)
        elif process == '字幕を付ける':
            self.subtitle_fix_chk.place(relx=0.2, y=self.option_pos_y)
            self.subtitle_fix_chk.configure(state=widget_state)
        elif process == 'ジャンプカットして字幕を付ける':
            self.jumpcut_fix_chk.place(relx=0.2, y=self.option_pos_y)
            self.jumpcut_fix_chk.configure(state=widget_state)
            self.subtitle_fix_chk.place(relx=0.4, y=self.option_pos_y)
            self.subtitle_fix_chk.configure(state=widget_state)
        else:
            self.log_frame.set_log('error:put_options method')
            return
        return

    # 処理実行ボタンの処理
    def run_button(self):
        # ボタン無効化
        self.disable_all_button()
        # 現在選択中の処理を実行
        process = self.current_process.get()
        if process == 'ジャンプカット':
            thread = threading.Thread(target=self.jumpcut)
        elif process == '字幕を付ける':
            thread = threading.Thread(target=self.add_subtitle)
        elif process == 'ジャンプカットして字幕を付ける':
            thread = threading.Thread(target=self.jumpcut_and_add_subtitle)
        else:
            self.log_frame.set_log('error:run_button method')
            return
        # スレッディング処理を開始
        thread.start()
        return

    # フォルダ内の動画をジャンプカット
    def jumpcut(self):
        # ジャンプカット開始
        self.log_frame.set_big_log(self.process_dir_path.split('/')[-1] + 'フォルダ内の動画をジャンプカットします')
        os.chdir(self.process_dir_path)
        video_dir_path = self.process_dir_path
        video_list = self.search_videos(self.process_dir_path)
        jumpcut_fix_bln = self.jumpcut_fix_bln.get()
        for i, video in enumerate(video_list):
            self.log_frame.set_log(video + 'をジャンプカットします ' + str(i+1) + '/' + str(len(video_list)))
            self.log_frame.set_log(video + 'の無音部分を検知します')
            cut_sections = self.silence_sections(video)
            if len(cut_sections) == 0:
                self.log_frame.set_log(video + 'には無音部分がありませんでした')
                continue
            video_sections = self.video_sections(cut_sections, video)
            video_sections = self.arrange_sections(video_sections, self.min_time, self.margin_time)
            if self.jumpcut_fix_bln.get():
                video_sections = self.all_sections(video_sections, video)
            self.cut_video(video_dir_path, video_sections, video)
            self.log_frame.set_log(video + 'をジャンプカットしました')
            self.jumpcut_fix_bln.set(jumpcut_fix_bln)
        # ボタン有効化
        self.enable_all_button()
        # ジャンプカット完了ログ
        self.log_frame.set_big_log(self.process_dir_path.split('/')[-1] + 'フォルダ内の動画をジャンプカットしました')
        return

# -----------------------ファイル分割できそう(ここから)-----------------------------
    # 無音部分検出
    def silence_sections(self, video):
        try:
            # 無音部分をffmpegで検出
            command = [FFMPEG_PATH, '-i', video, '-af',
                                     'silencedetect=noise=-30dB:d=0.3', '-f', 'null', '-']
            output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print('error:silence_sections method')
            print(e)
            return
        # 出力結果から無音部分の始まりと終わりの時間を1セットとする、二次元配列を作る
        s = str(output)
        # 出力結果を改行ごとに分ける
        lines = s.split('\\n')
        # 時間を入れていく1次元配列を作成
        time_list = []
        # 出力結果の各行から無音部分についての情報を探す
        for line in lines:
            # 無音部分についての出力行の場合
            if 'silencedetect' in line:
                # その行をスペースで区切る
                words = line.split(' ')
                # 行の中から無音部分の始まりと終わりを探す
                for i in range(len(words)):
                    # 無音部分の始まりの場合
                    if 'silence_start' in words[i]:
                        # その時間を配列にfloatに変換して追加する
                        time_list.append(float(words[i + 1]))
                    # 無音部分の終わりの場合
                    if 'silence_end' in words[i]:
                        # その時間を配列にfloatに変換して追加する
                        time_list.append(float(words[i + 1]))
        silence_section_list = list(zip(*[iter(time_list)] * 2))
        return silence_section_list

    # 動画の長さを取得
    def get_video_duration(self, video):
        duration = 0
        try:
            command = [FFPROBE_PATH, video, '-hide_banner', '-show_format']
            output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print('error:video_sections method')
            print(e)
            return
        s = str(output)
        lines = s.split('\\n')
        for line in lines:
            words = line.split('=')
            if words[0] == 'duration':
                duration = float(words[1])
                break
        return duration

    # カットする部分sectionsをカットしない部分new_sectionsに変換
    def video_sections(self, sections, video):
        time_list = []
        if sections[0][0] != 0.0:
            time_list.append(float(0.0))
            time_list.append(sections[0][0])
        for i in range(len(sections)-1):
            time_list.append(sections[i][1])
            time_list.append(sections[i+1][0])
        duration = self.get_video_duration(video)
        if sections[-1][1] < duration:
            time_list.append(sections[-1][1])
            time_list.append(duration)
        new_sections = list(zip(*[iter(time_list)] * 2))
        return new_sections

    # sectionsにオプションで変更を加える
    def arrange_sections(self, sections, min_time, margin_time):
        new_sections = []
        for i in range(len(sections)):
            if (sections[i][1] - sections[i][0]) < min_time:
                continue
            else:
                if i == 0 and sections[0][0] < margin_time:
                    new_sections.append([sections[i][0], sections[i][1] + margin_time])
                else:
                    new_sections.append([sections[i][0] - margin_time, sections[i][1] + margin_time])
        try:
            new_sections[-1][1] -= margin_time
        except Exception as e:
            print('error:arrange_sections method')
            print(e)
        return new_sections

    # ジャンプカットの修正をする場合のカットしない部分new_sectionsを作成
    def all_sections(self, sections, video):
        time_list = []
        if sections[0][0] != 0.0:
            time_list.append(float(0.0))
            time_list.append(sections[0][0])
        for i in range(len(sections)-1):
            time_list.append(sections[i][0])
            time_list.append(sections[i][1])
            time_list.append(sections[i][1])
            time_list.append(sections[i+1][0])
        time_list.append(sections[-1][0])
        time_list.append(sections[-1][1])
        duration = self.get_video_duration(video)
        if sections[-1][1] < duration:
            time_list.append(sections[-1][1])
            time_list.append(duration)
        new_sections = list(zip(*[iter(time_list)] * 2))
        return new_sections

# ------------------------------ファイル分割できそう(ここまで)----------------------------

    # 音のある部分を出力
    def cut_video(self, video_dir, sections, video):
        os.chdir(video_dir)
        digit = len(str(len(sections)))
        video_name = video.split('.')[0]
        jumpcut_dir = self.make_dir(video_dir + '/' + video_name + '_jumpcut')
        new_sections = []
        for i in range(len(sections)):
            split_file = jumpcut_dir + '/' + video_name + '_' + format(i+1, '0>' + str(digit)) + '.mp4'
            command = [FFMPEG_PATH, '-i', video, '-ss', str(sections[i][0]), '-t',
                       str(sections[i][1] - sections[i][0]), split_file]
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if self.jumpcut_fix_bln.get():
                self.thread_event = threading.Event()
                thread = threading.Thread(target=self.play_video_for_cut, args=[split_file, ])
                thread.start()
                self.thread_event.wait()
                if self.cut:
                    try:
                        os.remove(split_file)
                    except Exception as e:
                        print('error:cut_video method')
                        print(e)
                        self.log_frame.set_log('error:cut_video method')
                else:
                    new_sections.append(sections[i])
                thread.join()
            else:
                new_sections.append(sections[i])
            # 進捗をパーセントで表示
            if int((i+1)*100/len(sections)) != int(i*100/len(sections)):
                s = str(int(((i+1) * 100) / len(sections)))
                self.log_frame.set_log('カット処理' + '{:>3}'.format(s) + '%完了')
        return jumpcut_dir, new_sections

    # ジャンプカット修正のためのウィンドウを表示
    def play_video_for_cut(self, video_path):
        window = tk.Toplevel()
        # window = tk.Toplevel(self.root)
        window.geometry("700x550" + '+' + str(self.window_width) + '+' + str(0))
        window.title('この部分を使いますか？')
        frame = Frame(window)
        frame.pack()
        video_audio_player = Video_Audio_player()
        frame.video_lavel = tk.Label(window)
        frame.video_lavel.pack()
        def end_process():
            try:
                video_audio_player.stop()
                window.destroy()
                self.thread_event.set()
            except Exception as e:
                print('error:play_video_for_cut.end_process method')
                print(e)
                self.log_frame.set_log('error:play_video_for_cut.end_process method')
            return
        def on_closing():
            self.jumpcut_fix_bln.set(False)
            self.cut = False
            end_process()
            return
        window.protocol("WM_DELETE_WINDOW", on_closing)
        text = 'この部分を使いますか?(このウィンドウを消すと、以降カットしません)'
        frame.label = tk.Label(window, text=text)
        frame.label.place(relx=0.2, rely=0.9)
        def select_cut():
            self.cut = True
            end_process()
            return
        def select_leave():
            self.cut = False
            end_process()
            return
        select_button_rel_y = 0.95
        select_button_height = 25
        select_button_relwidth = 0.1
        cut_button = tk.Button(window, text='カット', command=select_cut,
                                           highlightbackground=self.button_background, fg='black', highlightthickness=0)
        cut_button.place(relx=0.39, rely=select_button_rel_y,
                                     relwidth=select_button_relwidth, height=select_button_height)
        leave_button = tk.Button(window, text='残す', command=select_leave,
                                           highlightbackground=self.button_background, fg='black', highlightthickness=0)
        leave_button.place(relx=0.51, rely=select_button_rel_y,
                                     relwidth=select_button_relwidth, height=select_button_height)
        try:
            video_audio_player.openfile(video_path, frame.video_lavel)
            video_audio_player.play()
        except Exception as e:
            print('error:play_video_for_cut method')
            print(e)
            self.log_frame.set_log('error:play_video_for_cut method')
            return
        return

    # 字幕付き動画作成
    def add_subtitle(self):
        # 音声テキスト作成開始ログ
        self.log_frame.set_big_log(self.process_dir_path.split('/')[-1] + 'フォルダ内の動画に字幕を付けます')
        os.chdir(self.process_dir_path)
        video_list = self.search_videos(self.process_dir_path)
        try:
            shutil.rmtree('.tmp')
        except:
            pass
        os.mkdir('.tmp')
        subtitle_fix_bln = self.subtitle_fix_bln.get()
        for i, video in enumerate(video_list):
            self.log_frame.set_log(video + 'をカットして字幕を付けます ' + str(i+1) + '/' + str(len(video_list)))
            shutil.copyfile(video, '.tmp/' + video)
            self.log_frame.set_log(video + 'の無音部分を検知します')
            cut_sections = self.silence_sections(video)
            video_sections = self.video_sections(cut_sections, video)
            video_sections = self.arrange_sections(video_sections, self.min_time, self.margin_time)
            video_sections = self.all_sections(video_sections, video)
            self.log_frame.set_log(video + 'の音声認識のために動画をカットします')
            shutil.copyfile(video, '.tmp/' + video)
            jumpcut_dir, video_sections = self.cut_video(self.process_dir_path + '/.tmp', video_sections, video)
            jumpcut_dir = os.path.abspath(jumpcut_dir)
            jumpcut_video_list = self.search_videos(jumpcut_dir)
            self.speech_recognize(jumpcut_dir, jumpcut_video_list)
            text_path = os.path.abspath('./.tmp/' + jumpcut_dir.split('/')[-1] + '/' + jumpcut_dir.split('/')[-1] + '_subtitle')
            for i, jumpcut_video in enumerate(jumpcut_video_list):
                text_list = [jumpcut_video.split('.')[0] + '.txt', ]
                self.make_srt(jumpcut_dir, jumpcut_video, text_path, text_list, [[0.0, video_sections[i][1] - video_sections[i][0]], ])
                if self.subtitle_fix_bln.get():
                    self.decided = False
                    while not self.decided:
                        self.thread_event = threading.Event()
                        self.make_srt(jumpcut_dir, jumpcut_video, text_path, text_list,[[0.0, video_sections[i][1] - video_sections[i][0]], ])
                        jumpcut_video_subtitle = self.print_subtitle(jumpcut_dir, jumpcut_video, jumpcut_dir)
                        thread = threading.Thread(target=self.play_video_for_subtitle, args=[jumpcut_video_subtitle, text_path + '/' + jumpcut_video.split('.')[0] + '.txt'])
                        thread.start()
                        self.thread_event.wait()
                        thread.join()
                else:
                    self.print_subtitle(jumpcut_dir, jumpcut_video, jumpcut_dir)
                s = str(int((i+1)*100/len(jumpcut_video_list)))
                self.log_frame.set_log('字幕付け' + '{:>3}'.format(s) + '%完了')
                os.remove(jumpcut_dir + '/' + jumpcut_video)
            # 動画を結合
            self.combine_video(jumpcut_dir, video.split('.')[0])
            self.subtitle_fix_bln.set(subtitle_fix_bln)
            self.log_frame.set_log(video + 'に字幕を付けました')
        shutil.rmtree('.tmp')
        # ボタン有効化
        self.enable_all_button()
        # 音声テキスト作成完了ログ
        self.log_frame.set_big_log(self.process_dir_path.split('/')[-1] + 'フォルダ内の動画に字幕を付けました')
        return

    # ジャンプカットして字幕を付ける処理
    def jumpcut_and_add_subtitle(self):
        # 音声テキスト作成開始ログ
        self.log_frame.set_big_log(self.process_dir_path.split('/')[-1] + 'フォルダ内の動画をジャンプカットして字幕を付けます')
        os.chdir(self.process_dir_path)
        video_list = self.search_videos(self.process_dir_path)
        try:
            shutil.rmtree('.tmp')
        except:
            pass
        os.mkdir('.tmp')
        subtitle_fix_bln = self.subtitle_fix_bln.get()
        for i, video in enumerate(video_list):
            self.log_frame.set_log(video + 'をカットして字幕を付けます ' + str(i+1) + '/' + str(len(video_list)))
            shutil.copyfile(video, '.tmp/' + video)
            self.log_frame.set_log(video + 'の無音部分を検知します')
            cut_sections = self.silence_sections(video)
            video_sections = self.video_sections(cut_sections, video)
            video_sections = self.arrange_sections(video_sections, self.min_time, self.margin_time)
            if self.jumpcut_fix_bln.get():
                video_sections = self.all_sections(video_sections, video)
            self.log_frame.set_log(video + 'の音声認識のために動画をカットします')
            shutil.copyfile(video, '.tmp/' + video)
            jumpcut_dir, video_sections = self.cut_video(self.process_dir_path + '/.tmp', video_sections, video)
            jumpcut_dir = os.path.abspath(jumpcut_dir)
            jumpcut_video_list = self.search_videos(jumpcut_dir)
            self.speech_recognize(jumpcut_dir, jumpcut_video_list)
            text_path = os.path.abspath('./.tmp/' + jumpcut_dir.split('/')[-1] + '/' + jumpcut_dir.split('/')[-1] + '_subtitle')
            for i, jumpcut_video in enumerate(jumpcut_video_list):
                text_list = [jumpcut_video.split('.')[0] + '.txt', ]
                self.make_srt(jumpcut_dir, jumpcut_video, text_path, text_list, [[0.0, video_sections[i][1] - video_sections[i][0]], ])
                if self.subtitle_fix_bln.get():
                    self.decided = False
                    while not self.decided:
                        self.thread_event = threading.Event()
                        self.make_srt(jumpcut_dir, jumpcut_video, text_path, text_list,[[0.0, video_sections[i][1] - video_sections[i][0]], ])
                        jumpcut_video_subtitle = self.print_subtitle(jumpcut_dir, jumpcut_video, jumpcut_dir)
                        thread = threading.Thread(target=self.play_video_for_subtitle, args=[jumpcut_video_subtitle, text_path + '/' + jumpcut_video.split('.')[0] + '.txt'])
                        thread.start()
                        self.thread_event.wait()
                        thread.join()
                else:
                    self.print_subtitle(jumpcut_dir, jumpcut_video, jumpcut_dir)
                s = str(int((i+1)*100/len(jumpcut_video_list)))
                self.log_frame.set_log('字幕付け' + '{:>3}'.format(s) + '%完了')
                os.remove(jumpcut_dir + '/' + jumpcut_video)
            # 動画を結合
            self.combine_video(jumpcut_dir, video.split('.')[0])
            self.subtitle_fix_bln.set(subtitle_fix_bln)
            self.log_frame.set_log(video + 'をジャンプカットして字幕を付けました')
        shutil.rmtree('.tmp')
        # ボタン有効化
        self.enable_all_button()
        # 音声テキスト作成完了ログ
        self.log_frame.set_big_log(self.process_dir_path.split('/')[-1] + 'フォルダ内の動画をジャンプカットして字幕を付けました')
        return

    # 字幕修正のためのウィンドウを表示
    def play_video_for_subtitle(self, video_path, text_path):
        # window = tk.Toplevel(self.root)
        window = tk.Toplevel()
        window.geometry("700x550"+ '+' + str(self.window_width) + '+' + str(0))
        window.title('このテキストを使いますか？')
        frame = Frame(window)
        frame.pack()
        video_audio_player = Video_Audio_player()
        frame.video_lavel = tk.Label(window)
        frame.video_lavel.pack()
        def end_process():
            try:
                video_audio_player.stop()
                window.destroy()
                self.thread_event.set()
            except Exception as e:
                print('error:play_video_for_subtitle.end_process method')
                print(e)
                self.log_frame.set_log('error:play_video_for_subtitle.end_process method')
            return
        def on_closing():
            self.subtitle_fix_bln.set(False)
            self.decided = True
            end_process()
            return
        window.protocol("WM_DELETE_WINDOW", on_closing)
        text = 'このテキストを使いますか?(このウィンドウを消すと、以降自動で字幕を付けます)'
        frame.label = tk.Label(window, text=text)
        frame.label.place(relx=0.01, rely=0.9)
        def select_decide():
            self.log_frame.set_log('この字幕で決定します')
            self.decided = True
            end_process()
            return
        def select_change():
            self.log_frame.set_log('字幕を変更します')
            try:
                with open(text_path, mode='w', encoding='utf8') as wf:
                    wf.write(subtitle_text_box.get())
            except Exception as e:
                print('error:play_video_for_subtitle')
                print(e)
                self.log_frame.set_log('error:play_video_for_subtitle')
            end_process()
            return
        select_widget_rel_y = 0.95
        select_widget_height = 25
        select_widget_relwidth = 0.1
        decide_button = tk.Button(window, text='決定', command=select_decide,
                                           highlightbackground=self.button_background, fg='black', highlightthickness=0)
        decide_button.place(relx=0.89, rely=select_widget_rel_y,
                                     relwidth=select_widget_relwidth, height=select_widget_height)
        subtitle_text = ''
        try:
            with open(text_path, mode='r', encoding='utf8') as rf:
                subtitle_text = rf.read()
        except Exception as e:
            print('error:play_video_for_subtitle')
            print(e)
            self.log_frame.set_log('error:play_video_for_subtitle')
        subtitle_text_box = tk.Entry(window, width=60)
        subtitle_text_box.insert(tk.END, subtitle_text)
        subtitle_text_box.place(relx=0.01, rely=select_widget_rel_y)
        change_button = tk.Button(window, text='変更', command=select_change,
                                           highlightbackground=self.button_background, fg='black', highlightthickness=0)
        change_button.place(relx=0.79, rely=select_widget_rel_y,
                                     relwidth=select_widget_relwidth, height=select_widget_height)
        try:
            video_audio_player.openfile(video_path, frame.video_lavel)
            video_audio_player.play()
        except Exception as e:
            print('error:play_video_for_subtitle method')
            print(e)
            self.log_frame.set_log('error:play_video_for_subtitle method')
            return
        return

    # 音声認識処理
    def speech_recognize(self, video_dir, video_list):
        os.chdir(video_dir)
        text_dir = self.make_dir(video_dir + '/' + video_dir.split('/')[-1] + '_subtitle')
        try:
            os.remove('.tmp')
        except:
            pass
        os.mkdir('.tmp')
        for i, video in enumerate(video_list):
            try:
                audio = '.tmp/' + video.split('.')[0] + '.wav'
                try:
                    command = [FFMPEG_PATH, '-i', video, audio]
                    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except Exception as e:
                    print('error:speech_recognize method')
                    print(e)
                    self.log_frame.set_log('error:speech_recognize method')
                r = sr.Recognizer()
                with sr.AudioFile(audio) as source:
                    audio_rec = r.record(source)
                os.remove(audio)
                s = r.recognize_google(audio_rec, language='ja')
                text_file_name = video.split('.')[0] + '.txt'
                with open(text_dir + '/' + text_file_name, mode='w', encoding='utf8') as f:
                    f.write(s)
            except:
                s = ''
                text_file_name = video.split('.')[0] + '.txt'
                with open(text_dir + '/' + text_file_name, mode='w', encoding='utf8') as f:
                    f.write(s)
            s = str(int((i+1)*100/len(video_list)))
            self.log_frame.set_log('音声テキスト化' + '{:>3}'.format(s) + '%完了')
        os.rmdir('.tmp')
        os.chdir(self.process_dir_path)
        return

# ----------------------------ファイル分割できそう(ここから)-------------------------------

    # srtファイル作成
    def make_srt(self, video_dir, video, text_path, text_list, subtitle_sections):
        def time_for_srt(time):
            result = []
            hours = int(time / 3600)
            result += str(hours).zfill(2) + ':'
            time -= hours * 3600
            minutes = int(time / 60)
            result += str(minutes).zfill(2) + ':'
            time -= minutes * 60
            seconds = int(time)
            result += str(seconds).zfill(2) + ','
            time -= seconds
            microseconds = round(time * 1000)
            result += str(microseconds).zfill(3)
            return ''.join(result)
        with open(video_dir + '/' + video.split('.')[0] + '_subtitle.srt', mode='w', encoding='utf8') as wf:
            for i, text in enumerate(text_list):
                wf.write(str(i + 1) + '\n')
                sec_num = i
                time_info = time_for_srt(subtitle_sections[sec_num][0]) + ' --> ' + time_for_srt(subtitle_sections[sec_num][1])
                wf.write(time_info + '\n')
                with open(text_path + '/' + text, mode='r', encoding='utf8') as rf:
                    wf.write(rf.read() + '\n\n')
        return

    # 動画の字幕焼き付け
    def print_subtitle(self, video_dir, video, srt_path):
        try:
            command = [FFMPEG_PATH, '-i', video_dir + '/' + video,
                       '-vf', 'subtitles=' + srt_path + '/' + video.split('.')[0] + '_subtitle.srt:force_style=\'FontSize=10\'',
                       '-y', video_dir + '/' + video.split('.')[0] + '_subtitle.mp4']
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print('error:print_subtitle method')
            print(e)
            self.log_frame.set_log('error:print_subtitle method')
            return
        return video_dir + '/' + video.split('.')[0] + '_subtitle.mp4'

    # 動画の結合
    def combine_video(self, video_dir, output_name):
        video_list = self.search_videos(video_dir)
        try:
            with open(video_dir + '/combine.txt', mode='w', encoding='utf8') as wf:
                for i, video in enumerate(video_list):
                    wf.write('file ' + video_dir + '/' + video + '\n')
            command = [FFMPEG_PATH, '-f', 'concat', '-safe', '0', '-i', video_dir + '/combine.txt',
                       '-c', 'copy', output_name + '_jumpcut_subtitle.mp4']
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print('error:combine_video method')
            print(e)
        return

# -------------------ファイル分割できそう(ここまで)-----------------------------

def main():
    Videdi()

if __name__ == '__main__':
    main()
