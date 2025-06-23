from google import genai
from google.genai import types
from config import *
import base64
from PIL import Image
from io import BytesIO
import os
import time


class LLMClient:
    def __init__(self,
                 api_key: str = GOOGLE_GENAI_API_KEY):
        if not api_key:
            raise ValueError("API key cannot be empty. Please configure GOOGLE_GENAI_API_KEY in config.py.")

        # 严格按照您提供的方式初始化 client，API Key 直接传入
        self.client = genai.Client(api_key=api_key)
        print("LLMClient (Gemini Text) initialized using genai.Client(api_key).")

    def generate_text(self,
                      prompt_text: str,
                      model_name: str = "gemini-2.5-flash",
                      max_tokens: int = STORY_MAX_WORDS,
                      temperature: float = STORY_TEMPERATURE) -> str | None:
        """
        调用 Google Gemini API 生成文本内容。
        prompt_text: 用户输入的文本提示。
        model_name: 要使用的Gemini文本模型名称（例如"gemini-2.5-flash", "gemini-pro"）。
        max_tokens: 生成内容的最大 token 数量。
        temperature: 控制生成内容的随机性（0.0-1.0之间，越高越随机）。

        returns: 生成的文本内容，如果生成失败或未返回内容，则返回 None。
        """
        try:
            print(f"向 Gemini API 发送文本生成请求，模型：{model_name}...")

            # 严格按照您提供的范例调用 client.models.generate_content
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt_text,  # contents 可以直接是字符串
                config=types.GenerateContentConfig(  # 使用 types.GenerationConfig 构建配置对象
                    # system_instruction= None,  # 暂时设置为 None
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )

            if response.candidates and response.candidates[0].finish_reason.name != 'STOP':
                reason = response.candidates[0].finish_reason.name
                print(f"Gemini API 文本生成未正常完成。终止原因: {reason}。")
                if reason == 'MAX_TOKENS':
                    print("请尝试在 config.py 中调高 STORY_MAX_WORDS 的值。")
                return None

            # 确保 response.text 存在且不为空
            if hasattr(response, 'text') and response.text:
                return response.text
            else:
                print("Gemini API 返回了空文本，但未报告具体错误原因。")
                return None

        except Exception as e:
            print(f"调用 Gemini API 发生错误: {e}")
            return None
