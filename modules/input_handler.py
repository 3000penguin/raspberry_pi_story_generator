import time
from io import BytesIO

import pyaudio
import wave
import io
import os
import numpy as np
from config import ASSETS_AUDIO_DIR

import speech_recognition as sr

class InputHandler:

    def __init__(self,
                 filename: str = "temp_voice_input.wav",
                 silence_thresh: int = 15000,
                 silence_limit: float = 3.0):

        self.output_path = os.path.join(ASSETS_AUDIO_DIR, filename)
        os.makedirs(ASSETS_AUDIO_DIR, exist_ok=True)

        self.silence_thresh = silence_thresh
        self.silence_limit = silence_limit

        # 初始化 PyAudio
        self.audio = pyaudio.PyAudio()
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100  # 语音识别常用采样率
        self.CHUNK = 512  # 每次读取的帧大小

        # 明确禁用摄像头和图片描述功能
        self.camera = None
        print("InputHandler initialized. Image input (camera/AI description) is disabled.")

    def record_audio(
        self,
        filename: str = "temp_voice_input.wav",
        silence_thresh: int = 15000,
        silence_limit: float = 3.0) -> BytesIO | None:
        """

        :param filename: 录音文件名
        :param silence_thresh: 静音阈值，单位为音频采样的平均幅度
        :param silence_limit: 允许的连续静音秒数
        :return: 录音的字节流数据，如果录音失败则返回 None
        """

        output_path = os.path.join(ASSETS_AUDIO_DIR, filename)
        os.makedirs(ASSETS_AUDIO_DIR, exist_ok=True)

        audio = pyaudio.PyAudio()
        try:
            print("开始动态录音...")
            time.sleep(0.5)

            stream = audio.open(
                format= self.FORMAT,
                channels= self.CHANNELS,
                rate= self.RATE,
                input=True,
                frames_per_buffer= self.CHUNK
            )
        except Exception as e:
            print(f"录音设备初始化失败: {e}")
            return None

        frames = []
        silent_chunks = 0
        max_silent_chunks = int(silence_limit * self.RATE / self.CHUNK)
        while True:
            data = stream.read(self.CHUNK)
            frames.append(data)
            # 计算当前块平均幅度
            amplitude = np.frombuffer(data, dtype=np.int16)
            current_volume = np.abs(amplitude).mean()
            print(f"当前音量: {current_volume:.2f} | 安静阈值：{silence_thresh}")
            if current_volume < silence_thresh:
                silent_chunks += 1
            else:
                silent_chunks = 0
            if silent_chunks >= max_silent_chunks:
                print("检测到长时间静音，停止录音")
                break

        stream.stop_stream()
        stream.close()
        audio.terminate()

        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(frames))

        print(f"录音已保存至 {output_path}")

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(frames))
        wav_buffer.seek(0)

        return wav_buffer

    @staticmethod
    def audio_to_text_from_file(filepath: str = None):
        """
        从录音文件中读取音频数据并进行语音识别。
        参数：
            filepath: 录音文件的路径，默认为 None
        返回：
            text: 识别到的文本或 None
        """
        r = sr.Recognizer()
        with sr.AudioFile(filepath) as source:
            audio_data = r.record(source)
            try:
                text = r.recognize_google(audio_data, language='zh-CN')
                print(f"识别结果: {text}")
                return text
            except sr.UnknownValueError:
                print("Google 语音识别无法理解音频")
            except sr.RequestError as e:
                print(f"无法请求 Google 语音识别服务; {e}")

    @staticmethod
    def audio_to_text_from_types(audio_wav_buffer: BytesIO):
        """
        直接用音频字节流（如PCM/wav）进行语音识别。
        参数:
            audio_bytes: 音频的字节流（如 b''.join(frames) 的结果）
            sample_rate: 采样率，默认16000
        返回:
            识别到的文本或 None
        """
        r = sr.Recognizer()
        # 用 BytesIO 包装字节流，假设为 wav 格式
        with sr.AudioFile(audio_wav_buffer) as source:
            audio_data = r.record(source)
            try:
                text = r.recognize_google(audio_data, language='zh-CN')
                print(f"识别结果: {text}")
                return text
            except sr.UnknownValueError:
                print("Google 语音识别无法理解音频")
            except sr.RequestError as e:
                print(f"无法请求 Google 语音识别服务; {e}")

def record_and_transcribe_speech(filename: str = "temp_voice_input.wav",
                                 silence_thresh: int = 15000,
                                 silence_limit: float = 3.0):

    input_handler = InputHandler(filename = filename, silence_thresh = silence_thresh, silence_limit = silence_limit)
    wav_bytes = input_handler.record_audio(filename = filename, silence_thresh = silence_thresh, silence_limit = silence_limit)  # 调用 InputHandler 的动态录音方法

    if wav_bytes:
        print(f"录音成功")
    else:
        print("录音失败，无法进行语音识别。")

    text = input_handler.audio_to_text_from_types(wav_bytes)

    print("\n=== 识别结果 ===")
    if text:
        recognized_text = text.strip()
        return recognized_text
    else:
        return "语音识别失败或未返回文本。"
