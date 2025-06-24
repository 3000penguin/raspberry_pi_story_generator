import os

from modules.api_clients.llm_client import LLMClient
import config
import json
import typing  # 导入 typing 模块用于类型提示


# 定义故事段落结构
class StorySegment(typing.TypedDict):
    image_prompt: str
    audio_text: str
    character_description: str  # 在此阶段仅作为模型输出，后期可用于统一角色生成图片


# 定义整体故事响应结构
class StoryResponse(typing.TypedDict):
    complete_story: typing.List[StorySegment]  # 列表包含多个 StorySegment
    pages: int


class StoryGenerator:
    def __init__(self):
        self.llm_client = LLMClient(api_key=config.GOOGLE_GENAI_API_KEY)
        # 确保图片输出目录存在
        os.makedirs(config.ASSETS_IMAGE_DIR, exist_ok=True)
        # 为了在这里使用os.makedirs，需要导入os模块
        # import os

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
                        "character_description": "没有人物，只有动物和物体。用艺术风格参考（例如“Pixar风格”，“吉卜力”）描述所有角色（名称、特征、服装等保持一致），30字以内。"
                    }},
                    // ... 更多场景
                ],
                "pages": {num_pages}
            }}
            请确保只输出JSON内容，不要有任何额外文字。
            '''

        print(f"正在生成结构化故事，主题：'{theme}'，页数：{num_pages}...")

        try:
            # 调用LLM客户端生成文本，并明确要求JSON输出和Schema
            response_text = self.llm_client.generate_text(
                prompt_text=prompt,
                model_name=config.GEMINI_TEXT_MODEL,
                max_tokens=config.STORY_MAX_WORDS,  # 这里的max_tokens要足够大以容纳JSON
                temperature=config.STORY_TEMPERATURE,
                # 注意：gemini.GenerativeModel.generate_content直接支持response_mime_type和response_schema
                # 但llm_client.generate_story 是封装后的，如果需要，需在llm_client内部传递
                # 这里假设prompt已经足够引导模型输出JSON
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