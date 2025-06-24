from modules.api_clients.image_gen_client import ImageGenClient
import config
import typing  # 导入 typing 用于类型提示
import os
import time  # 为了生成唯一的文件名

# 导入 StorySegment 类型定义，以确保类型一致性
from modules.story_generator import StorySegment


class ImageGenerator:
    def __init__(self):
        self.image_gen_client = ImageGenClient(api_key=config.GOOGLE_GENAI_API_KEY)
        # 确保图片输出目录存在
        os.makedirs(config.ASSETS_IMAGE_DIR, exist_ok=True)
        # 检查图片输出目录是否为空，不为空则清空
        self.output_dir = config.ASSETS_IMAGE_DIR
        if os.path.exists(self.output_dir) and os.listdir(self.output_dir):
            for filename in os.listdir(self.output_dir):
                file_path = os.path.join(self.output_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        import shutil
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"清空目录时删除 {file_path} 失败: {e}")

    def generate_illustrations_for_story(self, story_segments: typing.List[StorySegment]) -> typing.List[
        typing.Tuple[str, str]]:
        """
        为每个故事段落生成插画。
        参数: story_segments: 结构化的故事段落列表，每个段落包含 'image_prompt'。
        返回: 一个列表，每个元素是键值对 (故事段落文本, 生成图片的文件路径)。
        """
        generated_pages_data = []  # 存储 (audio_text, image_path)

        print(f"\n----- 正在为 {len(story_segments)} 个故事段落生成插画 -----")

        for i, segment in enumerate(story_segments):
            image_prompt = segment.get('image_prompt', '')
            audio_text = segment.get('audio_text', '')  # 提取 audio_text
            character_description = segment.get('character_description', '')  # 提取角色描述

            if not image_prompt:
                print(f"警告：第 {i + 1} 段故事没有图片提示，跳过图片生成。")
                generated_pages_data.append((audio_text, None))
                continue

            print(f"正在为第 {i + 1} 段故事生成图片，提示：'{image_prompt[:50]}...'")

            # 调用 image_gen_client 生成图片
            # 这里将 model_name 从 config 中获取
            image_gen_text, image = self.image_gen_client.generate_image(
                prompt_text=image_prompt,
                model_name=config.GEMINI_IMAGE_GENERATION_MODEL
            )

            # --- 检查并处理结果 ---
            if image_gen_text:
                print(f"\nGemini 返回的文本内容: '{image_gen_text}'")

            if image:
                print(f"\n=== 第{i}段图片生成成功 ===")
                try:
                    # 保存图片到文件
                    os.makedirs(self.output_dir, exist_ok=True)
                    filename = f"generated_image_{i}.png"
                    filepath = os.path.join(self.output_dir, filename)
                    image.save(filepath)

                    # 保存后立即检查； 检查后添加
                    if os.path.exists(filepath):
                        print(f"  ✅ 验证成功：文件已在磁盘上找到。")
                        print(f"  图片已保存到: {filepath}")
                        generated_pages_data.append((audio_text, filepath))
                    else:
                        print(f"  ❌ 错误：save() 命令执行后，文件未在路径 '{filepath}' 中找到。")
                        generated_pages_data.append((audio_text, None))
                        print("============================")

                except Exception as e:
                    print(f"处理或显示图片时发生错误: {e}")
            else:
                print("\n!!! 图片生成失败或未返回图片数据。")


            # 可以添加一个短暂停顿，避免API请求过于频繁
            time.sleep(1)

        print("\n----- 插画生成完成 -----")
        return generated_pages_data