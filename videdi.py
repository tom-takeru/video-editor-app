import tkinter as tk
from tkinter import *
import tkinter.font as font
import os
import subprocess
import threading
import shutil
import speech_recognition as sr

import sys
APP_PATH = '/'.join(sys.argv[0].split('/')[:-3])
# python videdi.pyで実行する時のため
if APP_PATH == "":
    APP_PATH = '/Applications/videdi.app'

class Videdi:
    def __init__(self, width=800, height=500):
        self.utility = videdi_utility.utility()

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
        window_bg = '#'+'ec'*3
        self.root.configure(bg=window_bg)
        # ウィンドウの枠を指定
        self.root.configure(borderwidth=10, relief=RIDGE)

        # フォントを指定
        bold_font = font.Font(self.root, size=16, weight='bold')
        button_font = font.Font(self.root, size=14)
        process_button_fg = 'red'
        button_background = window_bg

        # スレッド
        self.thread = None

        # タイトルラベル
        pos_y = 0
        self.title_height = 100
        title_font = font.Font(self.root, family='impact', size=self.title_height, weight='bold')
        self.title_lab = tk.Label(text='VIDEDI', font=title_font, foreground='lightgray', bg='black')
        self.title_lab.place(x=0, y=pos_y, relwidth=1.0, height=self.title_height)

        # 現在選択中フォルダラベル
        pos_y += self.title_height + 15
        height = 20
        self.folder_dir = ''
        self.folder_name_min = 40
        self.current_folder_var = tk.StringVar()
        self.current_folder_var.set('編集したい動画のあるフォルダを選択してください')
        self.current_folder_lab = tk.Label(textvariable=self.current_folder_var, font=bold_font, bg=window_bg)
        self.current_folder_lab.place(x=0, y=pos_y, relwidth=1.0, height=height)

        # フォルダ選択ボタン
        self.sf_button_pos_y = pos_y + height + 15
        self.sf_button_height = 25
        self.sf_button_relwidth = 0.2
        self.select_folder_button = tk.Button(text='フォルダの選択', command=self.select_folder_button,
                                              font=button_font,
                                              highlightbackground=button_background, fg='black', highlightthickness=0)
        self.select_folder_button.place(relx=(1 - self.sf_button_relwidth) / 2, y=self.sf_button_pos_y,
                                        relwidth=self.sf_button_relwidth, height=self.sf_button_height)
        self.select_folder_button.configure(relief=FLAT)

        # スクロール式のログラベル
        self.scroll_pos_y = self.sf_button_pos_y + self.sf_button_height + 15
        self.scroll_height = 200
        self.log_max = 100
        self.frame = videdi_log.LogFrame(master=self.root, log_max=self.log_max, bg=window_bg,
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

        # ジャンプカット動画の最小時間を設定(単位:秒)
        self.min_time = 0.5
        # ジャンプカット動画の前後の余裕を設定(単位:秒)
        self.margin_time = 0.1

        # ジャンプカット動画作成ボタン
        self.jc_button_relx = 0.05
        self.jc_button_pos_y = self.scroll_pos_y + self.scroll_height + 25
        self.jc_button_height = 25
        self.jc_button_relwidth = 0.2
        self.jumpcut_button = tk.Button(text='ジャンプカット動画作成', command=self.jumpcut_button,
                                        font=button_font,
                                        highlightbackground=button_background, fg=process_button_fg, highlightthickness=0)
        self.jumpcut_button.place(relx=self.jc_button_relx, y=self.jc_button_pos_y,
                                  relwidth=self.jc_button_relwidth, height=self.jc_button_height)
        self.jumpcut_button.configure(state='disabled')

        # 音声テキスト作成ボタン
        self.stt_button_relx = self.jc_button_relx + self.jc_button_relwidth * 1.1
        self.stt_button_pos_y = self.jc_button_pos_y
        self.stt_button_height = 25
        self.stt_button_relwidth = 0.15
        self.speech_to_text_button = tk.Button(text='音声テキスト作成', command=self.speech_to_text_button,
                                        font=button_font,
                                        highlightbackground=button_background, fg=process_button_fg, highlightthickness=0)
        self.speech_to_text_button.place(relx=self.stt_button_relx, y=self.stt_button_pos_y,
                                         relwidth=self.stt_button_relwidth, height=self.stt_button_height)
        self.speech_to_text_button.configure(state='disabled')

        # 字幕付き動画作成ボタン
        self.as_button_relx = self.stt_button_relx + self.stt_button_relwidth * 1.1
        self.as_button_pos_y = self.jc_button_pos_y
        self.as_button_height = 25
        self.as_button_relwidth = 0.15
        self.add_subtitle_button = tk.Button(text='字幕付き動画作成', command=self.add_subtitle_button,
                                        font=button_font,
                                        highlightbackground=button_background, fg=process_button_fg, highlightthickness=0)
        self.add_subtitle_button.place(relx=self.as_button_relx, y=self.as_button_pos_y,
                                       relwidth=self.as_button_relwidth, height=self.as_button_height)
        self.add_subtitle_button.configure(state='disabled')

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

    # ボタン非表示化
    def hide_all_button(self):
        self.select_folder_button.configure(state='disabled')
        self.log_reset_button.configure(state='disabled')
        self.jumpcut_button.configure(state='disabled')
        self.speech_to_text_button.configure(state='disabled')
        self.add_subtitle_button.configure(state='disabled')
        return

    # ボタン再表示
    def put_all_button(self):
        self.select_folder_button.configure(state='normal')
        self.log_reset_button.configure(state='normal')
        self.jumpcut_button.configure(state='normal')
        self.speech_to_text_button.configure(state='normal')
        self.add_subtitle_button.configure(state='normal')
        return

    # フォルダ選択ボタンの処理
    def select_folder_button(self):
        self.utility.select_folder(self)
        return

    # ジャンプカット動画作成ボタンの処理
    def jumpcut_button(self):
        # ボタン非表示化
        self.hide_all_button()
        # 自動カット処理をスレッディング
        self.thread = threading.Thread(target=videdi_jumpcut.jumpcut, args=(self, ))
        self.thread.start()
        return

    # 音声テキスト作成ボタンの処理
    def speech_to_text_button(self):
        # ボタン非表示化
        self.hide_all_button()
        # 音声テキスト作成処理をスレッディング
        self.thread = threading.Thread(target=self.speech_to_text)
        self.thread.start()
        return

    # 音声テキスト作成
    def speech_to_text(self):
        # 音声テキスト作成開始ログ
        self.frame.set_big_log(self.folder_dir.split('/')[-1] + 'フォルダ内の動画の音声テキスト作成開始')
        video_list = self.utility.search_videos(self.folder_dir)
        # 音声認識処理
        self.speech_recognize(self.folder_dir, video_list)
        # ボタンを再表示
        self.put_all_button()
        # 音声テキスト作成完了ログ
        self.frame.set_big_log(self.folder_dir.split('/')[-1] + 'フォルダ内の動画の音声テキスト作成完了')
        return

    # 音声認識処理
    def speech_recognize(self, video_dir, video_list):
        os.chdir(video_dir)
        text_folder = self.utility.make_folder(self, video_dir.split('/')[-1] + '_sub')
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
                text = video[0:-4] + '.txt'
                with open(text_folder + '/' + text, mode='w', encoding='utf8') as f:
                    f.write(s)
                self.frame.set_log(video + 'の音声をテキスト化しました ' + str(int((i+1)*100/len(video_list))) + '%完了')
            except Exception as e:
                print(e)
                self.frame.set_log(video + 'から音声は検出できませんでした ' + str(int((i+1)*100/len(video_list))) + '%完了')
        os.rmdir('.tmp')
        os.chdir(self.folder_dir)
        return

    # 字幕付き動画作成ボタンの処理
    def add_subtitle_button(self):
        # ボタン非表示化
        self.hide_all_button()
        # 字幕付き動画作成処理をスレッディング
        self.thread = threading.Thread(target=self.add_subtitle)
        self.thread.start()
        return

    # 字幕付き動画作成
    def add_subtitle(self):
        # 音声テキスト作成開始ログ
        self.frame.set_big_log(self.folder_dir.split('/')[-1] + 'フォルダ内の動画の字幕付き動画作成開始')
        os.chdir(self.folder_dir)
        video_list = self.utility.search_videos(self.folder_dir)
        os.mkdir('.tmp')
        for i, video in enumerate(video_list):
            self.frame.set_log(video + 'の字幕付き動画作成開始 ' + str(i+1) + '/' + str(len(video_list)))
            shutil.copyfile(video, '.tmp/' + video)
            cut_sections = videdi_jumpcut.silence_sections(self, video)
            video_sections = videdi_jumpcut.leave_sections(self, cut_sections, video)
            video_sections = videdi_jumpcut.arrange_sections(self, video_sections, self.min_time, self.margin_time)
            self.frame.set_log(video + 'の音声認識のために動画をカット')
            shutil.copyfile(video, '.tmp/' + video)
            jumpcut_folder = videdi_jumpcut.cut_video(self, self.folder_dir + '/.tmp', video_sections, video)
            jumpcut_video_list = self.utility.search_videos(jumpcut_folder)
            self.speech_recognize(jumpcut_folder, jumpcut_video_list)
            texts_path = './.tmp/' + jumpcut_folder.split('/')[-1] + '/' + jumpcut_folder.split('/')[-1] + '_sub'
            self.make_srt(self.folder_dir, texts_path, video, video_sections)
            self.print_sub(self.folder_dir, video)
        shutil.rmtree('.tmp')
        # ボタンを再表示
        self.put_all_button()
        # 音声テキスト作成完了ログ
        self.frame.set_big_log(self.folder_dir.split('/')[-1] + 'フォルダ内の動画の字幕付き動画作成完了')
        return

    # srtファイル作成
    def make_srt(self, video_dir, texts_path, video, video_sections):
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
        os.chdir(video_dir)
        text_list = sorted(os.listdir(texts_path))
        with open('./' + video[0:-4] + '_sub.srt', mode='w', encoding='utf8') as wf:
            for i, text in enumerate(text_list):
                wf.write(str(i + 1) + '\n')
                sec_num = int(text.split('_')[-1].split('.')[0]) - 1
                time_info = time_for_srt(video_sections[sec_num][0]) + ' --> ' + time_for_srt(video_sections[sec_num][1])
                wf.write(time_info + '\n')
                with open(texts_path + '/' + text, mode='r', encoding='utf8') as rf:
                    wf.write(rf.read() + '\n\n')
        return

    # 動画の字幕焼き付け
    def print_sub(self, video_dir, video):
        try:
            os.chdir(video_dir)
            command = [APP_PATH + '/Contents/MacOS/ffmpeg', '-i', video,
                       '-vf', 'subtitles=' + video[0:-4] + '_sub.srt:force_style=\'FontSize=10\'',
                       video[0:-4] + '_sub.mp4']
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.frame.set_log(video + 'の字幕付き動画作成完了')
        except Exception as e:
            print(e)
            self.frame.set_log('error004')
        os.chdir(self.folder_dir)
        return

def main():
    Videdi()

if __name__ == '__main__':
    # other files
    import videdi_log
    import videdi_jumpcut
    import videdi_utility
    main()