import speech_recognition as sr
from io import BytesIO
from modules.input_handler import AudioRecorder

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

    input_handler = AudioRecorder(filename = filename, silence_thresh = silence_thresh, silence_limit = silence_limit)
    wav_bytes = input_handler.record_audio(filename = filename, silence_thresh = silence_thresh, silence_limit = silence_limit)

    if wav_bytes:
        print(f"录音成功")
    else:
        print("录音失败，无法进行语音识别。")

    text = audio_to_text_from_types(wav_bytes)

    print("\n=== 识别结果 ===")
    if text:
        recognized_text = text.strip()
        return recognized_text
    else:
        return "语音识别失败或未返回文本。"

