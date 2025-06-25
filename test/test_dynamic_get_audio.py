# test/test_get_audio.py
import time

import pyaudio
import wave
import os
import numpy as np
from config import ASSETS_AUDIO_DIR

def record_dynamic_audio(
    filename: str,
    silence_thresh: int = 500,
    silence_limit: float = 1.0) -> None:

    """根据讲话停顿动态录音，silence_thresh 为静音阈值，silence_limit 为允许的连续静音秒数"""
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 512

    output_path = os.path.join(ASSETS_AUDIO_DIR, filename)
    os.makedirs(ASSETS_AUDIO_DIR, exist_ok=True)

    audio = pyaudio.PyAudio()
    try:
        print("开始动态录音...")
        time.sleep(0.5)

        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
    except Exception as e:
        print(f"录音设备初始化失败: {e}")
        return

    frames = []
    silent_chunks = 0
    max_silent_chunks = int(silence_limit * RATE / CHUNK)
    while True:
        data = stream.read(CHUNK)
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
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    print(f"录音已保存至 {output_path}")

def main():
    record_dynamic_audio("dynamic_test.wav", silence_thresh=15000, silence_limit=3.0)

if __name__ == "__main__":
    main()