import os
import subprocess
import sys

APP_PATH = '/'.join(sys.argv[0].split('/')[:-3])
# python videdi.pyで実行する時のため
if APP_PATH == "":
    APP_PATH = '/Applications/videdi.app'

# フォルダ内の動画をジャンプカット
def jumpcut(videdi):
    # ジャンプカット開始
    print("videdi_jumpcut内部----------------------")
    videdi.frame.set_big_log(videdi.folder_dir.split('/')[-1] + 'フォルダ内の動画のジャンプカット動画作成開始')
    os.chdir(videdi.folder_dir)
    video_dir = os.path.abspath(videdi.folder_dir)
    video_list = videdi.search_videos(videdi.folder_dir)
    for i, video in enumerate(video_list):
        videdi.frame.set_log('')
        videdi.frame.set_log(video + 'のジャンプカット動画作成開始 ' + str(i + 1) + '/' + str(len(video_list)))
        cut_sections = videdi.silence_sections(video)
        print('\ncut_sections')
        print(cut_sections)
        if len(cut_sections) == 0:
            videdi.frame.set_log(video + 'には無音部分がありませんでした。')
            continue
        video_sections = videdi.leave_sections(cut_sections, video)
        print('\nleave_sections')
        print(video_sections)
        video_sections = videdi.arrange_sections(video_sections, videdi.min_time, videdi.margin_time)
        print('\narrange_sections')
        print(video_sections)
        videdi.cut_video(video_dir, video_sections, video)
        videdi.frame.set_log(video + 'のジャンプカット動画作成完了')

    # ボタンを再表示
    videdi.put_all_button()

    # ジャンプカット完了ログ
    videdi.frame.set_big_log(videdi.folder_dir.split('/')[-1] + 'フォルダ内の動画のジャンプカット動画作成完了')
    return


# 無音部分検出
def silence_sections(videdi, video):
    try:
        videdi.frame.set_log(video + ' : 無音部分検知中')
        output = subprocess.run([APP_PATH + '/Contents/MacOS/ffmpeg', '-i', video, '-af',
                                 'silencedetect=noise=-30dB:d=0.3', '-f', 'null', '-'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print(e)
        videdi.frame.set_log('error001')
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


# カット部分のsectionsをカットしない部分のsectionsに変換
def leave_sections(videdi, sections, video):
    try:
        duration = 0
        output = subprocess.run(
            [APP_PATH + '/Contents/MacOS/ffprobe', video, '-hide_banner', '-show_format'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        s = str(output)
        lines = s.split('\\n')
        for line in lines:
            words = line.split('=')
            if words[0] == 'duration':
                duration = float(words[1])
                break
        time_list = []
        if sections[0][0] == 0.0:
            for i in range(len(sections) - 1):
                time_list.append(sections[i][1])
                time_list.append(sections[i + 1][0])
            if sections[-1][1] < duration:
                time_list.append(sections[-1][1])
                time_list.append(duration)
        else:
            time_list.append(float(0.0))
            time_list.append(sections[0][0])
            for i in range(len(sections) - 1):
                time_list.append(sections[i][1])
                time_list.append(sections[i + 1][0])
            if sections[-1][1] < duration:
                time_list.append(sections[-1][1])
                time_list.append(duration)
    except Exception as e:
        print(e)
        videdi.frame.set_log('error002')
        return

    new_sections = list(zip(*[iter(time_list)] * 2))
    return new_sections


# 間隔の短い動画部分を削除
def arrange_sections(videdi, sections, min_time, margin_time):
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
        videdi.frame.set_log('error003')
    return new_sections


# 音のある部分を出力
def cut_video(videdi, video_dir, sections, video):
    os.chdir(video_dir)
    digit = len(str(len(sections)))
    video_name = video.split('.')[0]
    jumpcut_folder = videdi.make_folder(video_name + '_jumpcut')
    for i in range(len(sections)):
        split_file = jumpcut_folder + '/' + video_name + '_' + format(i + 1, '0>' + str(digit)) + '.mp4'
        subprocess.run(
            [APP_PATH + '/Contents/MacOS/ffmpeg', '-i', video, '-ss', str(sections[i][0]), '-t',
             str(sections[i][1] - sections[i][0]), split_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # logを表示
        if int((i + 1) * 100 / len(sections)) != int(i * 100 / len(sections)):
            videdi.frame.set_log(video + '   ' + str(int(((i + 1) * 100) / len(sections))) + '%完了')
    return jumpcut_folder
