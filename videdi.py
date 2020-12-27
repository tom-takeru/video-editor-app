import os
import sys
import subprocess
import threading
import io
import shutil
import tkinter as tk
from tkinter import font
from tkinter import filedialog
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


class Videdi:
    def __init__(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT):
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
        current_dir_path = self.process_dir_path
        if len(current_dir_path) == 0:
            idir = os.path.abspath(os.path.dirname(__file__))
        else:
            idir = os.path.abspath(os.path.dirname(current_dir_path))
        # フォルダ選択済みフラグをおろす
        self.dir_is_available = False
        # 実行系ボタン無効化
        self.disable_all_button()
        # フォルダを選択する
        self.process_dir_path = filedialog.askdirectory(initialdir=idir)
        # フォルダが選択されなかった場合、直前に選択していたフォルダを選択
        if len(self.process_dir_path) == 0:
            self.process_dir_path = current_dir_path
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
            if len(videdi_util.search_videos(self.process_dir_path)) != 0:
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
        process = self.current_process.get()
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
            thread = threading.Thread(target=self.jumpcut_and_add_subtitle)
        else:
            self.log_frame.set_log('error:run_button method')
            return
        # スレッディング処理を開始
        thread.start()

    # フォルダ内の動画をジャンプカット
    def jumpcut(self):
        # ジャンプカット開始
        self.log_frame.set_big_log(self.process_dir_path.split('/')[-1] + 'フォルダ内の動画をジャンプカットします')
        os.chdir(self.process_dir_path)
        video_dir_path = self.process_dir_path
        video_list = videdi_util.search_videos(self.process_dir_path)
        for i, video in enumerate(video_list):
            self.log_frame.set_log(video + 'をジャンプカットします ' + str(i+1) + '/' + str(len(video_list)))
            self.log_frame.set_log(video + 'の無音部分を検知します')
            cut_sections = videdi_util.silence_sections(video)
            if len(cut_sections) == 0:
                self.log_frame.set_log(video + 'には無音部分がありませんでした')
                continue
            video_sections = videdi_util.video_sections(cut_sections, video)
            video_sections = videdi_util.arrange_sections(video_sections, float(self.min_time.get()),
                                                          float(self.margin_time.get()))
            video_sections = videdi_util.all_sections(video_sections, video)
            jumpcut_dir, _ = self.cut_video(video_dir_path, video_sections, video)
            videdi_util.combine_video(jumpcut_dir, os.path.splitext(video)[0] + '_jumpcut.mp4')
            self.log_frame.set_log(video + 'をジャンプカットしました')
        # ボタン有効化
        self.enable_all_button()
        # ジャンプカット完了ログ
        self.log_frame.set_big_log(self.process_dir_path.split('/')[-1] + 'フォルダ内の動画をジャンプカットしました')

