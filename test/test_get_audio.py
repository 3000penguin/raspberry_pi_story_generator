import os
import sys

import speech_recognition as sr

from modules.input_handler import AudioRecorder

os.close(sys.stderr.fileno())

def run_input_handler_test():
    print("----- 正在测试 InputHandler 模块 (基于PyAudio动态录音 & Google语音识别) -----")
    # 初始化 InputHandler，它现在只负责录音。可以调整静音检测参数。
    input_handler = AudioRecorder()

    # --- 核心：录制音频 ---
    print("\n--- 测试语音输入功能 (录音) ---")
    audio_bytes = input_handler.record_audio()  # 调用 InputHandler 的动态录音方法

    if audio_bytes:
        print(f"录音成功，获取到 {len(audio_bytes)} 字节音频数据。")

        r = sr.Recognizer()

        with sr.AudioFile(audio_bytes) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language='zh-CN')  # 使用 Google 的语音识别服务

            if text:
                recognized_text = text.strip()
                print(f"\n=== 识别结果 ===\n'{recognized_text}'\n==========================")
                print(f"语音主题获取成功: '{recognized_text}'")
            else:
                print("语音识别失败或未返回文本。")
    else:
        print("录音失败，无法进行语音识别。")

    print("\n----- InputHandler 模块测试完成 -----")


if __name__ == "__main__":
    run_input_handler_test()