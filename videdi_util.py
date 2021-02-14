import os
import subprocess
import sys
import speech_recognition as sr
import secret

# speech_recognitionの通信において認証されていないSSL通信で接続するため
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

try:
    FFMPEG_PATH = sys._MEIPASS + '/ffmpeg'
    FFPROBE_PATH = sys._MEIPASS + '/ffprobe'
except AttributeError:
    FFMPEG_PATH = '/usr/local/bin/ffmpeg'
    FFPROBE_PATH = '/usr/local/bin/ffprobe'


# フォルダ内のvideoファイル名取得
def search_videos(search_dir):
    # フォルダ内のファイルやディレクトリ名を取得
    files = os.listdir(search_dir)
    # フォルダ内の動画ファイル名を取得
    files = [i for i in files if i[-4:].lower() == '.mov' or i[-4:].lower() == '.mp4']
    # ファイル名を絶対パスにする
    files = [search_dir + i for i in files]
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
                if not (os.path.exists(file_path[0] + '(' + str(i) + ')' + file_path[1])):
                    return file_path[0] + '(' + str(i) + ')' + file_path[1]
                i += 1
        else:
            while True:
                if not (os.path.exists(os.path.dirname(path) + '(' + str(i) + ')/')):
                    return os.path.dirname(path) + '(' + str(i) + ')/'
                i += 1
    else:
        return path


# 無音部分検出
def silence_sections(video):
    # 無音部分をffmpegで検出
    command = [FFMPEG_PATH, '-i', video, '-af', 'silencedetect=noise=-30dB:d=0.3', '-f', 'null', '-']
    output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
            new_sections.append([sections[i][0] - margin_time, sections[i][1] + margin_time, False])
    if new_sections[0][0] < 0:
        new_sections[0][0] = 0.0
    for i in range(len(new_sections) - 1):
        if new_sections[i + 1][0] - new_sections[i][1] < 0.1:
            new_sections[i + 1][0] = (new_sections[i + 1][0] + new_sections[i][1]) / 2
            new_sections[i][1] = new_sections[i + 1][0]
    for i in range(len(new_sections)):
        new_sections[i][2] = False
    return new_sections


# ジャンプカットの修正をする場合のカットしない部分new_sectionsを作成
def all_sections(sections, video):
    new_sections = []
    if sections[0][0] > 0.5:
        new_sections.append([float(0.0), sections[0][0], True])
    for i in range(len(sections)-1):
        new_sections.append(sections[i])
        if sections[i][1] == sections[i+1][0]:
            continue
        new_sections.append([sections[i][1], sections[i+1][0], True])
    new_sections.append(sections[-1])
    duration = get_video_duration(video)
    if duration - sections[-1][1] > 0.5:
        new_sections.append([sections[-1][1], duration, True])
    return new_sections


# 音声認識
def speech_recognize(video, output_text_file):
    video_name = os.path.split(video)[1]
    audio = os.path.split(video)[0] + '/.tmp' + os.path.splitext(video_name)[0] + '.wav'
    command = [FFMPEG_PATH, '-i', video, audio]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        r = sr.Recognizer()
        with sr.AudioFile(audio) as source:
            audio_rec = r.record(source)
        os.remove(audio)
        # s = r.recognize_google(audio_rec, language='ja', key=api.GOOGLE_SPEECH_RECOGNITION_API_KEY)
        text = r.recognize_wit(audio_rec, key=secret.WIT_API_KEY)
        # 文字列を整える
        new_text = fix_text_for_subtitle(text)
    except sr.UnknownValueError:
        # 何を言っているのかわからなかった場合は空の文字列にする
        new_text = ''
    except sr.RequestError as e:
        # インターネット接続がなかった場合はFalseを返す
        print(e)
        return False
    with open(output_text_file, mode='w', encoding='utf8') as f:
        f.write(new_text)
    # 無事認識できた場合はFalseを返す
    return True


# 音声認識のテキストの加工
def fix_text_for_subtitle(text):
    words = text.split(' ')
    new_text = ''
    max_char = 30
    if len(text) > max_char:
        center_index = len(words) / 2
        for i, word in enumerate(words):
            if i < center_index:
                new_text += word
            else:
                new_text += '\n' + word
                center_index = 10000
    else:
        for word in text.split(' '):
            new_text += word
    return new_text


# srtファイル作成
def make_srt(output_file, text_list, subtitle_sections):
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
    with open(output_file, mode='w', encoding='utf8') as wf:
        for i, text in enumerate(text_list):
            wf.write(str(i + 1) + '\n')
            time_info = time_for_srt(
                subtitle_sections[i][0]) + ' --> ' + time_for_srt(subtitle_sections[i][1])
            wf.write(time_info + '\n')
            with open(text, mode='r', encoding='utf8') as rf:
                wf.write(rf.read() + '\n\n')
    return output_file


# 動画の字幕焼き付け
def print_subtitle(video, srt_file, font_size, font_color, output_file):
    try:
        command = [FFMPEG_PATH, '-i', video, '-vf']
        subtitle_command = 'subtitles=' + srt_file + ":force_style='"
        subtitle_command += "FontSize=" + font_size
        subtitle_command += ",PrimaryColour=&H" + font_color[5:7] + font_color[3:5] + font_color[1:3] + "&"
        subtitle_command += "'"
        command += [subtitle_command, ]
        command += ['-c:a', 'copy', output_file]
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print('error:print_subtitle method')
        print(e)
        return
    return output_file


# 動画の結合
def combine_video(video_dir, output_file):
    video_list = search_videos(video_dir)
    try:
        with open(video_dir + 'combine.txt', mode='w', encoding='utf8') as wf:
            for i, video in enumerate(video_list):
                wf.write('file ' + video + '\n')
        command = [FFMPEG_PATH, '-f', 'concat', '-safe', '0', '-i', video_dir + 'combine.txt',
                   '-c', 'copy', output_file]
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.remove(video_dir + 'combine.txt')
    except Exception as e:
        print('error:combine_video method')
        print(e)
    return output_file
