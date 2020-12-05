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

import sys
APP_PATH = '/'.join(sys.argv[0].split('/')[:-3])
# python videdi.pyで実行する時のため
if APP_PATH == '':
    APP_PATH = '/Applications/videdi.app'

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
    def __init__(self, width=800, height=550):
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
        button_background = window_bg

        # タイトルラベル
        pos_y = 0
        self.title_height = 100
        title_font = font.Font(self.root, family='impact', size=self.title_height, weight='bold')
        self.title_lab = tk.Label(text='VIDEDI', font=title_font, foreground='lightgray', bg='black')
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
        self.fld_bln = False
        self.sf_button_pos_y = pos_y + height + 15
        self.sf_button_height = 25
        self.sf_button_relwidth = 0.2
        self.select_dir_button = tk.Button(text='フォルダの選択', command=self.select_dir,
                                              font=button_font,
                                              highlightbackground=button_background, fg='black', highlightthickness=0)
        self.select_dir_button.place(relx=(1 - self.sf_button_relwidth) / 2, y=self.sf_button_pos_y,
                                        relwidth=self.sf_button_relwidth, height=self.sf_button_height)

        # スクロール式のログラベル
        self.scroll_pos_y = self.sf_button_pos_y + self.sf_button_height + 15
        self.scroll_height = 200
        self.log_max = 100
        self.frame = ScrollFrame(master=self.root, log_max=self.log_max, bg=window_bg,
                                 width=self.window_width, height=self.window_height)
        self.frame.place(x=0, y=self.scroll_pos_y, relwidth=1.0, height=self.scroll_height)
        self.frame.interior.bind('<ButtonPress-1>', self.move_start)
        self.frame.interior.bind('<B1-Motion>', self.move_move)
        self.frame.interior.bind('<MouseWheel>', self.mouse_y_scroll)

        # ログリセットボタン
        self.lr_button_relx = 0.85
        self.lr_button_pos_y = self.sf_button_pos_y + 15
        self.lr_button_height = 25
        self.lr_button_relwidth = 0.15
        self.log_reset_button = tk.Button(text='ログリセット', command=self.frame.reset_all_logs,
                                          font=button_font,
                                          highlightbackground=button_background, fg='black', highlightthickness=0)
        self.log_reset_button.place(relx=self.lr_button_relx, y=self.lr_button_pos_y,
                                    relwidth=self.lr_button_relwidth, height=self.lr_button_height)


        # 処理選択ラベル
        self.run_choices_pos_y = self.scroll_pos_y + self.scroll_height + 20
        self.run_choices_lab = tk.Label(text='処理選択', font=bold_font)
        self.run_choices_lab.place(relx=0.05, y=self.run_choices_pos_y)

        # 処理のドロップダウンメニュー
        self.process_list = ['ジャンプカット', '字幕を付ける', 'ジャンプカットして字幕を付ける']
        self.variable = tk.StringVar(self.root)
        self.variable.set(self.process_list[0])
        self.variable.trace("w", self.put_options)
        self.process_opt = tk.OptionMenu(self.root, self.variable, *self.process_list)
        self.process_opt.config(width=19)
        self.process_opt.place(relx=0.15, y=self.run_choices_pos_y)
        self.process_opt.config(state='disable')

        # オプション選択ラベル
        self.option_pos_y = self.run_choices_pos_y + 30
        self.option_lab = tk.Label(text='オプション', font=bold_font)
        self.option_lab.place(relx=0.05, y=self.option_pos_y)

        # ジャンプカット修正チェックボックス
        self.jc_modi_bln = tk.BooleanVar()
        self.jc_modi_bln.set(False)
        self.jc_modi_chk = tk.Checkbutton(self.root, variable=self.jc_modi_bln, text='ジャンプカット修正')
        # ジャンプカット動画の最小時間を設定(単位:秒)
        self.min_time = 0.5
        # ジャンプカット動画の前後の余裕を設定(単位:秒)
        self.margin_time = 0.1

        # 字幕修正チェックボックス
        self.sub_modi_bln = tk.BooleanVar()
        self.sub_modi_bln.set(False)
        self.sub_modi_chk = tk.Checkbutton(self.root, variable=self.sub_modi_bln, text='字幕修正')


        self.put_options()

        # 実行ボタン
        self.run_button_pos_y = self.option_pos_y + 30
        self.run_button_height = 25
        self.run_button_relwidth = 0.1
        self.run_button = tk.Button(text='実行', state='disable', command=self.run_button, font=button_font,
                                    highlightbackground=button_background, fg=process_button_fg, highlightthickness=0)
        self.run_button.place(relx=(1-self.run_button_relwidth)/2, y=self.run_button_pos_y,
                                  relwidth=self.run_button_relwidth, height=self.run_button_height)

        # メインループでイベント待ち
        if __name__ == '__main__':
            self.root.mainloop()

    def move_start(self, event):
        self.frame.canvas.scan_mark(event.x, event.y)

    def move_move(self, event):
        self.frame.canvas.scan_dragto(event.x, event.y, gain=1)

    def mouse_y_scroll(self, event):
        if event.delta > 0:
            self.frame.canvas.yview_scroll(-1, 'units')
        elif event.delta < 0:
            self.frame.canvas.yview_scroll(1, 'units')

    # フォルダ選択処理
    def select_dir(self):
        dir = self.process_dir
        if len(dir) == 0:
            idir = os.path.abspath(os.path.dirname(__file__))
        else:
            idir = os.path.abspath(os.path.dirname(dir))
        self.fld_bln = False
        # ボタン無効化
        self.process_opt.configure(state='disable')
        self.jc_modi_chk.configure(state='disable')
        self.sub_modi_chk.configure(state='disable')
        self.run_button.configure(state='disabled')
        self.process_dir = filedialog.askdirectory(initialdir=idir)
        if len(self.process_dir) == 0:
            self.process_dir = dir
        if os.path.exists(self.process_dir):
            if len(self.process_dir) > self.dir_name_min:
                s = self.process_dir.split('/')
                dir_name = s[-1]
            else:
                dir_name = self.process_dir
            if self.search_videos(self.process_dir) != []:
                self.current_dir_var.set(dir_name + 'フォルダを選択中')
                self.fld_bln = True
                # 処理のボタンの有効化
                self.process_opt.configure(state='normal')
                self.run_button.configure(state='normal')
                self.put_options()
            else:
                self.current_dir_var.set(dir_name + 'フォルダには処理できる動画ファイルがありません。')
        else:
            self.current_dir_var.set('フォルダが選択されていません。')
        return

    # 指定フォルダ内のvideoファイル名取得
    def search_videos(self, search_dir):
        files = os.listdir(search_dir)
        files = [i for i in files if i[-4:].lower() == '.mov' or i[-4:].lower() == '.mp4']
        return sorted(files)

    # フォルダを作成
    def make_dir(self, s):
        if os.path.exists('./' + s):
            i = 2
            while True:
                if not (os.path.exists('./' + s + str(i))):
                    new_dir = './' + s + str(i)
                    os.mkdir('./' + s + str(i))
                    break
                i += 1
        else:
            new_dir = './' + s
            os.mkdir('./' + s)
        return new_dir

    # ボタン無効化
    def disable_all_button(self):
        self.select_dir_button.configure(state='disabled')
        self.log_reset_button.configure(state='disabled')
        self.process_opt.configure(state='disable')
        self.jc_modi_chk.configure(state='disable')
        self.sub_modi_chk.configure(state='disable')
        self.run_button.configure(state='disable')
        return

    # ボタン有効化
    def enable_all_button(self):
        self.select_dir_button.configure(state='normal')
        self.log_reset_button.configure(state='normal')
        self.process_opt.configure(state='normal')
        self.jc_modi_chk.configure(state='normal')
        self.sub_modi_chk.configure(state='normal')
        self.run_button.configure(state='normal')
        return

    # 処理の内容からオプションを表示
    def put_options(self, *args):
        self.jc_modi_chk.place_forget()
        self.sub_modi_chk.place_forget()
        process = self.variable.get()
        fld_is = 'disable'
        if self.fld_bln:
            fld_is = 'normal'
        if process == 'ジャンプカット':
            self.jc_modi_chk.place(relx=0.15, y=self.option_pos_y)
            self.jc_modi_chk.configure(state=fld_is)
        elif process == '字幕を付ける':
            self.sub_modi_chk.place(relx=0.15, y=self.option_pos_y)
            self.sub_modi_chk.configure(state=fld_is)
        elif process == 'ジャンプカットして字幕を付ける':
            self.jc_modi_chk.place(relx=0.15, y=self.option_pos_y)
            self.jc_modi_chk.configure(state=fld_is)
            self.sub_modi_chk.place(relx=0.35, y=self.option_pos_y)
            self.sub_modi_chk.configure(state=fld_is)
        else:
            self.frame.set_log('error:put_options method')
            return
        return

    # 処理実行ボタンの処理
    def run_button(self):
        # ボタン無効化
        self.disable_all_button()
        process = self.variable.get()
        if process == 'ジャンプカット':
            thread = threading.Thread(target=self.jumpcut)
        elif process == '字幕を付ける':
            thread = threading.Thread(target=self.addsub)
        elif process == 'ジャンプカットして字幕を付ける':
            thread = threading.Thread(target=self.jc_and_addsub)
        else:
            self.frame.set_log('error:run_button method')
            return
        thread.start()
        return

    # フォルダ内の動画をジャンプカット
    def jumpcut(self):
        # ジャンプカット開始
        self.frame.set_big_log(self.process_dir.split('/')[-1] + 'フォルダ内の動画をジャンプカットします')
        os.chdir(self.process_dir)
        video_dir = os.path.abspath(self.process_dir)
        video_list = self.search_videos(self.process_dir)
        for i, video in enumerate(video_list):
            self.frame.set_log(video + 'をジャンプカットします ' + str(i+1) + '/' + str(len(video_list)))
            self.frame.set_log(video + 'の無音部分を検知します')
            cut_sections = self.silence_sections(video)
            # print('\ncut_sections')
            # print(cut_sections)
            if len(cut_sections) == 0:
                self.frame.set_log(video + 'には無音部分がありませんでした')
                continue
            video_sections = self.leave_sections(cut_sections, video)
            # print('\nleave_sections')
            # print(video_sections)
            video_sections = self.arrange_sections(video_sections, self.min_time, self.margin_time)
            # print('\narrange_sections')
            # print(video_sections)
            self.cut_video(video_dir, video_sections, video)
            self.frame.set_log(video + 'をジャンプカットしました')
        # ボタン有効化
        self.enable_all_button()
        # ジャンプカット完了ログ
        self.frame.set_big_log(self.process_dir.split('/')[-1] + 'フォルダ内の動画をジャンプカットしました')
        return

    # 無音部分検出
    def silence_sections(self, video):
        try:
            command = [APP_PATH + '/Contents/MacOS/ffmpeg', '-i', video, '-af',
                                     'silencedetect=noise=-30dB:d=0.3', '-f', 'null', '-']
            output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print(e)
            self.frame.set_log('error:silence_sections method')
            return

        s = str(output)
        lines = s.split('\\n')
        time_list = []
        for line in lines:
            if 'silencedetect' in line:
                words = line.split(' ')
                for i in range(len(words)):
                    if 'silence_start' in words[i]:
                        time_list.append(float(words[i + 1]))
                    if 'silence_end' in words[i]:
                        time_list.append(float(words[i + 1]))
        silence_section_list = list(zip(*[iter(time_list)] * 2))
        return silence_section_list

    # カット部分のsectionsをカットしない部分のnew_sectionsに変換
    def leave_sections(self, sections, video):
        try:
            duration = 0
            command = [APP_PATH + '/Contents/MacOS/ffprobe', video, '-hide_banner', '-show_format']
            output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print(e)
            self.frame.set_log('error:leave_sections method')
            return
        s = str(output)
        lines = s.split('\\n')
        for line in lines:
            words = line.split('=')
            if words[0] == 'duration':
                duration = float(words[1])
                break
        time_list = []
        if sections[0][0] == 0.0:
            for i in range(len(sections)-1):
                time_list.append(sections[i][1])
                time_list.append(sections[i+1][0])
            if sections[-1][1] < duration:
                time_list.append(sections[-1][1])
                time_list.append(duration)
        else:
            time_list.append(float(0.0))
            time_list.append(sections[0][0])
            for i in range(len(sections)-1):
                time_list.append(sections[i][1])
                time_list.append(sections[i+1][0])
            if sections[-1][1] < duration:
                time_list.append(sections[-1][1])
                time_list.append(duration)
        new_sections = list(zip(*[iter(time_list)] * 2))
        return new_sections

    # sectionsにoptionで変更を加える
    def arrange_sections(self, sections, min_time, margin_time):
        new_sections = []
        if sections[0][0] < margin_time and (sections[0][1] - sections[0][1]) >= min_time:
            sections[0][0] += margin_time
        for i in range(len(sections)):
            if (sections[i][1] - sections[i][0]) < min_time:
                continue
            else:
                new_sections.append([sections[i][0] - margin_time, sections[i][1] + margin_time])
        try:
            new_sections[-1][1] -= margin_time
        except Exception as e:
            print(e)
            self.frame.set_log('error:arrange_sections method')
        return new_sections

    # 音のある部分を出力
    def cut_video(self, video_dir, sections, video):
        os.chdir(video_dir)
        digit = len(str(len(sections)))
        video_name = video.split('.')[0]
        jumpcut_dir = self.make_dir(video_name + '_jumpcut')
        for i in range(len(sections)):
            split_file = jumpcut_dir + '/' + video_name + '_' + format(i+1, '0>' + str(digit)) + '.mp4'
            subprocess.run(
                [APP_PATH + '/Contents/MacOS/ffmpeg', '-i', video, '-ss', str(sections[i][0]), '-t',
                 str(sections[i][1] - sections[i][0]), split_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # logを表示
            if int((i+1)*100/len(sections)) != int(i*100/len(sections)):
                self.frame.set_log(video + '   ' + str(int(((i+1) * 100) / len(sections))) + '%完了')
        return jumpcut_dir

    # 字幕付き動画作成
    def addsub(self):
        # 音声テキスト作成開始ログ
        self.frame.set_big_log(self.process_dir.split('/')[-1] + 'フォルダ内の動画に字幕を付けます')
        os.chdir(self.process_dir)
        video_list = self.search_videos(self.process_dir)
        os.mkdir('.tmp')
        for i, video in enumerate(video_list):
            self.frame.set_log(video + 'に字幕を付けます ' + str(i+1) + '/' + str(len(video_list)))
            shutil.copyfile(video, '.tmp/' + video)
            self.frame.set_log(video + 'の無音部分を検知します')
            cut_sections = self.silence_sections(video)
            video_sections = self.leave_sections(cut_sections, video)
            video_sections = self.arrange_sections(video_sections, self.min_time, self.margin_time)
            self.frame.set_log(video + 'の音声認識のために動画を音声部分ごとにカットします')
            shutil.copyfile(video, '.tmp/' + video)
            jumpcut_dir = self.cut_video(self.process_dir + '/.tmp', video_sections, video)
            jumpcut_video_list = self.search_videos(jumpcut_dir)
            self.speech_recognize(jumpcut_dir, jumpcut_video_list)
            text_path = os.path.abspath('./.tmp/' + jumpcut_dir.split('/')[-1] + '/' + jumpcut_dir.split('/')[-1] + '_sub')
            text_list = sorted(os.listdir(text_path))
            self.make_srt(self.process_dir, video, text_path, text_list, video_sections)
            self.print_sub(self.process_dir, video, self.process_dir)
            self.frame.set_log(video + 'に字幕を付けました。')
        shutil.rmtree('.tmp')
        # ボタン有効化
        self.enable_all_button()
        # 音声テキスト作成完了ログ
        self.frame.set_big_log(self.process_dir.split('/')[-1] + 'フォルダ内の動画に字幕を付けました')
        return

    # ジャンプカットした動画を音声認識して結合
    def jc_and_addsub(self):
        # 音声テキスト作成開始ログ
        self.frame.set_big_log(self.process_dir.split('/')[-1] + 'フォルダ内の動画をジャンプカットして字幕を付けます')
        os.chdir(self.process_dir)
        video_list = self.search_videos(self.process_dir)
        if os.path.exists('.tmp'):
            shutil.rmtree('.tmp')
        os.mkdir('.tmp')
        for i, video in enumerate(video_list):
            self.frame.set_log(video + 'をジャンプカットして字幕を付けます ' + str(i+1) + '/' + str(len(video_list)))
            shutil.copyfile(video, '.tmp/' + video)
            self.frame.set_log(video + 'の無音部分を検知します')
            cut_sections = self.silence_sections(video)
            video_sections = self.leave_sections(cut_sections, video)
            video_sections = self.arrange_sections(video_sections, self.min_time, self.margin_time)
            self.frame.set_log(video + 'の音声認識のために動画をカットします')
            shutil.copyfile(video, '.tmp/' + video)
            jumpcut_dir = os.path.abspath(self.cut_video(self.process_dir + '/.tmp', video_sections, video))
            jumpcut_video_list = self.search_videos(jumpcut_dir)
            self.speech_recognize(jumpcut_dir, jumpcut_video_list)
            text_path = os.path.abspath('./.tmp/' + jumpcut_dir.split('/')[-1] + '/' + jumpcut_dir.split('/')[-1] + '_sub')
            for i, jc_video in enumerate(jumpcut_video_list):
                text_list = [jc_video[0:-4] + '.txt', ]
                self.make_srt(jumpcut_dir, jc_video, text_path, text_list, [[0.0, video_sections[i][1] - video_sections[i][0]], ])
                self.print_sub(jumpcut_dir, jc_video, jumpcut_dir)
                self.frame.set_log(jc_video + 'に字幕を付けました')
                os.remove(jumpcut_dir + '/' + jc_video)
            self.combine_video(jumpcut_dir, video[0:-4])
        shutil.rmtree('.tmp')
        # ボタン有効化
        self.enable_all_button()
        # 音声テキスト作成完了ログ
        self.frame.set_big_log(self.process_dir.split('/')[-1] + 'フォルダ内の動画をジャンプカットして字幕を付けました')
        return

    # # 音声テキスト作成
    # def speech_to_text(self):
    #     # 音声テキスト作成開始ログ
    #     self.frame.set_big_log(self.process_dir.split('/')[-1] + 'フォルダ内の動画の音声テキスト作成開始')
    #     video_list = self.search_videos(self.process_dir)
    #     # 音声認識処理
    #     self.speech_recognize(self.process_dir, video_list)
    #     # ボタン有効化
    #     self.enable_all_button()
    #     # 音声テキスト作成完了ログ
    #     self.frame.set_big_log(self.process_dir.split('/')[-1] + 'フォルダ内の動画の音声テキスト作成完了')
    #     return

    # 音声認識処理
    def speech_recognize(self, video_dir, video_list):
        os.chdir(video_dir)
        text_dir = self.make_dir(video_dir.split('/')[-1] + '_sub')
        os.mkdir('.tmp')
        for i, video in enumerate(video_list):
            try:
                audio = '.tmp/' + video[0:-4] + '.wav'
                command = [APP_PATH + '/Contents/MacOS/ffmpeg', '-i', video, audio]
                subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                r = sr.Recognizer()
                with sr.AudioFile(audio) as source:
                    audio_rec = r.record(source)
                os.remove(audio)
                s = r.recognize_google(audio_rec, language='ja')
                text_file_name = video[0:-4] + '.txt'
                with open(text_dir + '/' + text_file_name, mode='w', encoding='utf8') as f:
                    f.write(s)
                self.frame.set_log(video + 'の音声をテキスト化しました ' + str(int((i+1)*100/len(video_list))) + '%完了')
            except Exception as e:
                # print(e)
                s = ''
                text_file_name = video[0:-4] + '.txt'
                with open(text_dir + '/' + text_file_name, mode='w', encoding='utf8') as f:
                    f.write(s)
                self.frame.set_log(video + 'から音声は検出できませんでした ' + str(int((i+1)*100/len(video_list))) + '%完了')
        os.rmdir('.tmp')
        os.chdir(self.process_dir)
        return

    # srtファイル作成
    def make_srt(self, video_dir, video, text_path, text_list, sub_sections):
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
        with open(video_dir + '/' + video[0:-4] + '_sub.srt', mode='w', encoding='utf8') as wf:
            for i, text in enumerate(text_list):
                wf.write(str(i + 1) + '\n')
                sec_num = i
                time_info = time_for_srt(sub_sections[sec_num][0]) + ' --> ' + time_for_srt(sub_sections[sec_num][1])
                wf.write(time_info + '\n')
                with open(text_path + '/' + text, mode='r', encoding='utf8') as rf:
                    wf.write(rf.read() + '\n\n')
        return

    # 動画の字幕焼き付け
    def print_sub(self, video_dir, video, srt_path):
        try:
            command = [APP_PATH + '/Contents/MacOS/ffmpeg', '-i', video_dir + '/' + video,
                       '-vf', 'subtitles=' + srt_path + '/' + video[0:-4] + '_sub.srt:force_style=\'FontSize=10\'',
                       video_dir + '/' + video[0:-4] + '_sub.mp4']
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print(e)
            self.frame.set_log('error:print_sub method')
            return
        return

    # 動画の結合
    def combine_video(self, video_dir, output_name):
        video_list = self.search_videos(video_dir)
        try:
            with open(video_dir + '/combine.txt', mode='w', encoding='utf8') as wf:
                for i, video in enumerate(video_list):
                    wf.write('file ' + video_dir + '/' + video + '\n')
            command = [APP_PATH + '/Contents/MacOS/ffmpeg', '-f', 'concat', '-safe', '0', '-i', video_dir + '/combine.txt',
                       '-c', 'copy', output_name + '_jc_sub.mp4']
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print(e)
            self.frame.set_log('error:combine_video method')
        return

def main():
    Videdi()

if __name__ == '__main__':
    main()
