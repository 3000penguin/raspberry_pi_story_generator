from modules.input_handler import InputHandler

def run_audio_to_text_test():
    print("----- 正在测试 InputHandler 模块 (基于PyAudio动态录音 & Google语音识别) -----")

    # 初始化 InputHandler，它现在只负责录音。可以调整静音检测参数。
    input_handler = InputHandler()

    # --- 核心：录制音频 ---
    print("\n--- 测试语音输入功能 (录音) ---")
    wav_bytes = input_handler.record_audio()  # 调用 InputHandler 的动态录音方法

    if wav_bytes:
        print(f"录音成功")
    else:
        print("录音失败，无法进行语音识别。")

    text = input_handler.audio_to_text_from_types(wav_bytes)
    print("\n=== 识别结果 ===")
    if text:
        recognized_text = text.strip()
        print(f"'{recognized_text}'")
        print("==========================")
        print(f"语音主题获取成功: '{recognized_text}'")
    else:
        print("语音识别失败或未返回文本。")

    print("\n----- InputHandler 模块测试完成 -----")

if __name__ == "__main__":
    run_audio_to_text_test()