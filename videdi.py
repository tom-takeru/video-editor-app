import os
import sys
import subprocess
import threading
import io
import shutil
import tkinter as tk
from tkinter import font
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import speech_recognition as sr

# 自作モジュール
import video_audio_player
import videdi_log
import videdi_util

# 出力のエンコードをUTF-8に設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# 実行ファイルの絶対パスを変数に入れる
APP_PATH = '/'.join(sys.argv[0].split('/')[:-3])
# python videdi.pyで実行する場合
if APP_PATH == '':
    FFMPEG_PATH = APP_PATH + '/usr/local/bin/ffmpeg'
    FFPROBE_PATH = APP_PATH + '/usr/local/bin/ffprobe'
else:
    FFMPEG_PATH = APP_PATH + '/Contents/MacOS/ffmpeg'
    FFPROBE_PATH = APP_PATH + '/Contents/MacOS/ffprobe'


WINDOW_WIDTH = 700
WINDOW_HEIGHT = 600


class AutoEditor:
    def __init__(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT):
        # TKクラスをインスタンス化
        self.root = tk.Tk()
        # ウィンドウのタイトルを設定
        self.root.title('AUTO EDITOR')
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
        # ウィンドウの大きさを固定
        self.root.resizable(False, False)
        # ウィンドウの背景の色を設定
        window_bg = '#ececec'
        self.root.configure(bg=window_bg)
        # ウィンドウの枠を指定
        self.root.configure(borderwidth=10, relief=tk.RIDGE)
        # フォントを指定
        bold_font = font.Font(self.root, size=16, weight='bold')
        button_font = font.Font(self.root, size=14)
        process_button_fg = 'red'
        self.button_background = window_bg
        # タイトルラベル
        pos_y = 0
        self.title_height = 100
        title_font = font.Font(self.root, family='impact', size=self.title_height, weight='bold')
        self.title_lab = tk.Label(text='AUTO EDITOR', font=title_font, foreground='lightgray', bg='black')
        self.title_lab.place(x=0, y=pos_y, relwidth=1.0, height=self.title_height)
        # 現在選択中フォルダラベル
        pos_y += self.title_height + 15
        height = 20
        self.process_dir = ''
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
        self.select_dir_button = tk.Button(text='フォルダの選択', command=self.select_dir, font=button_font,
                                           highlightbackground=self.button_background, fg='black', highlightthickness=0)
        self.select_dir_button.place(relx=(1 - self.sd_button_relwidth) / 2, y=self.sd_button_pos_y,
                                     relwidth=self.sd_button_relwidth, height=self.sd_button_height)
        # スクロール式のログラベル
        self.scroll_pos_y = self.sd_button_pos_y + self.sd_button_height + 15
        self.scroll_height = 200
        self.log_max = 100
        self.log_frame = videdi_log.LogFrame(master=self.root, log_max=self.log_max, bg=window_bg,
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
        self.run_choices_pos_y = self.scroll_pos_y + self.scroll_height + 10
        self.run_choices_lab = tk.Label(text='処理選択', font=bold_font)
        self.run_choices_lab.place(relx=0.05, y=self.run_choices_pos_y)
        # 処理のドロップダウンメニュー
        self.process_list = ['ジャンプカット', 'ジャンプカットして字幕を付ける']
        self.current_process = tk.StringVar(self.root)
        self.current_process.set(self.process_list[0])
        self.current_process.trace("w", self.set_options)
        self.process_opt = tk.OptionMenu(self.root, self.current_process, *self.process_list)
        self.process_opt.config(width=19)
        self.process_opt.place(relx=0.2, y=self.run_choices_pos_y)
        self.process_opt.config(state='disable')
        # オプションの列
        self.option_pos_y = self.run_choices_pos_y + 30
        self.option2_pos_y = self.option_pos_y + 25
        self.option3_pos_y = self.option2_pos_y + 25
        # オプション選択ラベル
        self.option_lab = tk.Label(text='オプション', font=bold_font)
        self.option_lab.place(relx=0.05, y=self.option_pos_y)
        # ジャンプカット修正チェックボックス
        self.jumpcut_fix_bln = tk.BooleanVar()
        self.jumpcut_fix_bln.set(False)
        self.jumpcut_fix_chk = tk.Checkbutton(self.root, variable=self.jumpcut_fix_bln, text='ジャンプカット修正')
        # 字幕修正チェックボックス
        self.subtitle_fix_bln = tk.BooleanVar()
        self.subtitle_fix_bln.set(False)
        self.subtitle_fix_chk = tk.Checkbutton(self.root, variable=self.subtitle_fix_bln, text='字幕修正')
        # 有音部分の最小時間を設定(単位:秒)
        self.min_time_lab = tk.Label(text='有音部分の最小時間')
        self.min_time_unit_lab = tk.Label(text='(秒)')
        self.min_time = tk.StringVar()
        self.min_time.set('0.5')
        self.min_time_spinbox = tk.Spinbox(self.root, format='%1.1f', textvariable=self.min_time, from_=0, to=1.0,
                                           increment=0.1, state='readonly')
        # 有音部分の前後の余裕を設定(単位:秒)
        self.margin_time_lab = tk.Label(text='有音部分の前後の余裕')
        self.margin_time_unit_lab = tk.Label(text='(秒)')
        self.margin_time = tk.StringVar()
        self.margin_time.set('0.1')
        self.margin_time_spinbox = tk.Spinbox(self.root, format='%1.2f', textvariable=self.margin_time, from_=0, to=1.0,
                                              increment=0.01, state='readonly')
        # オプションをセット
        self.set_options()
        # 実行ボタン
        self.run_button_pos_y = self.option3_pos_y + 40
        self.run_button_height = 25
        self.run_button_relwidth = 0.1
        self.run_button = tk.Button(text='実行', state='disable', command=self.run_button, font=button_font,
                                    highlightbackground=self.button_background, fg=process_button_fg,
                                    highlightthickness=0)
        self.run_button.place(relx=(1-self.run_button_relwidth)/2, y=self.run_button_pos_y,
                              relwidth=self.run_button_relwidth, height=self.run_button_height)
        self.thread_event = None
        self.next_action = ''
        self.decided = False
        self.player = video_audio_player.Video_Audio_player()
        self.cut_bln = tk.BooleanVar()

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
        self.process_opt.configure(state='disable')
        self.jumpcut_fix_chk.configure(state='disable')
        self.subtitle_fix_chk.configure(state='disable')
        self.min_time_lab.configure(foreground='#aaa')
        self.min_time_spinbox.configure(state='disable')
        self.min_time_unit_lab.configure(foreground='#aaa')
        self.margin_time_lab.configure(foreground='#aaa')
        self.margin_time_spinbox.configure(state='disable')
        self.margin_time_unit_lab.configure(foreground='#aaa')
        self.run_button.configure(state='disable')

    # ボタン有効化
    def enable_all_button(self):
        self.select_dir_button.configure(state='normal')
        self.log_reset_button.configure(state='normal')
        self.process_opt.configure(state='normal')
        self.jumpcut_fix_chk.configure(state='normal')
        self.subtitle_fix_chk.configure(state='normal')
        self.min_time_lab.configure(foreground='black')
        self.min_time_spinbox.configure(state='readonly')
        self.min_time_unit_lab.configure(foreground='black')
        self.margin_time_lab.configure(foreground='black')
        self.margin_time_spinbox.configure(state='readonly')
        self.margin_time_unit_lab.configure(foreground='black')
        self.run_button.configure(state='normal')

    # 処理の内容からオプションを表示
    def set_options(self, *args):
        # オプションを初期化
        self.jumpcut_fix_bln.set(False)
        self.subtitle_fix_bln.set(False)
        # オプションを非表示にする
        self.jumpcut_fix_chk.place_forget()
        self.subtitle_fix_chk.place_forget()
        # 動画が入ったフォルダが選択されていたら、ウィジェットを有効化する
        chk_state = 'disable'
        spinbox_state = 'disable'
        text_color = '#aaa'
        if self.dir_is_available:
            chk_state = 'normal'
            spinbox_state = 'readonly'
            text_color = 'black'
        # ジャンプカットのオプションをセット
        self.min_time_lab.place(relx=0.2, y=self.option2_pos_y)
        self.min_time_spinbox.place(relx=0.385, y=self.option2_pos_y, width=60)
        self.min_time_unit_lab.place(relx=0.47, y=self.option2_pos_y)
        self.min_time_lab.configure(foreground=text_color)
        self.min_time_spinbox.configure(state=spinbox_state)
        self.min_time_unit_lab.configure(foreground=text_color)
        self.margin_time_lab.place(relx=0.2, y=self.option3_pos_y)
        self.margin_time_spinbox.place(relx=0.385, y=self.option3_pos_y, width=60)
        self.margin_time_unit_lab.place(relx=0.47, y=self.option3_pos_y)
        self.margin_time_lab.configure(foreground=text_color)
        self.margin_time_spinbox.configure(state=spinbox_state)
        self.margin_time_unit_lab.configure(foreground=text_color)
        process = self.current_process.get()
        # 処理ごとにオプションの表示をセット
        if process == 'ジャンプカット':
            self.jumpcut_fix_chk.place(relx=0.2, y=self.option_pos_y)
            self.jumpcut_fix_chk.configure(state=chk_state)
        elif process == 'ジャンプカットして字幕を付ける':
            self.jumpcut_fix_chk.place(relx=0.2, y=self.option_pos_y)
            self.jumpcut_fix_chk.configure(state=chk_state)
            self.subtitle_fix_chk.place(relx=0.5, y=self.option_pos_y)
            self.subtitle_fix_chk.configure(state=chk_state)
        else:
            self.log_frame.set_log('error:set_options method')

    # 処理実行ボタンの処理
    def run_button(self):
        # ボタン無効化
        self.disable_all_button()
        # 現在選択中の処理を実行
        process = self.current_process.get()
        if process == 'ジャンプカット':
            thread = threading.Thread(target=self.jumpcut)
        elif process == 'ジャンプカットして字幕を付ける':
            thread = threading.Thread(target=self.jumpcut_and_add_subtitle2)
        else:
            self.log_frame.set_log('error:run_button method')
            return
        # スレッディング処理を開始
        thread.start()

    # フォルダ内の動画をジャンプカット
    def jumpcut(self):
        # ジャンプカット開始
        self.log_frame.set_big_log(self.process_dir.split('/')[-1] + 'フォルダ内の動画をジャンプカットします')
        video_list = videdi_util.search_videos(self.process_dir)
        for i, video in enumerate(video_list):
            video_name = os.path.split(video)[1]
            self.log_frame.set_log(video_name + 'をジャンプカットします ' + str(i+1) + '/' + str(len(video_list)))
            self.log_frame.set_log(video_name + 'の無音部分を検知します')
            cut_sections = videdi_util.silence_sections(video)
            if len(cut_sections) == 0:
                self.log_frame.set_log(video_name + 'には無音部分がありませんでした')
                continue
            video_sections = videdi_util.video_sections(cut_sections, video)
            video_sections = videdi_util.arrange_sections(video_sections, float(self.min_time.get()),
                                                          float(self.margin_time.get()))
            video_sections = videdi_util.all_sections(video_sections, video)
            jumpcut_dir, _ = self.cut_video(self.process_dir, video_sections, video)
            new_video = videdi_util.check_path(os.path.splitext(video)[0] + '_jumpcut.mp4')
            videdi_util.combine_video(jumpcut_dir, new_video)
            self.log_frame.set_log(video_name + 'をジャンプカットしました')
        # ボタン有効化
        self.enable_all_button()
        # ジャンプカット完了ログ
        self.log_frame.set_big_log(self.process_dir.split('/')[-1] + 'フォルダ内の動画をジャンプカットしました')

    # 音のある部分を出力
    def cut_video(self, video_dir, sections, video):
        digit = len(str(len(sections)))
        video_name = os.path.split(video)[1]
        jumpcut_dir = videdi_util.check_path(video_dir + '.tmp_' + os.path.splitext(video_name)[0] + '_jumpcut/')
        os.mkdir(jumpcut_dir)
        # sectionsにしたがって動画をカット
        for i in range(len(sections)):
            split_file = jumpcut_dir + os.path.splitext(video_name)[0] + '_' + format(i+1, '0>' + str(digit)) + '.mp4'
            command = [FFMPEG_PATH, '-i', video, '-ss', str(sections[i][0]), '-t',
                       str(sections[i][1] - sections[i][0]), split_file]
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # 進捗をパーセントで表示
            self.log_frame.set_progress_log('カット処理', i + 1, len(sections))
        self.log_frame.set_log('カット処理完了')
        if self.jumpcut_fix_bln.get():
            self.log_frame.set_log('ジャンプカットを修正します')
            fix_window = tk.Toplevel()
            fix_window.geometry(str(WINDOW_WIDTH) + 'x' + str(WINDOW_HEIGHT+100) + '+' + str(self.window_width) + '+0')
            fix_window.title('ジャンプカット修正')
            frame = tk.Frame(fix_window)
            frame.pack()
            line1_rel_y = 0.82
            line2_rel_y = 0.9
            button_height = 35
            button_relwidth = 0.05
            video_scale_var = tk.DoubleVar()
            fix_window.video_scale = tk.Scale(fix_window, variable=video_scale_var, orient=tk.HORIZONTAL,
                                              from_=1, to=len(sections))
            fix_window.video_scale.place(relx=0.04, rely=line1_rel_y, relwidth=0.92)
            # 再生ボタン
            fix_window.preview_button = tk.Button(fix_window, text='▶︎', command=self.fix_win_preview,
                                                  highlightbackground=self.button_background, fg='red', font=('', 30),
                                                  highlightthickness=0)
            fix_window.preview_button.place(relx=0.39, rely=line2_rel_y, relwidth=button_relwidth,
                                            height=button_height)
            # 前へボタン
            fix_window.back_button = tk.Button(fix_window, text='＜', command=self.fix_win_back, font=('', 30),
                                               highlightbackground=self.button_background, fg='black',
                                               highlightthickness=0)
            fix_window.back_button.place(relx=0.33, rely=line2_rel_y, relwidth=button_relwidth, height=button_height)
            # 次へボタン
            fix_window.go_button = tk.Button(fix_window, text='＞', command=self.fix_win_go, font=('', 30),
                                             highlightbackground=self.button_background, fg='black',
                                             highlightthickness=0)
            fix_window.go_button.place(relx=0.45, rely=line2_rel_y, relwidth=button_relwidth, height=button_height)
            fix_window.cut_chk = tk.Checkbutton(fix_window, variable=self.cut_bln, text='カットする')
            fix_window.cut_chk.place(relx=0.62, rely=line2_rel_y)
            # 完了ボタン
            fix_window.finish_button = tk.Button(fix_window, text='編集完了', command=self.fix_win_finish,
                                                 highlightbackground=self.button_background, fg='black',
                                                 highlightthickness=0)
            fix_window.finish_button.place(relx=0.85, rely=line2_rel_y, relwidth=0.1,
                                           height=25)
            fix_window.protocol("WM_DELETE_WINDOW", self.fix_win_finish)
            fix_window.bind('<Key>', self.fix_win_keyboard)
            fix_window.focus_set()
            current_video_scale_var = 1
            while True:
                split_file = jumpcut_dir + '/' + os.path.splitext(video_name)[0] + '_' \
                             + format(current_video_scale_var, '0>' + str(digit)) + '.mp4'
                # カットチェックボックス
                self.cut_bln.set(sections[current_video_scale_var - 1][2])
                frame.video_label = tk.Label(fix_window)
                frame.video_label.pack()
                # 動画を読み込む
                self.player.__init__()
                self.player.openfile(split_file, frame.video_label)
                self.thread_event = threading.Event()
                fix_window.preview_button.configure(state='normal')
                fix_window.back_button.configure(state='normal')
                fix_window.go_button.configure(state='normal')
                fix_window.cut_chk.configure(state='normal')
                fix_window.finish_button.configure(state='normal')
                fix_window.video_scale.configure(state='normal')
                # 動画を再生する
                self.player.play()
                self.thread_event.wait()
                fix_window.video_scale.configure(state='disable')
                fix_window.preview_button.configure(state='disable')
                fix_window.back_button.configure(state='disable')
                fix_window.go_button.configure(state='disable')
                fix_window.cut_chk.configure(state='disable')
                fix_window.finish_button.configure(state='disable')
                sections[current_video_scale_var-1][2] = self.cut_bln.get()
                frame.video_label.destroy()
                current_video_scale_var = int(video_scale_var.get())
                if self.next_action == 'preview':
                    continue
                elif self.next_action == 'back':
                    if int(current_video_scale_var) != 1:
                        current_video_scale_var -= 1
                        video_scale_var.set(current_video_scale_var)
                elif self.next_action == 'go':
                    if int(current_video_scale_var) != len(sections):
                        current_video_scale_var += 1
                        video_scale_var.set(current_video_scale_var)
                elif self.next_action == 'finish':
                    fix_window.destroy()
                    break
        video_num = 1
        new_sections = []
        for i in range(len(sections)):
            split_file = jumpcut_dir + os.path.splitext(video_name)[0] + '_' + format(i + 1, '0>' + str(digit)) + '.mp4'
            if sections[i][2]:
                os.remove(split_file)
            else:
                os.rename(split_file, jumpcut_dir + '/' + os.path.splitext(video_name)[0] + '_'
                          + format(video_num, '0>' + str(digit)) + '.mp4')
                video_num += 1
                new_sections.append(sections[i])
        if self.jumpcut_fix_bln.get():
            self.log_frame.set_log('ジャンプカット修正完了')
        new_jumpcut_dir = videdi_util.check_path(video_dir + os.path.splitext(video_name)[0] + '_jumpcut/')
        os.rename(jumpcut_dir, new_jumpcut_dir)
        return new_jumpcut_dir, new_sections

    # ジャンプカットして字幕を付ける処理
    def jumpcut_and_add_subtitle(self):
        # 音声テキスト作成開始ログ
        self.log_frame.set_big_log(self.process_dir.split('/')[-1] + 'フォルダ内の動画をジャンプカットして字幕を付けます')
        video_list = videdi_util.search_videos(self.process_dir)
        try:
            shutil.rmtree(self.process_dir + '.tmp/')
        except OSError:
            pass
        os.mkdir(self.process_dir + '.tmp/')
        for i, video in enumerate(video_list):
            video_name = os.path.split(video)[1]
            self.log_frame.set_log(video_name + 'をカットして字幕を付けます ' + str(i+1) + '/' + str(len(video_list)))
            self.log_frame.set_log(video_name + 'の無音部分を検知します')
            cut_sections = videdi_util.silence_sections(video)
            if len(cut_sections) == 0:
                self.log_frame.set_log('無音部分がありませんでした')
                continue
            video_sections = videdi_util.video_sections(cut_sections, video)
            video_sections = videdi_util.arrange_sections(video_sections, float(self.min_time.get()),
                                                          float(self.margin_time.get()))
            video_sections = videdi_util.all_sections(video_sections, video)
            self.log_frame.set_log(video_name + 'の音声認識のために動画をカットします')
            jumpcut_dir, video_sections = self.cut_video(self.process_dir + '.tmp/', video_sections, video)
            jumpcut_video_list = videdi_util.search_videos(jumpcut_dir)
            text_dir = self.process_dir + '.tmp/.tmp_' + video_name.split('.')[0] + '_text/'
            os.mkdir(text_dir)
            srt_dir = self.process_dir + '.tmp/.tmp_' + video_name.split('.')[0] + '_srt/'
            os.mkdir(srt_dir)
            subtitle_dir = self.process_dir + '.tmp/.tmp_' + video_name.split('.')[0] + '_subtitle/'
            os.mkdir(subtitle_dir)
            self.log_frame.set_log(video_name + 'の音声部分をテキスト化します')
            self.speech_recognize(jumpcut_video_list, text_dir)
            self.log_frame.set_log(video_name + 'の字幕を動画に焼き付けます')
            for j in range(len(jumpcut_video_list)):
                jumpcut_video_file = os.path.split(jumpcut_video_list[j])[1]
                text_file = text_dir + os.path.splitext(jumpcut_video_file)[0] + '.txt'
                srt_file = videdi_util.make_srt(srt_dir + os.path.splitext(jumpcut_video_file)[0] + '.srt',
                                                [text_file, ],
                                                [[0.0, video_sections[j][1]
                                                  - video_sections[j][0]], ])
                videdi_util.print_subtitle(jumpcut_video_list[j], srt_file, subtitle_dir
                                           + os.path.splitext(jumpcut_video_file)[0] + '_subtitle.mp4')
                self.log_frame.set_progress_log('字幕付け', j + 1, len(jumpcut_video_list))
            if self.subtitle_fix_bln.get():
                fix_window = tk.Toplevel()
                fix_window.geometry(str(WINDOW_WIDTH) + 'x' + str(WINDOW_HEIGHT+100)
                                    + '+' + str(self.window_width) + '+0')
                fix_window.title('字幕修正')
                frame = tk.Frame(fix_window)
                frame.pack()
                line1_rel_y = 0.7
                line2_rel_y = 0.76
                line3_rel_y = 0.8
                button_height = 25
                button_relwidth = 0.06
                video_scale_var = tk.DoubleVar()
                fix_window.video_scale = tk.Scale(fix_window, variable=video_scale_var, orient=tk.HORIZONTAL,
                                                  from_=1, to=len(jumpcut_video_list))
                fix_window.video_scale.place(relx=0.04, rely=line1_rel_y, relwidth=0.92)
                # 再生ボタン
                fix_window.preview_button = tk.Button(fix_window, text='▶︎', command=self.fix_win_preview,
                                                      highlightbackground=self.button_background, fg='red',
                                                      font=('', 30),
                                                      highlightthickness=0)
                fix_window.preview_button.place(relx=0.47, rely=line2_rel_y, relwidth=button_relwidth,
                                                height=button_height)
                # 前へボタン
                fix_window.back_button = tk.Button(fix_window, text='＜', command=self.fix_win_back, font=('', 30),
                                                   highlightbackground=self.button_background, fg='black',
                                                   highlightthickness=0)
                fix_window.back_button.place(relx=0.39, rely=line2_rel_y, relwidth=button_relwidth,
                                             height=button_height)
                # 次へボタン
                fix_window.go_button = tk.Button(fix_window, text='＞', command=self.fix_win_go, font=('', 30),
                                                 highlightbackground=self.button_background, fg='black',
                                                 highlightthickness=0)
                fix_window.go_button.place(relx=0.55, rely=line2_rel_y, relwidth=button_relwidth,
                                           height=button_height)
                fix_window.subtitle_text_box = ScrolledText(fix_window, font=("", 15), height=5, width=59)
                fix_window.subtitle_text_box.place(relx=0.01, rely=line3_rel_y)
                fix_window.finish_button = tk.Button(fix_window, text='編集完了', command=self.fix_win_finish,
                                                     highlightbackground=self.button_background, fg='black',
                                                     highlightthickness=0)
                fix_window.finish_button.place(relx=0.89, rely=line3_rel_y, relwidth=0.1, height=button_height)
                fix_window.protocol("WM_DELETE_WINDOW", self.fix_win_finish)
                current_video_scale_var = 1
                while True:
                    frame.video_label = tk.Label(fix_window)
                    frame.video_label.pack()
                    self.thread_event = threading.Event()
                    jumpcut_video = jumpcut_video_list[current_video_scale_var-1]
                    jumpcut_video_file = os.path.split(jumpcut_video)[1]
                    subtitle_video = subtitle_dir + os.path.splitext(jumpcut_video_file)[0] + '_subtitle.mp4'
                    text_file = text_dir + os.path.splitext(jumpcut_video_file)[0] + '.txt'
                    current_subtitle_text = ''
                    try:
                        with open(text_file, mode='r', encoding='utf8') as rf:
                            current_subtitle_text = rf.read()
                    except Exception as e:
                        print('error:play_video_for_subtitle')
                        print(e)
                    fix_window.subtitle_text_box.configure(state='normal')
                    fix_window.subtitle_text_box.delete('1.0', 'end')
                    fix_window.subtitle_text_box.insert('1.0', current_subtitle_text)
                    self.player.__init__()
                    self.player.openfile(subtitle_video, frame.video_label)
                    fix_window.back_button.configure(state='normal')
                    fix_window.go_button.configure(state='normal')
                    fix_window.preview_button.configure(state='normal')
                    fix_window.finish_button.configure(state='normal')
                    self.player.play()
                    self.thread_event.wait()
                    fix_window.back_button.configure(state='disable')
                    fix_window.go_button.configure(state='disable')
                    fix_window.preview_button.configure(state='disable')
                    fix_window.finish_button.configure(state='disable')
                    fix_window.subtitle_text_box.configure(state='disable')
                    new_subtitle_text = fix_window.subtitle_text_box.get('1.0', 'end -1c')
                    if not (new_subtitle_text == current_subtitle_text):
                        with open(text_file, mode='w', encoding='utf8') as wf:
                            wf.write(new_subtitle_text)
                        srt_file = videdi_util.make_srt(srt_dir + os.path.splitext(jumpcut_video_file)[0] + '.srt',
                                                        [text_file, ],
                                                        [[0.0, video_sections[current_video_scale_var-1][1]
                                                          - video_sections[current_video_scale_var-1][0]], ])
                        os.remove(subtitle_video)
                        videdi_util.print_subtitle(jumpcut_video, srt_file,
                                                   subtitle_dir + os.path.splitext(jumpcut_video_file)[0]
                                                   + '_subtitle.mp4')
                    frame.video_label.destroy()
                    current_video_scale_var = int(video_scale_var.get())
                    if self.next_action == 'finish':
                        fix_window.destroy()
                        break
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
                new_srt_dir = self.process_dir + '.tmp/' + os.path.splitext(video_name)[0] + '_srt/'
                os.rename(srt_dir, new_srt_dir)
                new_subtitle_dir = self.process_dir + '.tmp/' + os.path.splitext(video_name)[0] + '_subtitle/'
                os.rename(subtitle_dir, new_subtitle_dir)
                subtitle_dir = new_subtitle_dir
            # 動画を結合
            jumpcut_subtitle_video = videdi_util.check_path(os.path.splitext(video)[0] + '_jumpcut_subtitle.mp4')
            videdi_util.combine_video(subtitle_dir, jumpcut_subtitle_video)
            self.log_frame.set_log(video_name + 'をジャンプカットして字幕を付けました')
            new_text_dir = self.process_dir + '.tmp/' + os.path.splitext(video_name)[0] + '_text/'
            os.rename(text_dir, new_text_dir)
        # 一時的なフォルダを削除
        shutil.rmtree(self.process_dir + '.tmp/')
        # ボタン有効化
        self.enable_all_button()
        # 音声テキスト作成完了ログ
        self.log_frame.set_big_log(self.process_dir.split('/')[-1] + 'フォルダ内の動画をジャンプカットして字幕を付けました')
        return

    # ジャンプカットして字幕を付ける処理
    def jumpcut_and_add_subtitle2(self):
        # 音声テキスト作成開始ログ
        self.log_frame.set_big_log(self.process_dir.split('/')[-2] + 'フォルダ内の動画をジャンプカットして字幕を付けます')
        video_list = videdi_util.search_videos(self.process_dir)
        try:
            shutil.rmtree(self.process_dir + '.tmp/')
        except OSError:
            pass
        os.mkdir(self.process_dir + '.tmp/')
        for i, video in enumerate(video_list):
            video_name = os.path.split(video)[1]
            self.log_frame.set_log(video_name + 'をカットして字幕を付けます ' + str(i+1) + '/' + str(len(video_list)))
            self.log_frame.set_log(video_name + 'の無音部分を検知します')
            cut_sections = videdi_util.silence_sections(video)
            if len(cut_sections) == 0:
                self.log_frame.set_log('無音部分がありませんでした')
                continue
            video_sections = videdi_util.video_sections(cut_sections, video)
            video_sections = videdi_util.arrange_sections(video_sections, float(self.min_time.get()),
                                                          float(self.margin_time.get()))
            video_sections = videdi_util.all_sections(video_sections, video)
            self.log_frame.set_log(video_name + 'の音声認識のために動画をカットします')
            # jumpcut_dir, video_sections = self.cut_video(self.process_dir + '.tmp/', video_sections, video)
            jumpcut_dir = self.process_dir + '.tmp/.tmp_' + os.path.splitext(video_name)[0] + '_jumpcut/'
            os.mkdir(jumpcut_dir)
            text_dir = self.process_dir + '.tmp/.tmp_' + video_name.split('.')[0] + '_text/'
            os.mkdir(text_dir)
            srt_dir = self.process_dir + '.tmp/.tmp_' + video_name.split('.')[0] + '_srt/'
            os.mkdir(srt_dir)
            subtitle_dir = self.process_dir + '.tmp/.tmp_' + video_name.split('.')[0] + '_subtitle/'
            os.mkdir(subtitle_dir)
            self.devide_video_into_sections(video, video_sections, jumpcut_dir)
            jumpcut_video_list = videdi_util.search_videos(jumpcut_dir)
            digit = len(str(len(jumpcut_video_list)))
            self.log_frame.set_log(video_name + 'の音声部分をテキスト化します')
            self.speech_recognize(jumpcut_video_list, text_dir)
            self.log_frame.set_log(video_name + 'の字幕を動画に焼き付けます')
            for j in range(len(jumpcut_video_list)):
                jumpcut_video_file = os.path.split(jumpcut_video_list[j])[1]
                text_file = text_dir + os.path.splitext(jumpcut_video_file)[0] + '.txt'
                srt_file = videdi_util.make_srt(srt_dir + os.path.splitext(jumpcut_video_file)[0] + '.srt',
                                                [text_file, ],
                                                [[0.0, video_sections[j][1]
                                                  - video_sections[j][0]], ])
                videdi_util.print_subtitle(jumpcut_video_list[j], srt_file, subtitle_dir
                                           + os.path.splitext(jumpcut_video_file)[0] + '_subtitle.mp4')
                self.log_frame.set_progress_log('字幕付け', j + 1, len(jumpcut_video_list))
            if self.subtitle_fix_bln.get():
                fix_window = tk.Toplevel()
                fix_window.configure(borderwidth=10, relief=tk.RIDGE)
                fix_window.geometry(str(WINDOW_WIDTH) + 'x' + str(WINDOW_HEIGHT+100)
                                    + '+' + str(self.window_width) + '+0')
                fix_window.resizable(False, False)
                fix_window.title('字幕修正')
                frame = tk.Frame(fix_window)
                frame.pack()
                line1_rel_y = 0.72
                line2_rel_y = 0.78
                line3_rel_y = 0.82
                last_line_rel_y = 0.96
                scale_var_relx = 0.02
                scale_var_relwidth = 0.96
                button_height = 25
                button_relwidth = 0.06
                video_scale_var = tk.DoubleVar()
                fix_window.video_scale = tk.Scale(fix_window, variable=video_scale_var, orient=tk.HORIZONTAL,
                                                  from_=1, to=len(jumpcut_video_list), activebackground='red', width=10,
                                                  bd=0, cursor="sb_h_double_arrow")
                fix_window.video_scale.place(relx=scale_var_relx, rely=line1_rel_y, relwidth=scale_var_relwidth)
                # 再生ボタン
                fix_window.preview_button = tk.Button(fix_window, text='▶︎', command=self.fix_win_preview,
                                                      highlightbackground=self.button_background, fg='red',
                                                      font=('', 30),
                                                      highlightthickness=0)
                fix_window.preview_button.place(relx=0.47, rely=line2_rel_y, relwidth=button_relwidth,
                                                height=button_height)
                # 前へボタン
                fix_window.back_button = tk.Button(fix_window, text='＜', command=self.fix_win_back, font=('', 30),
                                                   highlightbackground=self.button_background, fg='black',
                                                   highlightthickness=0)
                fix_window.back_button.place(relx=0.39, rely=line2_rel_y, relwidth=button_relwidth,
                                             height=button_height)
                # 次へボタン
                fix_window.go_button = tk.Button(fix_window, text='＞', command=self.fix_win_go, font=('', 30),
                                                 highlightbackground=self.button_background, fg='black',
                                                 highlightthickness=0)
                fix_window.go_button.place(relx=0.55, rely=line2_rel_y, relwidth=button_relwidth,
                                           height=button_height)
                fix_window.cut_chk = tk.Checkbutton(fix_window, variable=self.cut_bln, text='カットする')
                fix_window.cut_chk.place(relx=0.62, rely=line2_rel_y)
                fix_window.subtitle_text_box = ScrolledText(fix_window, font=("", 15), height=5, width=57)
                fix_window.subtitle_text_box.place(relx=0.01, rely=line3_rel_y)
                fix_window.subtitle_text_box.bind('<Leave>', lambda n: fix_window.focus_set())
                fix_window.finish_button = tk.Button(fix_window, text='編集完了', command=self.fix_win_finish,
                                                     highlightbackground=self.button_background, fg='black',
                                                     highlightthickness=0)
                fix_window.finish_button.place(relx=0.89, rely=last_line_rel_y, relwidth=0.1, height=button_height)
                fix_window.protocol("WM_DELETE_WINDOW", self.fix_win_finish)
                current_video_scale_var = 1
                while True:
                    frame.video_label = tk.Label(fix_window)
                    frame.video_label.pack()
                    self.thread_event = threading.Event()
                    jumpcut_video = jumpcut_video_list[current_video_scale_var-1]
                    jumpcut_video_file = os.path.split(jumpcut_video)[1]
                    subtitle_video = subtitle_dir + os.path.splitext(jumpcut_video_file)[0] + '_subtitle.mp4'
                    text_file = text_dir + os.path.splitext(jumpcut_video_file)[0] + '.txt'
                    current_subtitle_text = ''
                    try:
                        with open(text_file, mode='r', encoding='utf8') as rf:
                            current_subtitle_text = rf.read()
                    except Exception as e:
                        print('error:play_video_for_subtitle')
                        print(e)
                    fix_window.subtitle_text_box.configure(state='normal')
                    fix_window.subtitle_text_box.delete('1.0', 'end')
                    fix_window.subtitle_text_box.insert('1.0', current_subtitle_text)
                    self.cut_bln.set(video_sections[current_video_scale_var - 1][2])
                    self.player.__init__()
                    self.player.openfile(subtitle_video, frame.video_label)
                    bind_id = fix_window.bind('<Key>', self.fix_win_keyboard)
                    fix_window.back_button.configure(state='normal')
                    fix_window.go_button.configure(state='normal')
                    fix_window.preview_button.configure(state='normal')
                    fix_window.finish_button.configure(state='normal')
                    self.player.play()
                    self.thread_event.wait()
                    fix_window.focus_set()
                    fix_window.unbind('<Key>', bind_id)
                    fix_window.back_button.configure(state='disable')
                    fix_window.go_button.configure(state='disable')
                    fix_window.preview_button.configure(state='disable')
                    fix_window.finish_button.configure(state='disable')
                    fix_window.subtitle_text_box.configure(state='disable')
                    new_subtitle_text = fix_window.subtitle_text_box.get('1.0', 'end -1c')
                    if not (new_subtitle_text == current_subtitle_text):
                        with open(text_file, mode='w', encoding='utf8') as wf:
                            wf.write(new_subtitle_text)
                        srt_file = videdi_util.make_srt(srt_dir + os.path.splitext(jumpcut_video_file)[0] + '.srt',
                                                        [text_file, ],
                                                        [[0.0, video_sections[current_video_scale_var-1][1]
                                                          - video_sections[current_video_scale_var-1][0]], ])
                        os.remove(subtitle_video)
                        videdi_util.print_subtitle(jumpcut_video, srt_file,
                                                   subtitle_dir + os.path.splitext(jumpcut_video_file)[0]
                                                   + '_subtitle.mp4')
                    video_sections[current_video_scale_var - 1][2] = self.cut_bln.get()
                    frame.video_label.destroy()
                    current_video_scale_var = int(video_scale_var.get())
                    if self.next_action == 'finish':
                        fix_window.destroy()
                        break
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
            self.log_frame.set_log(video_name + 'をジャンプカットして字幕を付けました')
            new_text_dir = self.process_dir + '.tmp/' + os.path.splitext(video_name)[0] + '_text/'
            os.rename(text_dir, new_text_dir)
        # 一時的なフォルダを削除
        # shutil.rmtree(self.process_dir + '.tmp/')
        # ボタン有効化
        self.enable_all_button()
        # 音声テキスト作成完了ログ
        self.log_frame.set_big_log(self.process_dir.split('/')[-2] + 'フォルダ内の動画をジャンプカットして字幕を付けました')
        return

    # 音声認識処理
    def speech_recognize(self, video_list, text_dir):
        try:
            os.remove(text_dir + '.tmp/')
        except OSError:
            pass
        os.mkdir(text_dir + '.tmp/')
        for i, video in enumerate(video_list):
            video_name = os.path.split(video)[1]
            audio = text_dir + '.tmp/' + os.path.splitext(video_name)[0] + '.wav'
            text_file = os.path.splitext(video_name)[0] + '.txt'
            try:
                command = [FFMPEG_PATH, '-i', video, audio]
                subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception as e:
                print('error:speech_recognize method')
                print(e)
                self.log_frame.set_log('error:speech_recognize method')
                return
            try:
                r = sr.Recognizer()
                with sr.AudioFile(audio) as source:
                    audio_rec = r.record(source)
                os.remove(audio)
                s = r.recognize_google(audio_rec, language='ja')
                if len(s) > 35:
                    string_sections = s.split(' ')
                    s = ''
                    for j in range(len(string_sections)):
                        if len(s) < 30:
                            s += string_sections[j]
                        else:
                            s += '\n' + string_sections[j]
                else:
                    string_sections = s.split(' ')
                    s = ''
                    for string in string_sections:
                        s += string
            except sr.UnknownValueError:
                # 何を言っているのかわからなかった場合は空の文字列にする
                s = ''
            except sr.RequestError:
                # レスポンスが返ってこなかった場合は全て空の文字列にする
                for j in range(i, len(video_list)):
                    video_name = os.path.split(video_list[j])[1]
                    text_file = os.path.splitext(video_name)[0] + '.txt'
                    with open(text_dir + '/' + text_file, mode='w', encoding='utf8') as f:
                        f.write('')
                self.log_frame.set_log('インターネット接続がないため、音声を認識をスキップします')
                break
            with open(text_dir + '/' + text_file, mode='w', encoding='utf8') as f:
                f.write(s)
            # 進捗をパーセントで表示
            self.log_frame.set_progress_log('音声テキスト化', i + 1, len(video_list))
        try:
            shutil.rmtree(text_dir + '.tmp/')
        except OSError:
            pass
        return

    def devide_video_into_sections(self, video, sections, output_dir):
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
        # self.log_frame.set_log("pressed" + repr(event.char))
        if str(event.widget) == '.!toplevel.!frame2':
            return
        if pressed_key == ' ':
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


def main():
    AutoEditor()


if __name__ == '__main__':
    main()