# 一応怖いから取っておくーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー(ここから)

    # # 音のある部分を出力
    # def cut_video(self, video_dir, sections, video):
    #     digit = len(str(len(sections)))
    #     video_name = video.split('.')[0]
    #     jumpcut_dir = videdi_util.check_path(video_dir + '/' + video_name + '_jumpcut/')
    #     os.mkdir(jumpcut_dir)
    #     # sectionsにしたがって動画をカット
    #     for i in range(len(sections)):
    #         split_file = jumpcut_dir + '/' + video_name + '_' + format(i+1, '0>' + str(digit)) + '.mp4'
    #         command = [FFMPEG_PATH, '-i', video, '-ss', str(sections[i][0]), '-t',
    #                    str(sections[i][1] - sections[i][0]), split_file]
    #         subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #         # 進捗をパーセントで表示
    #         self.log_frame.set_progress_log('カット処理', i + 1, len(sections))
    #     self.log_frame.set_log('カット処理完了')
    #     cut_or_not = []
    #     for i in range(len(sections)):
    #         cut_or_not.append(not sections[i][2])
    #     if self.jumpcut_fix_bln.get():
    #         section_num = 0
    #         while True:
    #             split_file = jumpcut_dir + '/' + video_name + '_' + format(section_num+1, '0>' + str(digit)) + '.mp4'
    #             self.thread_event = threading.Event()
    #             thread = threading.Thread(target=self.play_video_for_cut, args=[split_file, cut_or_not, section_num])
    #             thread.start()
    #             self.thread_event.wait()
    #             thread.join()
    #             # 進捗をパーセントで表示
    #             self.log_frame.set_progress_log('カット選択処理', section_num + 1, len(sections))
    #             if self.next_action[0] == 'cut':
    #                 cut_or_not[section_num] = True
    #             elif self.next_action[0] == 'leave':
    #                 cut_or_not[section_num] = False
    #             elif self.next_action[0] == 'finish':
    #                 break
    #             if self.next_action[1] == 'back':
    #                 if section_num != 0:
    #                     section_num -= 1
    #             elif self.next_action[1] == 'go':
    #                 if section_num != len(sections)-1:
    #                     section_num += 1
    #     video_num = 1
    #     new_sections = []
    #     for i in range(len(sections)):
    #         split_file = jumpcut_dir + '/' + video_name + '_' + format(i + 1, '0>' + str(digit)) + '.mp4'
    #         if cut_or_not[i]:
    #             os.remove(split_file)
    #         else:
    #             os.rename(split_file,
    #                       jumpcut_dir + '/' + video_name + '_' + format(video_num, '0>' + str(digit)) + '.mp4')
    #             video_num += 1
    #             new_sections.append(sections[i])
    #     if self.jumpcut_fix_bln.get():
    #         self.log_frame.set_log('カット選択処理完了')
    #     return jumpcut_dir, new_sections
    #
    # # ジャンプカット修正のためのウィンドウを表示
    # def play_video_for_cut(self, video_path, cut_or_not, section_num):
    #     window = tk.Toplevel()
    #     window.geometry(str(WINDOW_WIDTH) + 'x' + str(WINDOW_HEIGHT) + '+' + str(self.window_width) + '+0')
    #     window.title('ジャンプカット修正')
    #     frame = tk.Frame(window)
    #     frame.pack()
    #     frame.video_label = tk.Label(window)
    #     frame.video_label.pack()
    #     player = video_audio_player.Video_Audio_player()
    #
    #     def end_process():
    #         player.stop()
    #         window.destroy()
    #         self.thread_event.set()
    #         return
    #
    #     def select_back():
    #         if cut_bln.get():
    #             self.next_action = ['cut', 'back']
    #         else:
    #             self.next_action = ['leave', 'back']
    #         end_process()
    #         return
    #
    #     def select_go():
    #         if cut_bln.get():
    #             self.next_action = ['cut', 'go']
    #         else:
    #             self.next_action = ['leave', 'go']
    #         end_process()
    #         return
    #
    #     def finish_fix():
    #         self.next_action = ['finish', '']
    #         end_process()
    #         return
    #     window.protocol("WM_DELETE_WINDOW", select_go)
    #     text = ''
    #     for i in range(51):
    #         if int(section_num*50/(len(cut_or_not)-1)) == i:
    #             text += '○'
    #         else:
    #             text += '・'
    #     var_font = font.Font(window, size=14)
    #     frame.label = tk.Label(window, text=text, font=var_font)
    #     frame.label.place(relx=0, rely=0.9, relwidth=1.0)
    #     select_button_rel_y = 0.95
    #     select_button_height = 25
    #     select_button_relwidth = 0.1
    #     # 前へボタン
    #     back_button = tk.Button(window, text='前へ', command=select_back, highlightbackground=self.button_background,
    #                            fg='black', highlightthickness=0)
    #     back_button.place(relx=0.39, rely=select_button_rel_y, relwidth=select_button_relwidth,
    #                      height=select_button_height)
    #     # 次へボタン
    #     go_button = tk.Button(window, text='次へ', command=select_go, highlightbackground=self.button_background,
    #                              fg='black', highlightthickness=0)
    #     go_button.place(relx=0.51, rely=select_button_rel_y, relwidth=select_button_relwidth,
    #                        height=select_button_height)
    #     # カットチェックボックス
    #     cut_bln = tk.BooleanVar()
    #     cut_bln.set(cut_or_not[section_num])
    #     cut_chk = tk.Checkbutton(window, variable=cut_bln, text='カットする')
    #     cut_chk.place(relx=0.62, rely=select_button_rel_y)
    #     # 完了ボタン
    #     finish_button = tk.Button(window, text='完了', command=finish_fix, highlightbackground=self.button_background,
    #                              fg='black', highlightthickness=0)
    #     finish_button.place(relx=0.9, rely=select_button_rel_y, relwidth=select_button_relwidth,
    #                        height=select_button_height)
    #     # 動画を読み込む
    #     player.openfile(video_path, frame.video_label)
    #     # 動画を再生する
    #     player.play()
    #     return

