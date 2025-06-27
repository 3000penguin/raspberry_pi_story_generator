from modules.presentation_manager import PresentationManager
import os
from config import ASSETS_IMAGE_DIR

def run_presentation_manager_test():
    print("----- 正在测试 PresentationManager 模块 -----")

    # 模拟多页故事数据 (每页包含文本和图片路径)
    # 确保 assets/generated_images 目录下有图片用于测试 (例如通过 test_core_gen.py 生成的图片)
    story_pages_data = []
    base_image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ASSETS_IMAGE_DIR)

    # 检查目录是否存在
    if not os.path.exists(base_image_dir):
        os.makedirs(base_image_dir)
        print(f"创建目录: {base_image_dir}")

    # 尝试加载所有生成的图片及其对应的模拟文本
    # 假设图片命名为 generated_image_0.png, generated_image_1.png, ...
    for i in range(3):  # 假设有3张图片用于测试
        image_name = f"generated_image_{i}.png"
        image_path = os.path.join(base_image_dir, image_name)

        # 模拟不同的故事文本
        if i == 0:
            text = "这是一只可爱的小恐龙丁丁，它住在绿色的森林里。丁丁喜欢吃苹果，也喜欢和小蝴蝶一起玩耍。它的梦想是有一天能够飞到云朵上面去。"
        elif i == 1:
            text = "一天，丁丁在森林里遇到了一只迷路的小兔子，小兔子很害怕。丁丁决定帮助它找妈妈，它们一起踏上了寻找之路。"
        elif i == 2:
            text = "经过一番努力，小恐龙丁丁和小兔子终于找到了兔妈妈。它们开心地跳了起来，丁丁也因此明白，帮助别人是多么快乐的一件事。"
        else:
            text = f"这是故事的第 {i + 1} 页。为了测试多页内容，我们准备了这段文字。"

        story_pages_data.append({'text': text, 'image_path': image_path})

    if not story_pages_data:
        print("警告：没有模拟故事页面数据。请确保 assets/generated_images 目录下有图片。")
        return

    # 实例化 PresentationManager，强制使用图形模式
    # 由于您有物理显示屏，我们强制禁用测试模式
    manager = PresentationManager(screen_size=(800, 480), test_mode=False)

    current_page_index = 0
    total_pages = len(story_pages_data)

    try:
        while True:  # 移除循环次数限制
            # 显示当前页面
            current_page_info = story_pages_data[current_page_index]
            manager.display_story_page(
                current_page_info['text'],
                current_page_info['image_path'],
                current_page_index + 1  # 页码从1开始
            )

            # 等待用户输入
            action = manager.wait_for_page_flip_input()

            if action == 'next':
                current_page_index = (current_page_index + 1) % total_pages  # 循环翻页
            elif action == 'prev':
                current_page_index = (current_page_index - 1 + total_pages) % total_pages  # 循环翻页
            elif action == 'scroll_up':
                if not manager.test_mode:
                    print("向上滚动功能待实现（在此简化为上一页）")
                current_page_index = (current_page_index - 1 + total_pages) % total_pages
            elif action == 'scroll_down':
                if not manager.test_mode:
                    print("向下滚动功能待实现（在此简化为下一页）")
                current_page_index = (current_page_index + 1) % total_pages
            elif action == 'quit':
                print("用户选择退出")
                break  # 退出循环


    except KeyboardInterrupt:
        print("\n用户中断测试")
    finally:
        manager.cleanup()  # 清理 Pygame 资源

    print("\n----- PresentationManager 模块测试完成 -----")


if __name__ == "__main__":
    # 这个测试现在可以在没有显示器的环境下运行
    # 在测试模式下，它会在控制台输出信息而不是显示图形界面
    run_presentation_manager_test()