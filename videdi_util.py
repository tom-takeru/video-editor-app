import os
import subprocess
import sys
# 実行ファイルの絶対パスを変数に入れる
APP_PATH = '/'.join(sys.argv[0].split('/')[:-3])
# python videdi.pyで実行する場合
if APP_PATH == '':
    APP_PATH = '/Applications/videdi.app'
FFMPEG_PATH = APP_PATH + '/Contents/MacOS/ffmpeg'
FFPROBE_PATH = APP_PATH + '/Contents/MacOS/ffprobe'


# フォルダ内のvideoファイル名取得
def search_videos(search_dir):
    # フォルダ内のファイルやディレクトリ名を取得
    files = os.listdir(search_dir)
    # フォルダ内の動画ファイル名を取得
    files = [i for i in files if i[-4:].lower() == '.mov' or i[-4:].lower() == '.mp4']
    # 動画ファイル名を名前順で返す
    return sorted(files)


# 名前衝突を回避
def check_path(path):
    # その名前のpathが既に存在する場合
    if os.path.exists(path):
        i = 2
        if path[-1] != os.sep:
            file_path = os.path.splitext(path)
            while True:
                if not (os.path.exists(file_path[0] + str(i) + file_path[1])):
                    return file_path[0] + str(i) + file_path[1]
                i += 1
        else:
            while True:
                if not (os.path.exists(os.path.dirname(path) + str(i))):
                    return os.path.dirname(path) + str(i)
                i += 1
    else:
        return path


# 無音部分検出
def silence_sections(video):
    try:
        # 無音部分をffmpegで検出
        command = [FFMPEG_PATH, '-i', video, '-af', 'silencedetect=noise=-30dB:d=0.3', '-f', 'null', '-']
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
    # 無音部分の二次元配列に変換する
    silence_section_list = list(zip(*[iter(time_list)] * 2))
    return silence_section_list
