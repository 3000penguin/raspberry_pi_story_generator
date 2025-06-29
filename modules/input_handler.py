import os
import time
import wave
from io import BytesIO

import numpy as np
import pyaudio

from config import ASSETS_AUDIO_DIR


class AudioRecorder:

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
        print("AudioRecorder initialized. Image input (camera/AI description) is disabled.")

    def __del__(self):
        if self.audio:
            self.audio.terminate()

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

        try:
            print("开始动态录音...")
            time.sleep(0.5)

            stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
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

        wav_buffer = BytesIO()

        # 保存到文件
        with wave.open(output_path, 'wb') as wf, wave.open(wav_buffer, 'wb') as wb:
            self._write_wav_data(wf, frames)
            print(f"录音已保存至 {output_path}")
            self._write_wav_data(wb, frames)
            print(f"录音数据已保存到内存缓冲区")
        wav_buffer.seek(0)

        return wav_buffer

    def _write_wav_data(self, wav_file, frames):
        """写入WAV文件数据的通用方法"""
        wav_file.setnchannels(self.CHANNELS)
        wav_file.setsampwidth(self.audio.get_sample_size(self.FORMAT))
        wav_file.setframerate(self.RATE)
        wav_file.writeframes(b''.join(frames))