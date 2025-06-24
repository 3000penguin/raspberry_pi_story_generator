# modules/api_clients/image_gen_client.py
from google import genai
from google.genai import types
from config import *
from PIL import Image
from io import BytesIO
import os

class ImageGenClient:
    def __init__(self, api_key: str = GOOGLE_GENAI_API_KEY):
        if not api_key:
            raise ValueError("API key cannot be empty. Please configure GOOGLE_GENAI_API_KEY in config.py.")

        self.client = genai.Client(api_key=api_key)
        print("ImageGenClient (Gemini Vision) initialized using genai.Client().")

    def generate_image(self,
                       prompt_text: str,
                       model_name: str = GEMINI_IMAGE_GENERATION_MODEL):
        """
        调用 Google Gemini API 进行文本转图片生成。
        成功时返回一个包含 (文本, 图片字节数据) 的元组。
        失败或未找到相应内容时，对应项为 None。
        """
        try:
            print(f"向 Gemini API 发送图片生成请求，模型：{model_name}...")

            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt_text,
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE']
                )
            )

            # 核心检查：确认生成是否正常完成
            if not response.candidates or response.candidates[0].finish_reason.name != 'STOP':
                reason = "Unknown"
                if response.candidates:
                    reason = response.candidates[0].finish_reason.name
                elif response.prompt_feedback and response.prompt_feedback.block_reason:
                    reason = f"PROMPT_BLOCKED ({response.prompt_feedback.block_reason.name})"
                print(f"Gemini API 图片生成未正常完成。终止原因: {reason}")
                return None, None

            # 初始化返回值
            text_response = None
            image_response = None

            # 正确地遍历所有部分，以寻找文本和图片
            for part in response.candidates[0].content.parts:
                if part.text:
                    text_response = part.text
                elif part.inline_data is not None:
                    image_response = Image.open(BytesIO(part.inline_data.data))

            if not image_response:
                print("Gemini API 响应中未找到图片数据。")

            return text_response, image_response

        except Exception as e:
            print(f"调用 Gemini API 发生错误: {e}")
            return None, None