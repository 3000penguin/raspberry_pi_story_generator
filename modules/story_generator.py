import os

from google.genai import types

from modules.api_clients.llm_client import LLMClient
from modules.api_clients.tts_client import tts_client
import config
import json
import typing  # 导入 typing 模块用于类型提示


# 定义故事段落结构
class StorySegment(typing.TypedDict):
    image_prompt: str
    audio_text: str
    character_description: str  # 在此阶段仅作为模型输出，后期可用于统一角色生成图片
    audio_path: str  # 添加音频文件路径字段


# 定义整体故事响应结构
class StoryResponse(typing.TypedDict):
    complete_story: typing.List[StorySegment]  # 列表包含多个 StorySegment
    pages: int

# json_schema_definition = {
#     "type": "object",
#     "properties": {
#         "complete_story": {
#             "type": "array",
#             "items": {
#                 "$ref": "#/definitions/StorySegment"
#             }
#         },
#         "pages": {
#             "type": "integer"
#         }
#     },
#     "definitions": {
#         "StorySegment": {
#             "type": "object",
#             "properties": {
#                 "image_prompt": {"type": "string"},
#                 "audio_text": {"type": "string"},
#                 "character_description": {"type": "string"}
#             },
#             "required": ["image_prompt", "audio_text", "character_description"]
#         }
#     }
# }

class StoryGenerator:
    def __init__(self):
        self.llm_client = LLMClient(api_key=config.GOOGLE_GENAI_API_KEY)
        os.makedirs(config.ASSETS_IMAGE_DIR, exist_ok=True)

    def generate_structured_story(self, theme: str, num_pages: int) -> typing.Tuple[
                                                                           typing.List[StorySegment], str] | None:
        """
        根据主题和页数生成结构化故事。
        theme: 故事的主题。
        num_pages: 希望故事包含的场景/段落数量。
        返回: (complete_story_list, story_text_summary) 或 None。
        """
        # 构建详细的 Prompt，引导模型生成结构化输出
        # 参考您提供的Animated_Story_Video_Generation_gemini.ipynb中的Prompt
        prompt = f'''
            你是一位动画视频制作人。请为一部关于 "{theme}" 的动画片，生成一个包含 {num_pages} 个场景的故事序列。每个场景大约1秒。
            
            请严格按照以下JSON结构输出内容。如果模型返回的不是有效的JSON，请尝试调整Prompt或降低温度。
            注意：character_description字段应在每个场景中保持角色的名称、特征、服装等一致。
            输出格式要求：
            {{
                "complete_story": [
                    {{
                        "image_prompt": "(明确的艺术风格，如儿童绘本风格，所有角色风格一致，无暴力) 对场景、其中角色和背景的完整描述，20字以内。随着故事推进，逐步变换场景。",
                        "audio_text": "一句对话/旁白，概括场景核心内容。",
                        "character_description": "没有人物，只有动物和物体。用艺术风格参考（例如"Pixar风格"，"吉卜力"）描述所有角色（名称、特征、服装等保持一致），30字以内。"
                    }},
                    // ... 更多场景
                ],
                "pages": {num_pages}
            }}
            请确保只输出JSON内容，不要有任何额外文字。
            '''

        print(f"正在生成结构化故事，主题：'{theme}'，页数：{num_pages}...")

        try:
            story_segment_schema = types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "image_prompt": types.Schema(type=types.Type.STRING),
                    "audio_text": types.Schema(type=types.Type.STRING),
                    "character_description": types.Schema(type=types.Type.STRING)
                },
                required=["image_prompt", "audio_text", "character_description"]
            )
            structured_response_schema = types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "complete_story": types.Schema(
                        type=types.Type.ARRAY,
                        items=story_segment_schema  # 直接内联 StorySegment 的 Schema
                    ),
                    "pages": types.Schema(type=types.Type.INTEGER)
                },
            )
            # 构建 types.GenerateContentConfig 对象
            structured_output_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=structured_response_schema  # 传递 types.Schema 对象
            )

            # 调用LLM客户端生成文本，并明确要求JSON输出和Schema
            response_text = self.llm_client.generate_text(
                prompt_text=prompt,
                model_name=config.GEMINI_TEXT_MODEL,
                max_tokens=config.STORY_MAX_WORDS,  # 这里的max_tokens要足够大以容纳JSON
                temperature=config.STORY_TEMPERATURE,
                config_param=structured_output_config  # 使用预定义的配置
            )

            if not response_text:
                print("故事文本生成失败或为空。")
                return None

            # 尝试解析JSON
            try:
                # 检查并清理可能的JSON前缀/后缀，确保纯JSON字符串
                if response_text.startswith("```json"):
                    response_text = response_text[len("```json"):].strip()
                if response_text.endswith("```"):
                    response_text = response_text[:-len("```")].strip()

                story_data: StoryResponse = json.loads(response_text)  # 使用类型提示

                complete_story_list = story_data.get('complete_story')
                num_pages_returned = story_data.get('pages')

                if complete_story_list and isinstance(complete_story_list, list) and num_pages_returned == num_pages:
                    # 为每个故事段落生成音频文件
                    print("正在为故事段落生成音频文件...")
                    for i, segment in enumerate(complete_story_list):
                        audio_text = segment.get('audio_text')
                        if audio_text:
                            # 为每个段落生成唯一的音频文件名
                            filename = f"story_page_{i+1}.mp3"
                            audio_path = tts_client.generate_speech(audio_text, filename)
                            if audio_path:
                                segment['audio_path'] = audio_path
                                print(f"第 {i+1} 页音频已生成: {filename}")
                            else:
                                print(f"第 {i+1} 页音频生成失败")
                                segment['audio_path'] = None

                    # 提取一个整体的故事摘要，可以简单拼接audio_text
                    story_summary = " ".join([seg['audio_text'] for seg in complete_story_list if 'audio_text' in seg])
                    return complete_story_list, story_summary
                else:
                    print("JSON结构不符合预期或故事段落为空。")
                    return None
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}")
                print(f"原始响应文本: {response_text[:500]}...")  # 打印部分响应方便调试
                return None
            except Exception as e:
                print(f"解析故事数据时发生未知错误: {e}")
                return None

        except Exception as e:
            print(f"调用故事生成服务时发生错误: {e}")
            return None

    def generate_audio_for_story(self, story_segment: StorySegment) -> str | None:
        """
        为给定的故事段落生成音频。
        story_segment: 单个故事段落，包含文本和其他元数据。
        返回: 音频文件的路径或 None。
        """
        audio_text = story_segment.get("audio_text")
        if not audio_text:
            print("没有找到音频文本，无法生成音频。")
            return None

        # 调用 TTS 客户端生成音频
        try:
            audio_path = tts_client.generate_audio(
                text=audio_text,
                output_dir=config.ASSETS_AUDIO_DIR,  # 音频文件输出目录
                file_name=f"story_segment_{story_segment.get('id')}.mp3"  # 生成唯一的文件名
            )
            return audio_path
        except Exception as e:
            print(f"生成音频时发生错误: {e}")
            return None
