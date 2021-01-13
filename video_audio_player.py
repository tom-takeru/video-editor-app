import os
import sys
import time
import threading
import subprocess
import simpleaudio
import shutil
from imageio.plugins.ffmpeg import FfmpegFormat
import imageio
from PIL import ImageTk, Image


APP_PATH = '/'.join(sys.argv[0].split('/')[:-3])
# python videdi.pyで実行する時のため
if APP_PATH == '':
    APP_PATH = '/Applications/videdi.app'
FFMPEG_PATH = APP_PATH + '/Contents/MacOS/ffmpeg'


# 音楽を再生する
class Audio_player():
    def __init__(self):
        pass

    def __del__(self):
        try:
            shutil.rmtree(self.tmp_dir)
        except:
            pass

    def openfile(self, file_path):
        self.tmp_dir = os.path.split(file_path)[0] + '/.tmp'
        os.mkdir(self.tmp_dir)
        self.audio = self.tmp_dir + '/' + os.path.splitext(os.path.split(file_path)[1])[0] + '.wav'
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
            self.__del__()
        except:
            pass

# 動画を再生する
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
        # try:
        #     self.video = imageio.get_reader(file_path)
        # except imageio.core.fetching.NeedDownloadError:
        #     imageio.plugins.avbin.download()
        #     self.video = imageio.get_reader(file_path)
        self.video = imageio.get_reader(file_path)

    def play(self):
        self.video_thread = threading.Thread(target=self._stream)
        self.video_thread.start()

    def stop(self):
        self.stop_bln = True

    def _stream(self):
        # print(self.video.get_meta_data())
        start_time=time.time()
        sleeptime = 1/self.video.get_meta_data()["fps"]
        if sleeptime < 0.03:
            sleeptime = sleeptime * 2
        frame_now = 0
        for i, image in enumerate(self.video.iter_data()):
            frame_now = frame_now + 1
            if self.stop_bln:
                break
            try:
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

# 動画と音声を再生する
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
