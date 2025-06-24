import os
import time
from modules.api_clients.image_gen_client import ImageGenClient
import config
from PIL import Image
from io import BytesIO

# 1. 检查 API 密钥配置
if not config.GOOGLE_GENAI_API_KEY:
    print("错误：请在 config.py 中配置正确的 GOOGLE_GENAI_API_KEY。")
    exit()

# 2. 定义测试参数
IMAGE_MODEL_NAME = "gemini-2.0-flash-preview-image-generation"
IMAGE_PROMPT = "儿童绘本风格，一只蓝色小机器人抱着一只黄色小鸟，在阳光明媚的草地上开心地玩耍，背景是彩虹和白云。"
IMAGE_OUTPUT_DIR = config.ASSETS_IMAGE_DIR

def run_api_tests():
    """执行 API 客户端集成测试"""
    print("----- 正在执行 API 客户端集成测试 -----")

    # --- 初始化客户端 ---
    try:
        image_gen_client_instance = ImageGenClient(api_key=config.GOOGLE_GENAI_API_KEY)
    except ValueError as e:
        print(f"客户端初始化失败: {e}")
        return

    # --- 测试图像生成 ---
    print(f"\n[图像生成测试] 使用模型: {IMAGE_MODEL_NAME}")
    print(f"  Prompt: {IMAGE_PROMPT}")

    # 调用客户端并正确解包返回的元组
    text_result, image_result = image_gen_client_instance.generate_image(
        prompt_text=IMAGE_PROMPT,
        model_name=IMAGE_MODEL_NAME
    )

    # --- 检查并处理结果 ---
    if text_result:
        print(f"\nGemini 返回的文本内容: '{text_result}'")

    if image_result:
        print("\n=== 图片生成成功 ===")
        try:
            # 保存图片到文件
            os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)
            filename = f"TEST_generated_image_{int(time.time())}.png"
            filepath = os.path.join(IMAGE_OUTPUT_DIR, filename)
            image_result.save(filepath)

            # **核心诊断步骤**：保存后立即检查文件是否存在
            if os.path.exists(filepath):
                print(f"  ✅ 验证成功：文件已在磁盘上找到。")
                print(f"  图片已保存到: {filepath}")
                print("============================")
                # 只有在确认保存成功后，才尝试显示图片
                print("  正在尝试显示图片...")
                image_result.show()
            else:
                # 如果文件不存在，打印一个明确的错误信息
                print(f"  ❌ 错误：save() 命令执行后，文件未在路径 '{filepath}' 中找到。")
                print("  请检查：")
                print(f"    1. 您的程序对目录 '{os.path.abspath(IMAGE_OUTPUT_DIR)}' 是否有写入权限。")
                print("    2. 磁盘空间是否充足。")
                print("============================")

        except Exception as e:
            print(f"处理或显示图片时发生错误: {e}")
    else:
        print("\n!!! 图片生成失败或未返回图片数据。")

    print("\n----- API 客户端集成测试完成 -----")

if __name__ == "__main__":
    run_api_tests()