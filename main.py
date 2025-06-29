import config  # 导入配置文件
from config import STORY_NUM_PAGES
from modules.api_clients.stt_client import *
from modules.image_generator import ImageGenerator
from modules.presentation_manager import PresentationManager
from modules.story_generator import StoryGenerator


def main():
    print("----- 树莓派个性化儿童绘本生成器启动 -----")

    # 1. 初始化核心模块
    story_generator = StoryGenerator()  # 内部会实例化 LLMClient
    image_generator = ImageGenerator()  # 内部会实例化 ImageGenClient

    # 初始化 PresentationManager，自动检测模式
    screen_size = (800, 480)
    screen_width, screen_height = screen_size
    presentation_manager = PresentationManager(screen_size=screen_size)

    # 检查 Pygame 是否成功初始化，如果失败则无法进行图形显示
    if not presentation_manager.pygame_initialized:
        print("\n!!! Pygame 显示器初始化失败。程序将以控制台模式运行，无法显示图形界面。")
        print("请检查树莓派显示器连接、驱动和相关配置。")
        # 显示错误弹窗
        if presentation_manager.test_mode:
            print("[弹窗] Pygame 显示器初始化失败")
        else:
            presentation_manager.show_popup(
                message="Pygame 显示器初始化失败。程序将以控制台模式运行，无法显示图形界面。\n请检查树莓派显示器连接、驱动和相关配置。",
                title="显示器初始化错误",
                buttons=[{"text": "确定", "value": "ok", "color": (220, 53, 69)}]
            )

    try:
        while True:
            # 显示主菜单
            menu_choice = presentation_manager.show_main_menu()

            if menu_choice == 'quit':
                print("用户选择退出程序。")
                break
            elif menu_choice == 'invalid':
                print("无效的输入，请重新选择。")
                continue

            # 获取故事主题
            story_theme = None
            if menu_choice == 'voice':
                print("\n----- 语音输入模式 -----")
                # 语音录制和转录（包含状态显示）
                story_theme = record_and_transcribe_speech(presentation_manager=presentation_manager)
                if not story_theme:
                    if presentation_manager.test_mode:
                        print("\n无法获取有效的故事主题，返回主菜单。")
                        continue
                    else:
                        result = presentation_manager.show_popup(
                            message="无法获取有效的故事主题。",
                            title="语音输入失败",
                            buttons=[
                                {"text": "返回主菜单", "value": "menu", "color": (108, 117, 125)},
                                {"text": "重试", "value": "retry", "color": (70, 130, 180)}
                            ]
                        )
                        if result == 'menu':
                            continue  # 返回主菜单
                        elif result == 'retry':
                            # 重试语音录入
                            story_theme = record_and_transcribe_speech(presentation_manager=presentation_manager)
                            if not story_theme:
                                continue  # 如果还是失败，返回主菜单

            elif menu_choice == 'manual':
                print("\n----- 手动输入模式 -----")
                if presentation_manager.test_mode:
                    story_theme = input("请输入故事主题: ").strip()
                else:
                    # 使用图形输入对话框
                    story_theme = presentation_manager.show_text_input_dialog(
                        message="请输入您想要创作的故事主题：",
                        title="手动输入故事主题",
                        placeholder="例如：小兔子的冒险、勇敢的小猫咪等...",
                        popup_width=450,
                        popup_height=280
                    )

                if not story_theme:
                    if not presentation_manager.test_mode:
                        presentation_manager.show_popup(
                            message="故事主题不能为空，返回主菜单。",
                            title="输入错误",
                            buttons=[{"text": "确定", "value": "ok", "color": (220, 53, 69)}]
                        )
                    continue  # 返回主菜单

            print(f"\n用户输入故事主题: '{story_theme}'")

            # 显示故事生成状态
            presentation_manager.show_status_screen("正在生成故事...", "AI创作中")

            # 2. 生成结构化故事
            print("\n----- 正在生成结构化故事和图片 -----")
            print(f"故事主题: {story_theme}, 预计 {config.STORY_MAX_WORDS} 字内...")

            story_segments, story_summary = story_generator.generate_structured_story(
                theme=story_theme,
                num_pages=STORY_NUM_PAGES
            )

            if not story_segments:
                print("!!! 故事生成失败或解析错误，请检查API Key和网络连接。")
                # 显示错误弹窗
                if presentation_manager.test_mode:
                    print("[弹窗] 故事生成失败或解析错误，返回主菜单")
                else:
                    presentation_manager.show_popup(
                        message="故事生成失败或解析错误，请检查API Key和网络连接。",
                        title="故事生成错误",
                        buttons=[{"text": "返回主菜单", "value": "menu", "color": (220, 53, 69)}]
                    )
                continue  # 返回主菜单

            print(f"\n故事摘要: '{story_summary}'")

            # 3. 生成插画
            generated_pages_data = image_generator.generate_illustrations_for_story(
                story_segments=story_segments
            )

            if not generated_pages_data:
                print("!!! 插画生成失败或未生成任何图片。")
                # 显示错误弹窗
                if presentation_manager.test_mode:
                    print("[弹窗] 插画生成失败或未生成任何图片")
                else:
                    presentation_manager.show_popup(
                        message="插画生成失败或未生成任何图片。\n程序将继续显示纯文本故事。",
                        title="插画生成警告",
                        buttons=[{"text": "继续", "value": "continue", "color": (255, 193, 7)}]
                    )
                # 即使图片失败，也可以尝试显示纯文本的故事
                generated_pages_data = [(seg.get('audio_text', ''), None) for seg in story_segments]

            print("\n----- 故事和插画生成完成 -----")

            # 4. 呈现故事页面
            print("\n----- 正在屏幕上呈现故事 -----")
            current_page_index = 0
            total_pages = len(generated_pages_data)

            want_continue = False
            finish = False

            while True:
                page_info = generated_pages_data[current_page_index]

                # 获取当前页面的音频路径（如果存在）
                audio_path = None
                if current_page_index < len(story_segments):
                    audio_path = story_segments[current_page_index].get('audio_path')

                presentation_manager.display_story_page(
                    page_info[0],  # audio_text
                    page_info[1],  # image_path
                    current_page_index + 1,  # page_number
                    audio_path  # audio_path
                )

                # 等待翻页输入
                action = presentation_manager.wait_for_page_flip_input()
                if action == 'next':
                    current_page_index = (current_page_index + 1) % total_pages

                    if finish and not want_continue:
                        # 使用弹窗询问用户故事结束后的操作
                        if presentation_manager.test_mode:
                            user_choice = input("故事读完了，选择操作 (1: 重新阅读, 2: 返回主菜单): ").strip()
                            if user_choice == '1':
                                want_continue = True
                            else:
                                break  # 返回主菜单
                        else:
                            result = presentation_manager.show_popup(
                                message="故事已读完！",
                                title="故事结束",
                                buttons=[
                                    {"text": "重新阅读", "value": "reread", "color": (70, 130, 180)},
                                    {"text": "返回主菜单", "value": "menu", "color": (40, 167, 69)}
                                ]
                            )
                            if result == 'reread':
                                want_continue = True
                            else:  # 返回主菜单
                                break

                    if want_continue:
                        if current_page_index >= total_pages:
                            current_page_index = current_page_index % total_pages

                elif action == 'prev':
                    current_page_index = (current_page_index - 1 + total_pages) % total_pages
                elif action == 'mute_toggle':
                    # 静音状态切换，重新显示当前页面以更新按钮图标，但不播放音频
                    continue  # 重新显示当前页面
                elif action == 'scroll_up':
                    print("向上滚动功能待实现（此处简化为上一页）")
                    current_page_index = (current_page_index - 1 + total_pages) % total_pages
                elif action == 'scroll_down':
                    print("向下滚动功能待实现（此处简化为下一页）")
                    current_page_index = (current_page_index + 1) % total_pages
                elif action == 'quit':
                    print("用户选择退出故事阅读，返回主菜单。")
                    # 显示退出确认弹窗
                    if presentation_manager.test_mode:
                        user_choice = input("确定要退出故事阅读吗？(y/n): ").strip().lower()
                        if user_choice == 'y' or user_choice == 'yes':
                            break  # 返回主菜单
                        else:
                            continue  # 继续当前页面
                    else:
                        result = presentation_manager.show_popup(
                            message="确定要退出故事阅读并返回主菜单吗？",
                            title="退出确认",
                            buttons=[
                                {"text": "取消", "value": "cancel", "color": (150, 150, 150)},
                                {"text": "退出", "value": "exit", "color": (220, 53, 69)}
                            ]
                        )
                        if result == 'exit':
                            break  # 返回主菜单
                        else:
                            continue  # 继续当前页面

                finish = bool(current_page_index >= (total_pages - 1))

            print("\n故事阅读结束。")

    except KeyboardInterrupt:
        print("\n程序被用户中断。")
        # 显示中断弹窗
        if presentation_manager.test_mode:
            print("[弹窗] 程序被用户中断")
        else:
            presentation_manager.show_popup(
                message="程序被用户中断。",
                title="程序中断",
                buttons=[{"text": "确定", "value": "ok", "color": (108, 117, 125)}]
            )
    except Exception as e:
        print(f"\n程序运行中发生未捕获的错误: {e}")
        # 显示错误弹窗
        if presentation_manager.test_mode:
            print(f"[弹窗] 程序运行中发生未捕获的错误: {e}")
        else:
            presentation_manager.show_popup(
                message=f"程序运行中发生未捕获的错误:\n{e}",
                title="程序错误",
                buttons=[{"text": "确定", "value": "ok", "color": (220, 53, 69)}]
            )
    finally:
        presentation_manager.cleanup()
        print("\n----- 绘本生成器程序已退出 -----")


if __name__ == "__main__":
    main()