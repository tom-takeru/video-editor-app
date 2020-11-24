import os
from tkinter import filedialog

class utility:
    def __init__(self):
        return

    # フォルダ選択処理
    def select_folder(self, videdi):
        folder = videdi.folder_dir
        if len(folder) == 0:
            idir = os.path.abspath(os.path.dirname(__file__))
        else:
            idir = os.path.abspath(os.path.dirname(folder))
        # ジャンプカット動画作成・音声テキスト作成・字幕付き動画作成ボタン非表示化
        videdi.jumpcut_button.configure(state='disabled')
        videdi.speech_to_text_button.configure(state='disabled')
        videdi.add_subtitle_button.configure(state='disabled')

        videdi.folder_dir = filedialog.askdirectory(initialdir=idir)
        if len(videdi.folder_dir) == 0:
            videdi.folder_dir = folder
        if os.path.exists(videdi.folder_dir):
            if len(videdi.folder_dir) > videdi.folder_name_min:
                s = videdi.folder_dir.split('/')
                folder_name = s[-1]
            else:
                folder_name = videdi.folder_dir
            if videdi.utility.search_videos(videdi.folder_dir) != []:
                videdi.current_folder_var.set(folder_name + 'フォルダを選択中')
                # ジャンプカット動画作成・音声テキスト作成・字幕付き動画作成ボタン表示
                videdi.jumpcut_button.configure(state='normal')
                videdi.speech_to_text_button.configure(state='normal')
                videdi.add_subtitle_button.configure(state='normal')
            else:
                videdi.current_folder_var.set(folder_name + 'フォルダには処理できる動画ファイルがありません。')
        else:
            videdi.current_folder_var.set('フォルダが選択されていません。')
        return

    # 指定フォルダ内のvideoファイル名取得
    def search_videos(self, search_dir):
        files = os.listdir(search_dir)
        files = [i for i in files if i[-4:].lower() == '.mov' or i[-4:].lower() == '.mp4']
        return sorted(files)

    # フォルダを作成
    def make_folder(self, videdi, s):
        if os.path.exists('./' + s):
            i = 2
            while True:
                if not (os.path.exists('./' + s + str(i))):
                    new_folder = './' + s + str(i)
                    os.mkdir('./' + s + str(i))
                    break
                i += 1
        else:
            new_folder = './' + s
            os.mkdir('./' + s)

        videdi.frame.set_log(new_folder.split('/')[-1] + 'フォルダ作成')
        return new_folder
