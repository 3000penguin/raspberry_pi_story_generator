import config  # 导入配置文件
from config import STORY_NUM_PAGES
from modules.api_clients.stt_client import *
from modules.image_generator import ImageGenerator
from modules.presentation_manager import PresentationManager
from modules.story_generator import StoryGenerator


def main():
    print("----- 树莓派个性化儿童绘本生成器启动 -----")

    # 1. 初始化核心模块
    # 注意：这里的初始化顺序很重要，API客户端需要在其被依赖的模块实例化之前被正确配置
    # 但由于API客户端实例化的API Key依赖config，且config已全局导入，所以直接实例化高层模块即可

    # 由于 AudioRecorder 和 STTClient 是直接用于输入部分，所以先初始化
    # 按照您input_handler.py的默认值初始化AudioRecorder

    story_generator = StoryGenerator()  # 内部会实例化 LLMClient
    image_generator = ImageGenerator()  # 内部会实例化 ImageGenClient

    # 初始化 PresentationManager，自动检测模式
    presentation_manager = PresentationManager(screen_size=(800, 480))

    # 检查 Pygame 是否成功初始化，如果失败则无法进行图形显示
    if not presentation_manager.pygame_initialized:
        print("\n!!! Pygame 显示器初始化失败。程序将以控制台模式运行，无法显示图形界面。")
        print("请检查树莓派显示器连接、驱动和相关配置。")
        # 即使无法显示，程序的核心逻辑也可以在控制台继续运行
        # 但为了演示效果，这里可以选择退出或只进行控制台输出
        # return
        pass  # 继续，但知道没有图形输出

    try:
        while True:
            print("\n----- 等待用户输入故事主题 -----")
            # 1. 等待用户输入故事主题
            story_theme = record_and_transcribe_speech()
            if story_theme:
                print("\n录音与转录成功，正在获取故事主题...")
            else:
                print("\n无法获取有效的故事主题，请重试或输入'Q(quit)'退出。")
                story_theme = input("或手动输入故事主题 (输入 'quit' 退出): ").strip()
                if story_theme.lower() == 'quit':
                    break  # 退出循环

            print(f"\n用户输入的故事主题: '{story_theme}'")

            # 2. 生成结构化故事
            print("\n----- 正在生成结构化故事和图片 -----")
            print(f"故事主题: {story_theme}, 预计 {config.STORY_MAX_WORDS} 字内...")

            # 假设生成3页
            story_segments, story_summary = story_generator.generate_structured_story(
                theme=story_theme,
                num_pages=STORY_NUM_PAGES
            )

            if not story_segments:
                print("!!! 故事生成失败或解析错误，请检查API Key和网络连接。")
                continue  # 继续等待下一次输入

            print(f"\n故事摘要: '{story_summary}'")

            # 3. 生成插画
            generated_pages_data = image_generator.generate_illustrations_for_story(
                story_segments=story_segments
            )

            if not generated_pages_data:
                print("!!! 插画生成失败或未生成任何图片。")
                # 即使图片失败，也可以尝试显示纯文本的故事
                generated_pages_data = [(seg.get('audio_text', ''), None) for seg in story_segments]  # 填充无图数据

            print("\n----- 故事和插画生成完成 -----")

            # 4. 呈现故事页面
            print("\n----- 正在屏幕上呈现故事 -----")
            current_page_index = 0
            total_pages = len(generated_pages_data)

            want_continue = False  # 用于控制是否继续翻页
            finish = False  # 用于标记是否已到达最后一页
            while True:
                page_info = generated_pages_data[current_page_index]

                presentation_manager.display_story_page(
                    page_info[0],  # audio_text
                    page_info[1],  # image_path
                    current_page_index + 1
                )

                # 等待翻页输入
                action = presentation_manager.wait_for_page_flip_input()
                if action == 'next':
                    current_page_index = (current_page_index + 1) % total_pages

                    if finish and not want_continue:
                        user_choice = input("读完了，是否退出？ (yes/no): ").strip().lower()
                        if user_choice == 'yes':
                            break  # 退出主循环
                        elif user_choice == 'no':
                            want_continue = True

                    if want_continue:
                        if current_page_index >= total_pages:
                            current_page_index = current_page_index % total_pages

                elif action == 'prev':
                    current_page_index = (current_page_index - 1 + total_pages) % total_pages
                elif action == 'scroll_up':
                    print("向上滚动功能待实现（此处简化为上一页）")
                    current_page_index = (current_page_index - 1 + total_pages) % total_pages
                elif action == 'scroll_down':
                    print("向下滚动功能待实现（此处简化为下一页）")
                    current_page_index = (current_page_index + 1) % total_pages
                elif action == 'quit':
                    print("用户选择退出故事阅读。")
                    break  # 退出故事阅读循环

                finish = bool(current_page_index >= (total_pages - 1))  # 如果当前页是最后一页，则标记为完成

            print("\n故事阅读结束。")

            # 可以在这里询问用户是否继续生成新故事
            user_choice = input("是否继续生成新故事？ (yes/no): ").strip().lower()
            if user_choice != 'yes':
                print("用户选择退出程序。")
                break

    except KeyboardInterrupt:
        print("\n程序被用户中断。")
    except Exception as e:
        print(f"\n程序运行中发生未捕获的错误: {e}")
    finally:
        presentation_manager.cleanup()
        print("\n----- 绘本生成器程序已退出 -----")


if __name__ == "__main__":
    main()