# 一応怖いから取っておくーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー(ここまで)

    # 音のある部分を出力
    def cut_video(self, video_dir, sections, video):
        digit = len(str(len(sections)))
        video_name = video.split('.')[0]
        jumpcut_dir = videdi_util.check_path(video_dir + '/' + video_name + '_jumpcut/')
        os.mkdir(jumpcut_dir)
        # sectionsにしたがって動画をカット
        for i in range(len(sections)):
            split_file = jumpcut_dir + '/' + video_name + '_' + format(i+1, '0>' + str(digit)) + '.mp4'
            command = [FFMPEG_PATH, '-i', video, '-ss', str(sections[i][0]), '-t',
                       str(sections[i][1] - sections[i][0]), split_file]
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # 進捗をパーセントで表示
            self.log_frame.set_progress_log('カット処理', i + 1, len(sections))
        self.log_frame.set_log('カット処理完了')
        cut_or_not = []
        for i in range(len(sections)):
            cut_or_not.append(not sections[i][2])
        if self.jumpcut_fix_bln.get():
            window = tk.Toplevel()
            window.geometry(str(WINDOW_WIDTH) + 'x' + str(WINDOW_HEIGHT) + '+' + str(self.window_width) + '+0')
            window.title('ジャンプカット修正')
            frame = tk.Frame(window)
            frame.pack()

            def end_process():
                player.stop()
                self.thread_event.set()
                return

            def select_back():
                if cut_bln.get():
                    self.next_action = ['cut', 'back']
                else:
                    self.next_action = ['leave', 'back']
                end_process()
                return

            def select_go():
                if cut_bln.get():
                    self.next_action = ['cut', 'go']
                else:
                    self.next_action = ['leave', 'go']
                end_process()
                return

            def finish_fix():
                self.next_action = ['finish', '']
                player.stop()
                window.destroy()
                self.thread_event.set()
                return

            window.protocol("WM_DELETE_WINDOW", finish_fix)
            section_num = 0
            while True:
                frame.video_label = tk.Label(window)
                frame.video_label.pack()
                self.thread_event = threading.Event()
                split_file = jumpcut_dir + '/' + video_name + '_' + format(section_num+1, '0>' + str(digit)) + '.mp4'
                text = ''
                for i in range(51):
                    if int(section_num * 50 / (len(cut_or_not) - 1)) == i:
                        text += '○'
                    else:
                        text += '・'
                var_font = font.Font(window, size=14)
                frame.label = tk.Label(window, text=text, font=var_font)
                frame.label.place(relx=0, rely=0.9, relwidth=1.0)
                select_button_rel_y = 0.95
                select_button_height = 25
                select_button_relwidth = 0.1
                # 前へボタン
                back_button = tk.Button(window, text='前へ', command=select_back, highlightbackground=self.button_background,
                                        fg='black', highlightthickness=0)
                back_button.place(relx=0.39, rely=select_button_rel_y, relwidth=select_button_relwidth,
                                  height=select_button_height)
                # 次へボタン
                go_button = tk.Button(window, text='次へ', command=select_go, highlightbackground=self.button_background,
                                      fg='black', highlightthickness=0)
                go_button.place(relx=0.51, rely=select_button_rel_y, relwidth=select_button_relwidth,
                                height=select_button_height)
                # カットチェックボックス
                cut_bln = tk.BooleanVar()
                cut_bln.set(cut_or_not[section_num])
                cut_chk = tk.Checkbutton(window, variable=cut_bln, text='カットする')
                cut_chk.place(relx=0.62, rely=select_button_rel_y)
                # 完了ボタン
                finish_button = tk.Button(window, text='完了', command=finish_fix, highlightbackground=self.button_background,
                                          fg='black', highlightthickness=0)
                finish_button.place(relx=0.9, rely=select_button_rel_y, relwidth=select_button_relwidth,
                                    height=select_button_height)
                player = video_audio_player.Video_Audio_player()
                # 動画を読み込む
                player.openfile(split_file, frame.video_label)
                # 動画を再生する
                player.play()
                self.thread_event.wait()
                frame.video_label.destroy()
                if self.next_action[0] == 'cut':
                    cut_or_not[section_num] = True
                elif self.next_action[0] == 'leave':
                    cut_or_not[section_num] = False
                elif self.next_action[0] == 'finish':
                    break
                if self.next_action[1] == 'back':
                    if section_num != 0:
                        section_num -= 1
                elif self.next_action[1] == 'go':
                    if section_num != len(sections)-1:
                        section_num += 1
        video_num = 1
        new_sections = []
        for i in range(len(sections)):
            split_file = jumpcut_dir + '/' + video_name + '_' + format(i + 1, '0>' + str(digit)) + '.mp4'
            if cut_or_not[i]:
                os.remove(split_file)
            else:
                os.rename(split_file,
                          jumpcut_dir + '/' + video_name + '_' + format(video_num, '0>' + str(digit)) + '.mp4')
                video_num += 1
                new_sections.append(sections[i])
        if self.jumpcut_fix_bln.get():
            self.log_frame.set_log('ジャンプカット修正完了')
        return jumpcut_dir, new_sections


    # ジャンプカットして字幕を付ける処理
    def jumpcut_and_add_subtitle(self):
        # 音声テキスト作成開始ログ
        self.log_frame.set_big_log(self.process_dir_path.split('/')[-1] + 'フォルダ内の動画をジャンプカットして字幕を付けます')
        os.chdir(self.process_dir_path)
        video_list = videdi_util.search_videos(self.process_dir_path)
        try:
            shutil.rmtree('.tmp')
        except OSError:
            pass
        os.mkdir('.tmp')
        subtitle_fix_bln = self.subtitle_fix_bln.get()
        jumpcut_fix_bln = self.jumpcut_fix_bln.get()
        for i, video in enumerate(video_list):
            self.log_frame.set_log(video + 'をカットして字幕を付けます ' + str(i+1) + '/' + str(len(video_list)))
            shutil.copyfile(video, '.tmp/' + video)
            self.log_frame.set_log(video + 'の無音部分を検知します')
            cut_sections = videdi_util.silence_sections(video)
            if len(cut_sections) == 0:
                self.log_frame.set_log('無音部分がありませんでした')
                continue
            video_sections = videdi_util.video_sections(cut_sections, video)
            video_sections = videdi_util.arrange_sections(video_sections, float(self.min_time.get()),
                                                          float(self.margin_time.get()))
            video_sections = videdi_util.all_sections(video_sections, video)
            self.log_frame.set_log(video + 'の音声認識のために動画をカットします')
            shutil.copyfile(video, '.tmp/' + video)
            jumpcut_dir, video_sections = self.cut_video(self.process_dir_path + '/.tmp', video_sections, video)
            jumpcut_dir = os.path.abspath(jumpcut_dir)
            jumpcut_video_list = videdi_util.search_videos(jumpcut_dir)
            self.speech_recognize(jumpcut_dir, jumpcut_video_list)
            text_path = os.path.abspath('./.tmp/' + jumpcut_dir.split('/')[-1] + '/' +
                                        jumpcut_dir.split('/')[-1] + '_subtitle')
            for j, jumpcut_video in enumerate(jumpcut_video_list):
                text_list = [jumpcut_video.split('.')[0] + '.txt', ]
                videdi_util.make_srt(jumpcut_dir, jumpcut_video, text_path, text_list,
                                     [[0.0, video_sections[j][1] - video_sections[j][0]], ])
                jumpcut_video_subtitle = videdi_util.print_subtitle(jumpcut_dir, jumpcut_video, jumpcut_dir)
                if self.subtitle_fix_bln.get():
                    self.decided = False
                    while not self.decided:
                        self.thread_event = threading.Event()
                        thread = threading.Thread(target=self.play_video_for_subtitle,
                                                  args=[jumpcut_video_subtitle,
                                                        text_path + '/' + os.path.splitext(jumpcut_video)[0] + '.txt'])
                        thread.start()
                        self.thread_event.wait()
                        os.remove(jumpcut_video_subtitle)
                        videdi_util.make_srt(jumpcut_dir, jumpcut_video, text_path, text_list,
                                             [[0.0, video_sections[j][1] - video_sections[j][0]], ])
                        jumpcut_video_subtitle = videdi_util.print_subtitle(jumpcut_dir, jumpcut_video, jumpcut_dir)
                        thread.join()
                # 進捗をパーセントで表示
                self.log_frame.set_progress_log('字幕付け', j + 1, len(jumpcut_video_list))
                os.remove(jumpcut_dir + '/' + jumpcut_video)
            # 動画を結合
            videdi_util.combine_video(jumpcut_dir, os.path.splitext(video)[0] + '_jumpcut_subtitle.mp4')
            self.jumpcut_fix_bln.set(jumpcut_fix_bln)
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
        window = tk.Toplevel()
        window.geometry(str(WINDOW_WIDTH) + 'x' + str(WINDOW_HEIGHT) + '+' + str(self.window_width) + '+0')
        window.title('字幕修正')
        frame = tk.Frame(window)
        frame.pack()
        player = video_audio_player.Video_Audio_player()
        frame.video_label = tk.Label(window)
        frame.video_label.pack()

        def end_process():
            player.stop()
            window.destroy()
            self.thread_event.set()
            return

        def on_closing():
            self.subtitle_fix_bln.set(False)
            self.decided = True
            end_process()
            return
        window.protocol("WM_DELETE_WINDOW", on_closing)
        text = '字幕を編集しますか?(このウィンドウを消すと、以降自動で字幕を付けます)'
        frame.label = tk.Label(window, text=text)
        frame.label.place(relx=0.01, rely=0.9)

        def select_decide():
            self.log_frame.set_log('決定します')
            self.decided = True
            with open(text_path, mode='w', encoding='utf8') as wf:
                wf.write(subtitle_text_box.get())
            end_process()
            return

        def select_preview():
            self.log_frame.set_log('プレビューします')
            with open(text_path, mode='w', encoding='utf8') as wf:
                wf.write(subtitle_text_box.get())
            end_process()
            return
        select_widget_rel_y = 0.94
        select_widget_height = 25
        select_widget_relwidth = 0.1
        decide_button = tk.Button(window, text='決定', command=select_decide, highlightbackground=self.button_background,
                                  fg='black', highlightthickness=0)
        decide_button.place(relx=0.89, rely=select_widget_rel_y, relwidth=select_widget_relwidth,
                            height=select_widget_height)
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
        change_button = tk.Button(window, text='プレビュー', command=select_preview,
                                  highlightbackground=self.button_background, fg='black', highlightthickness=0)
        change_button.place(relx=0.79, rely=select_widget_rel_y, relwidth=select_widget_relwidth,
                            height=select_widget_height)
        try:
            player.openfile(video_path, frame.video_label)
            player.play()
        except Exception as e:
            print('error:play_video_for_subtitle method')
            print(e)
            self.log_frame.set_log('error:play_video_for_subtitle method')
            return
        return

    # 音声認識処理
    def speech_recognize(self, video_dir, video_list):
        os.chdir(video_dir)
        text_dir = videdi_util.check_path(video_dir + '/' + video_dir.split('/')[-1] + '_subtitle/')
        os.mkdir(text_dir)
        try:
            os.remove('.tmp')
        except OSError:
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
            # 進捗をパーセントで表示
            self.log_frame.set_progress_log('音声テキスト化', i + 1, len(video_list))
        os.rmdir('.tmp')
        os.chdir(self.process_dir_path)
        return


def main():
    Videdi()


if __name__ == '__main__':
    main()
