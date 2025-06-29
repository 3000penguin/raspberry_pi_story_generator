import os
import time
from gtts import gTTS
import pygame
from typing import Optional
import config


class TTSClient:
    """
    使用 Google Text-to-Speech (gTTS) 的文本转语音客户端
    支持中文和英文文本转换为音频文件，并提供播放控制功能
    """

    def __init__(self, language='zh', slow=False):
        """
        初始化 TTS 客户端

        Args:
            language: 语言代码，默认为 'zh' (中文)
            slow: 是否慢速播放，默认 False
        """
        self.language = language
        self.slow = slow
        self.audio_dir = config.ASSETS_AUDIO_DIR

        # 确保音频目录存在
        os.makedirs(self.audio_dir, exist_ok=True)

        # 初始化 pygame mixer 用于音频播放
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.mixer_initialized = True
            print("pygame mixer 音频系统初始化成功")
        except Exception as e:
            print(f"pygame mixer 初始化失败: {e}")
            self.mixer_initialized = False

        # 音频播放状态
        self.current_audio_file = None
        self.is_playing = False
        self.is_paused = False
        self.is_muted = False  # 添加静音状态

    def generate_speech(self, text: str, filename: str = None) -> Optional[str]:
        """
        将文本转换为语音并保存为 MP3 文件

        Args:
            text: 要转换的文本
            filename: 保存的文件名，如果不提供则自动生成

        Returns:
            str: 生成的音频文件路径，失败返回 None
        """
        if not text or not text.strip():
            print("文本为空，无法生成语音")
            return None

        try:
            # 如果没有提供文件名，则生成一个基于时间戳的文件名
            if filename is None:
                timestamp = int(time.time())
                filename = f"tts_audio_{timestamp}.mp3"

            # 确保文件名以 .mp3 结尾
            if not filename.endswith('.mp3'):
                filename += '.mp3'

            audio_path = os.path.join(self.audio_dir, filename)

            print(f"正在生成语音: {text[:50]}...")

            # 创建 gTTS 对象并生成语音
            tts = gTTS(text=text, lang=self.language, slow=self.slow)
            tts.save(audio_path)

            print(f"语音文件已保存: {audio_path}")
            return audio_path

        except Exception as e:
            print(f"生成语音失败: {e}")
            return None

    def play_audio(self, audio_path: str, wait_for_completion: bool = False) -> bool:
        """
        播放指定的音频文件

        Args:
            audio_path: 音频文件路径
            wait_for_completion: 是否等待播放完成

        Returns:
            bool: 播放是否成功开始
        """
        # 如果处于静音状态，不播放音频
        if self.is_muted:
            print("当前处于静音状态，跳过音频播放")
            return True

        if not self.mixer_initialized:
            print("音频系统未初始化，无法播放音频")
            return False

        if not os.path.exists(audio_path):
            print(f"音频文件不存在: {audio_path}")
            return False

        try:
            # 停止当前播放的音频
            self.stop_audio()

            # 加载并播放新音频
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()

            self.current_audio_file = audio_path
            self.is_playing = True
            self.is_paused = False

            print(f"开始播放音频: {os.path.basename(audio_path)}")

            # 如果需要等待播放完成
            if wait_for_completion:
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                self.is_playing = False

            return True

        except Exception as e:
            print(f"播放音频失败: {e}")
            return False

    def pause_audio(self):
        """暂停音频播放"""
        if self.mixer_initialized and self.is_playing:
            pygame.mixer.music.pause()
            self.is_paused = True
            print("音频已暂停")

    def resume_audio(self):
        """恢复音频播放"""
        if self.mixer_initialized and self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            print("音频已恢复播放")

    def stop_audio(self):
        """停止音频播放"""
        if self.mixer_initialized:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False
            self.current_audio_file = None
            print("音频已停止")

    def is_audio_playing(self) -> bool:
        """检查音频是否正在播放"""
        if self.mixer_initialized:
            return pygame.mixer.music.get_busy() and not self.is_paused
        return False

    def generate_and_play(self, text: str, filename: str = None, wait_for_completion: bool = False) -> bool:
        """
        生成语音并立即播放

        Args:
            text: 要转换的文本
            filename: 保存的文件名
            wait_for_completion: 是否等待播放完成

        Returns:
            bool: 是否成功生成并开始播放
        """
        # 如果处于静音状态，不播放音频
        if self.is_muted:
            print("当前处于静音状态，跳过音频播放")
            return True

        audio_path = self.generate_speech(text, filename)
        if audio_path:
            return self.play_audio(audio_path, wait_for_completion)
        return False

    def set_mute(self, muted: bool):
        """
        设置静音状态

        Args:
            muted: True 为静音，False 为取消静音
        """
        self.is_muted = muted
        if muted:
            # 静音时停止当前播放的音频
            self.stop_audio()
            print("音频已静音")
        else:
            print("音频已取消静音")

    def toggle_mute(self) -> bool:
        """
        切换静音状态

        Returns:
            bool: 当前静音状态
        """
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.stop_audio()
            print("音频已静音")
        else:
            print("音频已取消静音")
        return self.is_muted

    def is_muted_status(self) -> bool:
        """
        获取当前静音状态

        Returns:
            bool: True 为静音状态，False 为正常状态
        """
        return self.is_muted

    def cleanup(self):
        """清理资源"""
        self.stop_audio()
        if self.mixer_initialized:
            pygame.mixer.quit()
            print("TTS 客户端资源已清理")


# 创建全局 TTS 客户端实例
tts_client = TTSClient()
