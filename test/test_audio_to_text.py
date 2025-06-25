from modules.api_clients.stt_client import record_and_transcribe_speech

def run_audio_to_text_test():
    print("----- 正在测试 stt_client 模块 (基于PyAudio动态录音 & Google语音识别) -----")

    text = record_and_transcribe_speech()

    print("\n=== 识别结果 ===")
    if text:
        recognized_text = text.strip()
        print(f"'{recognized_text}'")
        print("==========================")
        print(f"语音主题获取成功: '{recognized_text}'")
    else:
        print("语音识别失败或未返回文本。")

    print("\n----- stt_client 模块测试完成 -----")

if __name__ == "__main__":
    run_audio_to_text_test()