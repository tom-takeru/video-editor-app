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


# 動画の長さを取得
def get_video_duration(video):
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
def video_sections(sections, video):
    time_list = []
    if sections[0][0] != 0.0:
        time_list.append(float(0.0))
        time_list.append(sections[0][0])
    for i in range(len(sections)-1):
        time_list.append(sections[i][1])
        time_list.append(sections[i+1][0])
    duration = get_video_duration(video)
    if sections[-1][1] < duration:
        time_list.append(sections[-1][1])
        time_list.append(duration)
    new_sections = list(zip(*[iter(time_list)] * 2))
    return new_sections


# sectionsに変更を加える
def arrange_sections(sections, min_time, margin_time):
    new_sections = []
    # 最小時間未満のセクションを削除した新しい配列を作る
    for i in range(len(sections)):
        if (sections[i][1] - sections[i][0]) < min_time:
            continue
        else:
            new_sections.append([sections[i][0] - margin_time, sections[i][1] + margin_time, True])
    if new_sections[0][0] < 0:
        new_sections[0][0] = 0.0
    for i in range(len(new_sections) - 1):
        if new_sections[i + 1][0] - new_sections[i][1] < 0.1:
            new_sections[i + 1][0] = (new_sections[i + 1][0] + new_sections[i][1]) / 2
            new_sections[i][1] = new_sections[i + 1][0]
    for i in range(len(new_sections)):
        new_sections[i][2] = True
    return new_sections


# ジャンプカットの修正をする場合のカットしない部分new_sectionsを作成
def all_sections(sections, video):
    new_sections = []
    if sections[0][0] > 0.5:
        new_sections.append([float(0.0), sections[0][0], False])
    for i in range(len(sections)-1):
        new_sections.append(sections[i])
        if sections[i][1] == sections[i+1][0]:
            continue
        new_sections.append([sections[i][1], sections[i+1][0], False])
    new_sections.append(sections[-1])
    duration = get_video_duration(video)
    if duration - sections[-1][1] > 0.5:
        new_sections.append([sections[-1][1], duration, False])
    return new_sections


# srtファイル作成
def make_srt(video_dir, video, text_path, text_list, subtitle_sections):
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
            time_info = time_for_srt(
                subtitle_sections[sec_num][0]) + ' --> ' + time_for_srt(subtitle_sections[sec_num][1])
            wf.write(time_info + '\n')
            with open(text_path + '/' + text, mode='r', encoding='utf8') as rf:
                wf.write(rf.read() + '\n\n')
    return


# 動画の字幕焼き付け
def print_subtitle(video_dir, video, srt_path):
    try:
        new_file_path = check_path(video_dir + '/' + video.split('.')[0] + '_subtitle.mp4')
        command = [FFMPEG_PATH, '-i', video_dir + '/' + video, '-vf',
                   'subtitles=' + srt_path + '/' + video.split('.')[0] + r"_subtitle.srt:force_style='FontSize=10'",
                   new_file_path]
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print('error:print_subtitle method')
        print(e)
        return
    return video_dir + '/' + video.split('.')[0] + '_subtitle.mp4'


# 動画の結合
def combine_video(video_dir, output_name):
    video_list = search_videos(video_dir)
    try:
        with open(video_dir + '/combine.txt', mode='w', encoding='utf8') as wf:
            for i, video in enumerate(video_list):
                wf.write('file ' + video_dir + '/' + video + '\n')
        output_name = check_path(output_name)
        command = [FFMPEG_PATH, '-f', 'concat', '-safe', '0', '-i', video_dir + '/combine.txt',
                   '-c', 'copy', output_name]
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.remove(video_dir + '/combine.txt')
    except Exception as e:
        print('error:combine_video method')
        print(e)
    return
