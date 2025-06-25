import config
from modules.image_generator import ImageGenerator
from modules.story_generator import StoryGenerator


# --- 核心：在这里统一配置 Google Gen AI API Key ---
# 确保 config.py 中 GOOGLE_GENAI_API_KEY 已配置
if not config.GOOGLE_GENAI_API_KEY:
    print("错误：请在 config.py 中配置正确的 GOOGLE_GENAI_API_KEY。")
    exit()

# 严格遵循Google官方SDK的推荐：API Key通过genai.Client()的构造函数传入
# 在这里进行一次全局配置，以防万一其他地方也需要，但不依赖它
# genai.configure(api_key=config.GOOGLE_GENAI_API_KEY) # 旧库的方法，新库不建议或不支持

# --- 测试参数 ---
TEST_STORY_THEME = "一只好奇的小狐狸探索魔法森林的奇遇"
TEST_NUM_PAGES = 3  # 希望生成3个场景


def run_core_modules_test():
    print("----- 正在执行核心模块整合测试 -----")

    # 实例化故事生成模块和图像生成模块
    # 它们内部会实例化各自的API客户端（llm_client, image_gen_client）
    story_gen_instance = StoryGenerator()
    image_gen_instance = ImageGenerator()

    # --- 1. 测试故事生成模块 (调用llm_client) ---
    print(f"\n[故事生成测试] 主题: {TEST_STORY_THEME}, 页数: {TEST_NUM_PAGES}")

    # 调用 story_generator.py 中的方法来生成结构化故事
    story_segments_list, story_summary = story_gen_instance.generate_structured_story(
        theme=TEST_STORY_THEME,
        num_pages=TEST_NUM_PAGES
    )

    if story_segments_list:
        print("\n=== 结构化故事生成成功 ===")
        for i, segment in enumerate(story_segments_list):
            print(f"--- 第 {i + 1} 段 ---")
            print(f"  图片提示: {segment.get('image_prompt')}")
            print(f"  音频文本: {segment.get('audio_text')}")
            print(f"  角色描述: {segment.get('character_description')}")
        print("============================")
        print(f"故事摘要: {story_summary}")
    else:
        print("!!! 结构化故事生成失败或解析错误。")
        return  # 如果故事生成失败，则停止后续步骤

    # --- 2. 测试图像生成模块 (调用image_gen_client) ---
    print("\n[图像生成测试] 开始为故事段落生成插画...")
    # 调用 image_generator.py 中的方法为每个段落生成图片
    generated_pages_data = image_gen_instance.generate_illustrations_for_story(
        story_segments=story_segments_list
    )

    if generated_pages_data:
        print("\n=== 所有插画生成尝试完成 ===")
        for i, (audio_text, image_path) in enumerate(generated_pages_data):
            status = "成功" if image_path else "失败"
            print(f"  第 {i + 1} 段: 文本='{audio_text[:20]}...', 图片状态={status}, 路径={image_path}")
        print("================================")
    else:
        print("!!! 插画生成失败或未返回任何图片数据。")

    print("\n----- 核心模块整合测试完成 -----")


if __name__ == "__main__":
    run_core_modules_test()