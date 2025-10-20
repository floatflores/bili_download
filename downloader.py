import json
import os
import re
from enum import Enum

import requests
from tqdm import tqdm


class Audio_Downloader:

    __audio_url = ""
    __video_url = ""
    __title = ""

    __video_file_name = ""
    __audio_file_name = ""
    __headers = {
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "\
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"\
                    "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding":"gzip, deflate, br, zstd",
            "Accept-Language":"zh-CN,zh;q=0.9",
            "Connection":"keep-alive",
            "Origin":"https://www.bilibili.com",
            "Referer":"https://www.bilibili.com",
            "range": "bytes=0-",
            "Cookie": ""
            }

    __video_resolution = {1920: 1080, 1280: 720, 852: 480}

    class DownloadFileType(Enum):
        MP3 = 0,
        MP4 = 1

    def __init__(self, Bid: str):
        self.base_URL = "https://www.bilibili.com/video/"
        self.bid = Bid

        self.url = self.base_URL + Bid + '/'

        cookie_file_path = os.path.join(os.getcwd(), "cookie.txt")
        if os.path.exists(cookie_file_path):
            with open(cookie_file_path, "r", encoding="utf-8") as f:
                self.__headers["Cookie"] = f.read().strip()
        else:
            if input("没有cookie.txt文件的话，下载的质量会偏低，确定继续吗？[y/N]").lower() != "y":
                exit(0)

    def __get_audio_link(self, url):

        request = requests.get(url=url, headers=self.__headers)

        if self.__title is None:
            self.__title = re.search(r'(.*?)"title":"(.*?)",',
                                     request.text).group(2)
            self.__title = re.sub(r'[^\w\u4e00-\u9fa5]', '', self.__title)
        if not self.__title:
            self.__title = self.bid
        self.__audio_url = re.search(r'"audio":\[{"id":\d+,"baseUrl":"(.*?)",',
                                     request.text).group(1)

    def __get_both_link(self, url):

        request = requests.get(url=url, headers=self.__headers)

        self.__title = re.search(r'(.*?)"title":"(.*?)",',
                                 request.text).group(2)
        self.__title = re.sub(r'[^\w\u4e00-\u9fa5]', '', self.__title)

        if not self.__title:
            self.__title = self.bid

        play_info = re.search(r'(.*?)window\.__playinfo__=(.*?)</script>',
                              request.text).group(2)
        json_play_info = json.loads(play_info)

        founded = False
        for video_scale in json_play_info['data']['dash']['video']:
            if video_scale['codecs'] == "hev1.1.6.L150.90":
                for width, height in self.__video_resolution.items():
                    if video_scale['width'] == width and video_scale[
                            'height'] == height:
                        self.__video_url = video_scale['baseUrl']
                        founded = True
                        break
            if founded:
                break

        if not founded:
            self.__video_url = json_play_info['data']['dash']['video'][0][
                'baseUrl']

        self.__audio_url = json_play_info['data']['dash']['audio'][0][
            'baseUrl']

    def __download_file(self, type: DownloadFileType):

        if type == self.DownloadFileType.MP3:
            sufix = '.mp3'
            file_type = 'audio'
            source_url = self.__audio_url
        elif type == self.DownloadFileType.MP4:
            sufix = '.mp4'
            file_type = 'video'
            source_url = self.__video_url

        print("Downloading " + file_type + "...")

        response = requests.get(source_url,
                                headers=self.__headers,
                                stream=True)

        file_size = int(response.headers['content-length'])  #byte
        file_tmp_name = self.__title + '_tmp' + sufix
        file_name = self.__title + sufix

        with tqdm(total=file_size, unit="B", unit_scale=True) as progress_bar:
            with open(file_tmp_name, mode='ab') as file:
                for data in response.iter_content(chunk_size=512 * 1024):
                    progress_bar.update(len(data))
                    file.write(data)

        if type == self.DownloadFileType.MP3:
            command = 'ffmpeg -i ' + os.path.join(
                os.getcwd(), file_tmp_name
            ) + ' -ar 44100 -ac 2 -b:a 192k -acodec libmp3lame ' + os.path.join(
                os.getcwd(), file_name)
            self.__audio_file_name = file_name

        elif type == self.DownloadFileType.MP4:
            #high cost, high memory occupation
            #command = 'ffmpeg -i '+os.getcwd()+'\\'+video_tmp_name+' -vcodec h264 -b:v 20000k -vf scale=1920:1080 -r 60 '+os.getcwd()+'\\'+video_file_name
            command = 'ffmpeg -i ' + os.path.join(
                os.getcwd(),
                file_tmp_name) + ' -vcodec h264 -r 60 ' + os.path.join(
                    os.getcwd(), file_name)
            self.__video_file_name = file_name

        print("Recoding " + file_type + "....")

        os.system(command=command)
        os.remove(os.path.join(os.getcwd(), file_tmp_name))

        print("Finished")
        if (file_size >= 1024 * 1024):
            print(
                f"size of {file_type} file is {file_size/(1024*1024):.2f} MB")
        else:
            print(f"size of {file_type} file is {file_size/1024:.2f} KB")

    def run_download_audio(self):
        if not self.__audio_url:
            self.__get_audio_link(self.url)
        self.__download_file(self.DownloadFileType.MP3)

    def run_download_video(self):
        self.__get_both_link(self.url)
        self.__download_file(self.DownloadFileType.MP4)

    def merge_video_audio(self):

        self.__get_both_link(self.url)
        self.__download_file(self.DownloadFileType.MP3)
        self.__download_file(self.DownloadFileType.MP4)

        command = "ffmpeg -i "+self.__video_file_name+" -i "+self.__audio_file_name+" -ar 44100 -ac 2 -b:a 192k -acodec libmp3lame "\
                  "-vcodec h264 -r 60 "+self.__title+"fin.mp4"
        os.system(command=command)

        os.remove(os.path.join(os.getcwd(), self.__video_file_name))
        os.remove(os.path.join(os.getcwd(), self.__audio_file_name))

        os.rename(self.__title + "fin.mp4", self.__video_file_name)
