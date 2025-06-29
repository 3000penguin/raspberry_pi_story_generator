import os
import pygame
from PIL import Image, ImageDraw, ImageFont
import typing
import time
from typing import cast, Literal
from modules.api_clients.tts_client import tts_client


class PresentationManager:
    '''
    用于管理故事页面的显示和用户交互。
    支持图形模式和测试模式（无图形界面）。图形模式下使用 Pygame 显示故事页面，测试模式下仅在控制台输出信息。
    支持中文字体显示，自动检测系统字体。
    支持横屏和竖屏模式，根据屏幕尺寸自动调整布局。
    支持翻页按钮和键盘输入进行页面翻阅。
    支持图片和文本的智能换行显示。
    '''
    def __init__(self, screen_size: tuple = (800, 480), test_mode: bool = None):
        self.screen_size = screen_size
        self.pygame_initialized = False

        # 如果 test_mode 是 None，则自动检测
        if test_mode is None:
            # 只有在明确没有显示器的情况下才使用测试模式
            # 比如在 SSH 连接且没有 X11 转发的情况下
            self.test_mode = (os.name == 'nt' and not os.environ.get('DISPLAY')) or \
                           (os.name == 'posix' and not os.environ.get('DISPLAY') and
                            'SSH_CLIENT' in os.environ)
        else:
            self.test_mode = test_mode

        # 字体路径检测 - 支持多种操作系统和字体
        self.font_path = self._find_chinese_font()
        self.title_font_size = 28
        self.text_font_size = 20

        # 初始化按钮相关属性
        self.left_button_rect = None
        self.right_button_rect = None
        self.left_button_image = None
        self.right_button_image = None
        self.mute_button_rect = None  # 静音按钮区域
        self.mute_button_image = None  # 静音按钮图片
        self.unmute_button_image = None  # 取消静音按钮图片
        self.back_button_rect = None  # 退出按钮区域
        self.back_button_image = None  # 退出按钮图片

        print(f"初始化模式: {'测试模式' if self.test_mode else '图形模式'}")

        if not self.test_mode:
            try:
                # 初始化 pygame
                pygame.init()

                # 设置 SDL 视频驱动（树莓派特定优化）
                if os.name == 'posix':  # Linux/Unix (包括树莓派)
                    # 尝试使用不同的视频驱动
                    if not pygame.display.get_init():
                        print("尝试初始化显示系统...")
                        # 在树莓派上，可能需要设置特定的视频驱动
                        os.environ.setdefault('SDL_VIDEODRIVER', 'fbcon')
                        pygame.display.init()
                elif os.name == 'nt':  # Windows
                    os.environ['SDL_VIDEODRIVER'] = 'windib'

                # 检查可用的显示驱动
                available_drivers = pygame.display.get_driver()
                print(f"当前显示驱动: {available_drivers}")

                # 尝试创建显示窗口
                try:
                    # 使用全屏模式，去掉窗口装饰
                    self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
                    self.screen_size = self.screen.get_size()
                    print(f"成功创建全屏显示窗口: {self.screen_size}")
                except pygame.error as display_error:
                    print(f"创建全屏窗口失败，尝试无边框窗口: {display_error}")
                    # 如果全屏失败，尝试无边框窗口
                    try:
                        self.screen = pygame.display.set_mode(self.screen_size, pygame.NOFRAME | pygame.DOUBLEBUF)
                        print(f"使用无边框窗口模式: {self.screen_size}")
                    except pygame.error as noframe_error:
                        print(f"无边框模式也失败，使用普通窗口: {noframe_error}")
                        self.screen = pygame.display.set_mode(self.screen_size, pygame.DOUBLEBUF)
                        print(f"使用普通窗口模式: {self.screen_size}")

                pygame.display.set_caption("AI 绘本故事")

                self.pygame_initialized = True

                # 加载字体
                self.font_title = ImageFont.truetype(self.font_path, self.title_font_size)
                self.font_text = ImageFont.truetype(self.font_path, self.text_font_size)
                # 加载一个指定路径（self.font_path）的字体文件，并设置字体大小为 self.text_font_size，生成一个字体对象，赋值给 self.font_text。
                # 这样后续可以用 self.font_text 进行文本渲染，支持中文和自定义字号。

                # 加载按钮图片
                self._load_button_images()

                # 测试显示 - 填充白色背景
                self.screen.fill((255, 255, 255))
                pygame.display.flip()

                print("Pygame 图形模式初始化成功!")

            except Exception as e:
                print(f"Pygame 初始化失败，切换到测试模式: {e}")
                print(f"错误详情: {type(e).__name__}: {str(e)}")
                self.test_mode = True
                self.pygame_initialized = False
                self.screen = None
                self._init_test_mode()
        else:
            self.screen = None
            self._init_test_mode()

    def _find_chinese_font(self):
        """查找系统中可用的中文字体"""
        # 定义可能的字体路径（按优先级排序）
        font_paths = []

        if os.name == 'nt':  # Windows
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",    # 黑体
                "C:/Windows/Fonts/simsun.ttc",    # 宋体
                "C:/Windows/Fonts/simkai.ttf",    # 楷体
            ]
        else:  # Linux/Unix (包括树莓派)
            font_paths = [
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf",
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/TTF/wqy-zenhei.ttc",
                "/usr/share/fonts/TTF/wqy-microhei.ttc",
                # 树莓派可能的路径
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/opt/vc/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                # 最后才使用英文字体作为后备
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            ]

        # 查找第一个存在的字体文件
        for font_path in font_paths:
            if os.path.exists(font_path):
                print(f"找到可用字体: {font_path}")
                # 验证字体是否支持中文
                if self._test_font_chinese_support(font_path):
                    return font_path
                else:
                    print(f"字体 {font_path} 不支持中文，继续查找...")

        print("警告: 未找到支持中文的字体文件，需要安装中文字体")
        # 如果都找不到，返回第一个存在的字体（可能不支持中文）
        for font_path in font_paths:
            if os.path.exists(font_path):
                print(f"使用后备字体: {font_path}")
                return font_path

        return None

    def _test_font_chinese_support(self, font_path):
        """测试字体���否支持中文字符"""
        try:
            test_font = ImageFont.truetype(font_path, 20)
            # 测试一个简单的中文字符
            test_char = "中"
            bbox = test_font.getbbox(test_char)
            # 如果字体支持中文，bbox应该有合理的尺寸
            return (bbox[2] - bbox[0]) > 0 and (bbox[3] - bbox[1]) > 0
        except Exception as e:
            print(f"测试字体 {font_path} 时出错: {e}")
            return False

    def _init_test_mode(self):
        """初始化测试模式"""
        try:
            if self.font_path and os.path.exists(self.font_path):
                self.font_title = ImageFont.truetype(self.font_path, self.title_font_size)
                self.font_text = ImageFont.truetype(self.font_path, self.text_font_size)
                print(f"测试模式: 成功加载字体 {self.font_path}")
            else:
                raise Exception(f"字体文件不存在: {self.font_path}")
        except Exception as e:
            print(f"无法加载字体文件 {self.font_path}: {e}")
            # 使用默认字体
            try:
                self.font_title = ImageFont.load_default()
                self.font_text = ImageFont.load_default()
                print("测试模式: 使用默认字体")
            except Exception as default_font_error:
                print(f"默认字体加载失败: {default_font_error}")
                self.font_title = None
                self.font_text = None
        print("运行在测试模式下（无图形界面显示）")

    @staticmethod
    def _wrap_text_for_display(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> typing.List[str]:
        """
        根据指定宽度和字体�����������文文本进行智能换行。
        ���用于中文、英文文本，按字符逐个检查宽度，支持中英文混合。
        """
        lines = []
        if not text:
            return [""]

        current_line = ""

        for char in text:
            # 测试添加当前字符后的行宽度
            test_line = current_line + char

            if font.getlength(test_line) <= max_width:
                current_line += char
            else:
                # 如果当前行不为空，保存当前行
                if current_line:
                    lines.append(current_line)
                    current_line = char
                else:
                    # 如果单个字符就超过最大宽度，强制添加
                    current_line = char

        # 添加最后一行
        if current_line:
            lines.append(current_line)

        return lines if lines else [""]

    def _render_text_to_surface(self, text: str, font, color: tuple = (0, 0, 0), padding: int = 5) -> pygame.Surface:
        """将文本渲染为 pygame Surface（通用方法）"""
        try:
            # 用指定的字体 font 计算字符串 text 的边界框
            bbox = font.getbbox(text)
            text_width = int(bbox[2] - bbox[0] + padding * 2)
            text_height = int(bbox[3] - bbox[1] + padding * 2)

            text_surface_pil = Image.new('RGBA', (text_width, text_height), (255, 255, 255, 0))
            ImageDraw.Draw(text_surface_pil).text((padding, padding), text, font=font, fill=color)

            text_surface_pygame = pygame.image.fromstring(
                text_surface_pil.tobytes(),
                text_surface_pil.size,
                'RGBA'
            ).convert_alpha()

            return text_surface_pygame
        except Exception as e:
            print(f"文本��染失败: {e}")
            return pygame.Surface((1, 1), pygame.SRCALPHA)

    def _check_test_mode_action(self, action_description: str) -> bool:
        """检查测试模式并输出信息"""
        if self.test_mode:
            print(f"\n[��试模式] {action_description}")
            return True
        return False

    def display_story_page(self, page_text: str, image_path: str | None, page_number: int | None = None, audio_path: str | None = None):
        """
        在屏幕上显示一个故事页面（图片和文本），并播放音频。
        根据屏幕尺寸自动判断横屏和竖屏模式：
        - 横屏模式（宽>高）：图片和文字左侧布局
        - 竖屏模式（高>宽）：图片和文字上下布局

        page_text: 故事段落的文本内容。
        image_path: 插画图片的文件路径。
        page_number: 当前页码 (可选)。
        audio_path: 音频文件路径 (可选)。
        """
        # 使用新的测试模式检查方法
        if self._check_test_mode_action(f"显示第 {page_number or '?'} 页\n文本: {page_text}\n图片: {image_path}\n音频: {audio_path}"):
            if image_path and os.path.exists(image_path):
                print(f"图片存在: {image_path}")
            else:
                print(f"图片不存在或路径为空: {image_path}")

            if audio_path and os.path.exists(audio_path):
                print(f"音频存在: {audio_path}")
                print("测试模式：模拟播放音频")
            else:
                print(f"音频不存在或路径为空: {audio_path}")
            print("=" * 50)
            return

        if not self.pygame_initialized:
            print("显示器未初始化，无法呈现内容。")
            return

        # 播放当前页面的音频
        if audio_path and os.path.exists(audio_path):
            print(f"开始播放第 {page_number or '?'} 页的音频")
            tts_client.play_audio(audio_path)
        elif page_text:
            # 如果没有预生成的音频文件，实时生成并播放
            print(f"实时生成第 {page_number or '?'} 页的音频")
            tts_client.generate_and_play(page_text, f"temp_page_{page_number or 'unknown'}.mp3")

        self.screen.fill((255, 255, 255))

        screen_width, screen_height = self.screen_size
        padding_x = 20
        padding_y = 10

        # 判断是否为横屏模式（宽度大于高度）
        is_landscape = screen_width > screen_height

        if is_landscape:
            # 横屏模式：左右布局，图片在左，文字在右
            image_display_width = int(screen_width * 0.6)
            text_display_width = int(screen_width * 0.4)

            # 图片区域
            image_area_rect = (padding_x, padding_y, image_display_width - padding_x, screen_height - 2 * padding_y)
            # 文字区域
            text_area_rect = (image_display_width + padding_x, padding_y, text_display_width - 2 * padding_x, screen_height - 2 * padding_y)
        else:
            # 竖屏模式：上下布局，图片在上，文字在下
            image_display_height = int(screen_height * 0.6)
            text_display_height = int(screen_height * 0.4)

            # 图片区域
            image_area_rect = (padding_x, padding_y, screen_width - 2 * padding_x, image_display_height - padding_y)
            # 文字区域
            text_area_rect = (padding_x, image_display_height + padding_y, screen_width - 2 * padding_x, text_display_height - 2 * padding_y)

        # 显示图片
        if image_path and os.path.exists(image_path):
            try:
                img_pil = Image.open(image_path)
                img_width, img_height = img_pil.size

                if is_landscape:
                    max_img_width = image_area_rect[2]
                    max_img_height = image_area_rect[3]
                    # 图片居中显示在左侧区域
                    img_center_x = image_area_rect[0] + image_area_rect[2] // 2
                    img_center_y = screen_height // 2
                else:
                    max_img_width = image_area_rect[2]
                    max_img_height = image_area_rect[3]
                    # 图片居中显示在上方区域
                    img_center_x = screen_width // 2
                    img_center_y = image_area_rect[1] + image_area_rect[3] // 2

                scale_factor = min(max_img_width / img_width, max_img_height / img_height)
                new_width = int(img_width * scale_factor)
                new_height = int(img_height * scale_factor)

                img_pil = img_pil.resize((new_width, new_height),
                                         Image.Resampling.LANCZOS)
                mode = cast(Literal['P', 'RGB', 'RGBX', 'RGBA', 'ARGB'], img_pil.mode)
                img_pygame = pygame.image.fromstring(img_pil.tobytes(),
                                                     img_pil.size,
                                                     mode
                                                     ).convert_alpha()

                img_rect = img_pygame.get_rect(center=(img_center_x, img_center_y))
                self.screen.blit(img_pygame, img_rect)

            except Exception as e:
                print(f"加载或显示图片 {image_path} 失败: {e}")

        # 显示文字
        if page_text:
            if is_landscape:
                text_area_width = text_area_rect[2]
                text_start_x = text_area_rect[0]
                text_start_y = text_area_rect[1]
            else:
                text_area_width = text_area_rect[2]
                text_start_x = text_area_rect[0]
                text_start_y = text_area_rect[1]

            wrapped_lines = self._wrap_text_for_display(page_text,
                                                        self.font_text,
                                                        text_area_width)
            current_y = text_start_y

            for line in wrapped_lines:
                text_surface_pygame = self._render_text_to_surface(line, self.font_text)

                if is_landscape:
                    # 横屏模式：文字在右侧居中对齐
                    text_rect = text_surface_pygame.get_rect(
                        center=(text_start_x + text_area_width // 2, current_y + text_surface_pygame.get_height() // 2))
                else:
                    # 竖屏模式：文字在下方居中对齐
                    text_rect = text_surface_pygame.get_rect(
                        center=(screen_width // 2, current_y + text_surface_pygame.get_height() // 2))

                self.screen.blit(text_surface_pygame, text_rect)
                current_y += text_surface_pygame.get_height() + 5

        # 显示页码 - 使用通用方法
        if page_number is not None:
            page_num_text = f"第 {page_number} 页"
            page_num_surface_pygame = self._render_text_to_surface(page_num_text, self.font_text, (100, 100, 100))
            page_num_rect = page_num_surface_pygame.get_rect(
                bottomright=(screen_width - 10, screen_height - 10))
            self.screen.blit(page_num_surface_pygame, page_num_rect)

        # 显示翻页按钮、静音按钮和退出按钮
        self._draw_page_buttons()
        self._draw_mute_button()
        self._draw_back_button()

        pygame.display.flip()

    def _draw_mute_button(self):
        """绘制静音按钮"""
        if not self.pygame_initialized or not self.mute_button_image or not self.unmute_button_image:
            return

        screen_width, screen_height = self.screen_size
        button_margin = 20  # 按钮距离边缘的距离

        # 获取静音按钮尺寸
        mute_button_size = self.mute_button_image.get_size()

        # 右侧边缘中间位置（静音按钮）
        mute_x = screen_width - button_margin - mute_button_size[0]
        mute_y = (screen_height - mute_button_size[1]) // 2  # 垂直居中
        self.mute_button_rect = pygame.Rect(mute_x, mute_y, mute_button_size[0], mute_button_size[1])

        # 根据当前静音状态选择显示的图标
        if tts_client.is_muted_status():
            self.screen.blit(self.mute_button_image, (mute_x, mute_y))
        else:
            self.screen.blit(self.unmute_button_image, (mute_x, mute_y))

    def _draw_page_buttons(self):
        """绘制翻页按钮"""
        if not self.pygame_initialized or not self.left_button_image or not self.right_button_image:
            return

        screen_width, screen_height = self.screen_size
        button_margin = 20  # 按钮距离边缘的距离

        # 获取按钮尺寸
        left_button_size = self.left_button_image.get_size()
        right_button_size = self.right_button_image.get_size()

        # 左下角按钮（上一页）
        left_x = button_margin
        left_y = screen_height - button_margin - left_button_size[1]
        self.left_button_rect = pygame.Rect(left_x, left_y, left_button_size[0], left_button_size[1])

        # 右下角按钮（下一页）
        right_x = screen_width - button_margin - right_button_size[0]
        right_y = screen_height - button_margin - right_button_size[1]
        self.right_button_rect = pygame.Rect(right_x, right_y, right_button_size[0], right_button_size[1])

        # 绘制按钮
        self.screen.blit(self.left_button_image, (left_x, left_y))
        self.screen.blit(self.right_button_image, (right_x, right_y))

    def _draw_back_button(self):
        """绘制退出按钮"""
        if not self.pygame_initialized or not self.back_button_image:
            return

        screen_width, screen_height = self.screen_size
        button_margin = 20  # 按钮距离边缘的距离

        # 获取退出按钮尺寸
        back_button_size = self.back_button_image.get_size()

        # 左上角位置（退出按钮）
        back_x = button_margin
        back_y = button_margin
        self.back_button_rect = pygame.Rect(back_x, back_y, back_button_size[0], back_button_size[1])

        # 绘制按钮
        self.screen.blit(self.back_button_image, (back_x, back_y))

    def wait_for_page_flip_input(self) -> str | None:
        """
        等待用户进行翻页输入（键盘方向键或鼠标点击按钮）。
        返回: 'next' (下一页), 'prev' (上一页), 'scroll_up' (向上滚动), 'scroll_down' (向下滚动), 'quit' (退出) 或 None (无有效输入)。
        """
        if self.test_mode:
            # 测试模式：模拟用户输入
            print("测试模式：模拟用户输入 (自动翻页)")
            time.sleep(1)  # 暂停1秒模拟用户查看
            import random
            actions = ['next', 'prev', 'scroll_up', 'scroll_down']
            action = random.choice(actions)
            print(f"模拟用户操作: {action}")
            return action

        if not self.pygame_initialized:
            print("显示器未初始化，无法获取输入。")
            return None

        print("等待翻页输入：←/→ (左右翻页), ↑/↓ (上下滚动), Q (退出), 或点击屏幕按钮")
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'quit'  # 应用程序关闭事件

                # 处理键盘输入
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        print("检测到 -> (右翻页)")
                        return 'next'
                    elif event.key == pygame.K_LEFT:
                        print("检测到 <- (左翻页)")
                        return 'prev'
                    elif event.key == pygame.K_UP:
                        print("检测到 ↑ (向上滚���)")
                        return 'scroll_up'
                    elif event.key == pygame.K_DOWN:
                        print("检测到 ↓ (向下滚动)")
                        return 'scroll_down'
                    elif event.key == pygame.K_q:
                        print("检测到 Q (退出)")
                        return 'quit'
                    elif event.key == pygame.K_ESCAPE:  # 添加 ESC 键退出
                        print("检测到 ESC (退出)")
                        return 'quit'

                # 处理鼠标点击
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键点击
                        mouse_pos = event.pos

                        # 检查是否点击了左按钮（上一页）
                        if self.left_button_rect and self.left_button_rect.collidepoint(mouse_pos):
                            print("检测到点击左按钮 (上一页)")
                            return 'prev'

                        # 检查是否点击了右按钮（下一页）
                        if self.right_button_rect and self.right_button_rect.collidepoint(mouse_pos):
                            print("检测到点击右按钮 (下一页)")
                            return 'next'

                        # 检查是否点击了静音按钮
                        if self.mute_button_rect and self.mute_button_rect.collidepoint(mouse_pos):
                            # 切换静音状态
                            is_muted = tts_client.toggle_mute()
                            print(f"检测到点击静音按钮 ({'静音' if is_muted else '取消静音'})")
                            # 重新绘制当前页面以更新静音按钮图标
                            return 'mute_toggle'

                        # 检查是否点击了退出按钮
                        if self.back_button_rect and self.back_button_rect.collidepoint(mouse_pos):
                            print("检测到点击退出按钮")
                            return 'quit'

                        # 如果点击了其他区域，可以添加其他交互逻辑
                        print(f"检测到鼠标点击位置: {mouse_pos}")

            time.sleep(0.1)  # 减少CPU占用

    def cleanup(self):
        """
        处理 Pygame 资源。
        """
        if self.pygame_initialized and self.screen:
            pygame.quit()
        print("Pygame display cleaned up.")

    def _load_button_images(self):
        """���载按���图片"""
        try:
            # 获取��前文件的目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 构建UI资源路径
            ui_dir = os.path.join(os.path.dirname(current_dir), 'assets', 'ui')

            left_button_path = os.path.join(ui_dir, 'left.png')
            right_button_path = os.path.join(ui_dir, 'right.png')

            if os.path.exists(left_button_path):
                self.left_button_image = pygame.image.load(left_button_path).convert_alpha()
                print(f"成功加载左箭头按钮: {left_button_path}")
            else:
                print(f"未找到左箭头按钮图片: {left_button_path}")
                self.left_button_image = self._create_arrow_button('left')

            if os.path.exists(right_button_path):
                self.right_button_image = pygame.image.load(right_button_path).convert_alpha()
                print(f"成功加载右箭头按钮: {right_button_path}")
            else:
                print(f"未找到右箭头按钮图片: {right_button_path}")
                self.right_button_image = self._create_arrow_button('right')

            # 加载静音和取消静音按钮
            self.mute_button_image = pygame.image.load(os.path.join(ui_dir, 'mute.png')).convert_alpha()
            self.unmute_button_image = pygame.image.load(os.path.join(ui_dir, 'unmute.png')).convert_alpha()

            # 加载退出按钮
            self.back_button_image = pygame.image.load(os.path.join(ui_dir, 'back.png')).convert_alpha()

        except Exception as e:
            print(f"加载按钮图片失败: {e}")
            # 创建默认按钮
            self.left_button_image = self._create_arrow_button('left')
            self.right_button_image = self._create_arrow_button('right')
            self.mute_button_image = self._create_mute_button()
            self.unmute_button_image = self._create_unmute_button()
            self.back_button_image = self._create_back_button()

    def _create_arrow_button(self, direction):
        """创建默认的箭头按钮"""
        try:
            button_size = 60
            button_surface = pygame.Surface((button_size, button_size), pygame.SRCALPHA)

            # 绘制圆形背景
            pygame.draw.circle(button_surface, (200, 200, 200, 180),
                             (button_size//2, button_size//2), button_size//2 - 2)
            pygame.draw.circle(button_surface, (100, 100, 100),
                             (button_size//2, button_size//2), button_size//2 - 2, 2)

            # 绘制箭头
            center_x, center_y = button_size//2, button_size//2
            arrow_size = 15

            if direction == 'left':
                # 左箭头
                points = [
                    (center_x + arrow_size//2, center_y - arrow_size),
                    (center_x - arrow_size//2, center_y),
                    (center_x + arrow_size//2, center_y + arrow_size)
                ]
            else:  # right
                # 右箭头
                points = [
                    (center_x - arrow_size//2, center_y - arrow_size),
                    (center_x + arrow_size//2, center_y),
                    (center_x - arrow_size//2, center_y + arrow_size)
                ]

            pygame.draw.polygon(button_surface, (50, 50, 50), points)
            return button_surface

        except Exception as e:
            print(f"创建默认按钮失败: {e}")
            # 返回一个简单的矩形按钮
            button_surface = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.rect(button_surface, (200, 200, 200, 180), (0, 0, 60, 60))
            return button_surface

    def _create_mute_button(self):
        """创建静音按钮"""
        try:
            button_size = 60
            button_surface = pygame.Surface((button_size, button_size), pygame.SRCALPHA)

            # 绘制圆形背景
            pygame.draw.circle(button_surface, (200, 200, 200, 180),
                             (button_size//2, button_size//2), button_size//2 - 2)
            pygame.draw.circle(button_surface, (100, 100, 100),
                             (button_size//2, button_size//2), button_size//2 - 2, 2)

            # 绘制音量图标（简化的音符形状）
            center_x, center_y = button_size//2, button_size//2
            pygame.draw.polygon(button_surface, (50, 50, 50), [
                (center_x - 10, center_y - 20),
                (center_x + 10, center_y - 20),
                (center_x + 20, center_y),
                (center_x + 10, center_y + 20),
                (center_x - 10, center_y + 20),
                (center_x - 20, center_y)
            ])

            return button_surface

        except Exception as e:
            print(f"创建静音按钮失败: {e}")
            # 返回一个简单的矩形按钮
            button_surface = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.rect(button_surface, (200, 200, 200, 180), (0, 0, 60, 60))
            return button_surface

    def _create_unmute_button(self):
        """创建取消静音按钮"""
        try:
            button_size = 60
            button_surface = pygame.Surface((button_size, button_size), pygame.SRCALPHA)

            # 绘制圆形背景
            pygame.draw.circle(button_surface, (200, 200, 200, 180),
                             (button_size//2, button_size//2), button_size//2 - 2)
            pygame.draw.circle(button_surface, (100, 100, 100),
                             (button_size//2, button_size//2), button_size//2 - 2, 2)

            # 绘制音量图标（简化的音符形状，带有斜杠表示静音）
            center_x, center_y = button_size//2, button_size//2
            pygame.draw.polygon(button_surface, (50, 50, 50), [
                (center_x - 10, center_y - 20),
                (center_x + 10, center_y - 20),
                (center_x + 20, center_y),
                (center_x + 10, center_y + 20),
                (center_x - 10, center_y + 20),
                (center_x - 20, center_y)
            ])
            pygame.draw.line(button_surface, (255, 255, 255), (center_x - 15, center_y - 15), (center_x + 15, center_y + 15), 2)
            pygame.draw.line(button_surface, (255, 255, 255), (center_x + 15, center_y - 15), (center_x - 15, center_y + 15), 2)

            return button_surface

        except Exception as e:
            print(f"创建取消静音按钮失败: {e}")
            # 返回一个简单的矩形按钮
            button_surface = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.rect(button_surface, (200, 200, 200, 180), (0, 0, 60, 60))
            return button_surface

    def _create_back_button(self):
        """创建退出按钮"""
        try:
            button_size = 60
            button_surface = pygame.Surface((button_size, button_size), pygame.SRCALPHA)

            # 绘制圆形背景
            pygame.draw.circle(button_surface, (200, 200, 200, 180),
                             (button_size//2, button_size//2), button_size//2 - 2)
            pygame.draw.circle(button_surface, (100, 100, 100),
                             (button_size//2, button_size//2), button_size//2 - 2, 2)

            # 绘制简单的叉号图标
            center_x, center_y = button_size//2, button_size//2
            cross_size = 15
            pygame.draw.line(button_surface, (50, 50, 50), (center_x - cross_size, center_y - cross_size), (center_x + cross_size, center_y + cross_size), 2)
            pygame.draw.line(button_surface, (50, 50, 50), (center_x + cross_size, center_y - cross_size), (center_x - cross_size, center_y + cross_size), 2)

            return button_surface

        except Exception as e:
            print(f"创建退出按钮失败: {e}")
            # 返回一个简单的矩形按钮
            button_surface = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.rect(button_surface, (200, 200, 200, 180), (0, 0, 60, 60))
            return button_surface

    def show_popup(self, message: str, title: str = "提示", buttons: list = None,
                   popup_width: int = 400, popup_height: int = 200) -> str:
        """
        显示弹窗消息，支持自定义按钮

        Args:
            message: 弹窗消息内容
            title: ���窗标题
            buttons: 按钮列表，每个按钮是字典 {"text": "按钮文本", "value": "返回值", "color": (r,g,b)}
                    默认为 [{"text": "确定", "value": "ok", "color": (70, 130, 180)}]
            popup_width: 弹窗宽度
            popup_height: 弹窗高度

        Returns:
            str: 用户点击的按钮返回值，如 "ok", "cancel", "yes", "no" 等
        """
        # 默认按钮配置
        if buttons is None:
            buttons = [{"text": "确定", "value": "ok", "color": (70, 130, 180)}]

        # 使���通用的测试模式检查方法
        if self._check_test_mode_action(f"显示弹窗: {title}\n消息: {message}"):
            button_texts = [btn["text"] for btn in buttons]
            print(f"按钮: {', '.join(button_texts)}")
            # 测试模式默认返回第一个按钮的值
            return buttons[0]["value"]

        if not self.pygame_initialized:
            print("显示器未初始化，无法显示弹窗。")
            return buttons[0]["value"]

        screen_width, screen_height = self.screen_size

        # 计算弹窗位置（居中）
        popup_x = (screen_width - popup_width) // 2
        popup_y = (screen_height - popup_height) // 2

        # 创建半透明遮罩层
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # 半透明黑色

        # 绘制弹窗背景
        popup_surface = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
        pygame.draw.rect(popup_surface, (255, 255, 255), (0, 0, popup_width, popup_height))
        pygame.draw.rect(popup_surface, (100, 100, 100), (0, 0, popup_width, popup_height), 2)

        # 渲染标题 - 使用通用方法
        title_surface = self._render_text_to_surface(title, self.font_title, (50, 50, 50))
        title_rect = title_surface.get_rect(center=(popup_width // 2, 30))
        popup_surface.blit(title_surface, title_rect)

        # 渲染消息内容 - 使用通用方法和智能换行
        wrapped_message_lines = self._wrap_text_for_display(message, self.font_text, popup_width - 40)
        message_start_y = 70
        line_height = 25

        for i, line in enumerate(wrapped_message_lines):
            line_surface = self._render_text_to_surface(line, self.font_text)
            line_rect = line_surface.get_rect(center=(popup_width // 2, message_start_y + i * line_height))
            popup_surface.blit(line_surface, line_rect)

        # 创建按钮 - 支持多按钮布局
        button_width = max(80, popup_width // (len(buttons) + 1))  # 动态计算按钮宽度
        button_height = 35
        button_y = popup_height - 60
        button_rects = []

        # 计算按钮总宽度和间距
        total_button_width = len(buttons) * button_width
        button_spacing = 15
        total_spacing = (len(buttons) - 1) * button_spacing
        buttons_area_width = total_button_width + total_spacing

        # 按钮起始位置（居中）
        start_x = (popup_width - buttons_area_width) // 2

        for i, button_config in enumerate(buttons):
            button_x = start_x + i * (button_width + button_spacing)
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            button_rects.append((button_rect, button_config))

            # 绘制按钮背景
            button_color = button_config.get("color", (70, 130, 180))
            pygame.draw.rect(popup_surface, button_color, button_rect)
            pygame.draw.rect(popup_surface, (50, 50, 50), button_rect, 2)

            # 渲染按钮文本 - 使用通用方法
            button_text_surface = self._render_text_to_surface(
                button_config["text"], self.font_text, (255, 255, 255), padding=0
            )
            button_text_rect = button_text_surface.get_rect(center=button_rect.center)
            popup_surface.blit(button_text_surface, button_text_rect)

        # 显示弹窗
        self.screen.blit(overlay, (0, 0))
        self.screen.blit(popup_surface, (popup_x, popup_y))
        pygame.display.flip()

        # 等待用户交互
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if event.type == pygame.KEYDOWN:
                    # ESC 键返回第一个按钮（通常是取消）
                    if event.key == pygame.K_ESCAPE:
                        return buttons[0]["value"]
                    # 回车键返回最后一个按钮（通常是确定）
                    elif event.key == pygame.K_RETURN:
                        return buttons[-1]["value"]
                    # 数字键快速选择按钮（1-9）
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        button_index = event.key - pygame.K_1
                        if button_index < len(buttons):
                            return buttons[button_index]["value"]

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键点击
                        mouse_pos = event.pos
                        # 转换鼠标坐标到弹窗坐标系
                        relative_pos = (mouse_pos[0] - popup_x, mouse_pos[1] - popup_y)

                        # 检查���否点击了某个按钮
                        for button_rect, button_config in button_rects:
                            if button_rect.collidepoint(relative_pos):
                                return button_config["value"]

                        # 点击弹窗外部区域关闭弹窗（返回第一个按钮值）
                        if not (0 <= relative_pos[0] <= popup_width and 0 <= relative_pos[1] <= popup_height):
                            return buttons[0]["value"]

            time.sleep(0.01)  # 减少CPU占用

    def show_confirm_dialog(self, message: str, title: str = "确认") -> bool:
        """显示确认对话框（是/否）"""
        buttons = [
            {"text": "取消", "value": "cancel", "color": (150, 150, 150)},
            {"text": "确定", "value": "ok", "color": (70, 130, 180)}
        ]
        result = self.show_popup(message, title, buttons)
        return result == "ok"

    def show_yes_no_dialog(self, message: str, title: str = "选择") -> bool:
        """显示是否对话框"""
        buttons = [
            {"text": "否", "value": "no", "color": (180, 70, 70)},
            {"text": "是", "value": "yes", "color": (70, 180, 70)}
        ]
        result = self.show_popup(message, title, buttons)
        return result == "yes"

    def show_choice_dialog(self, message: str, choices: list, title: str = "选择") -> str:
        """显示多选择对话框"""
        buttons = []
        colors = [
            (70, 130, 180),   # 蓝色
            (70, 180, 70),    # 绿色
            (180, 140, 70),   # 橙色
            (180, 70, 180),   # 紫色
            (70, 180, 180),   # 青色
        ]

        for i, choice in enumerate(choices):
            color = colors[i % len(colors)]
            buttons.append({
                "text": choice,
                "value": f"choice_{i}",
                "color": color
            })

        result = self.show_popup(message, title, buttons)
        # 返回选择的索引
        if result.startswith("choice_"):
            return int(result.split("_")[1])
        return 0

    def show_main_menu(self) -> str:
        """显示主菜单"""
        if self.test_mode:
            print("\n----- 主菜单 -----")
            menu_choice = input("请选择操作 (1: 语音录入, 2: 手动输入, Q: 退出): ").strip().lower()
            if menu_choice == '1':
                return 'voice'
            elif menu_choice == '2':
                return 'manual'
            elif menu_choice == 'q':
                return 'quit'
            else:
                return 'invalid'
        else:
            # 图形模式显示全屏主菜单
            if not self.pygame_initialized:
                print("显示器未初始化，使用控制台菜单。")
                menu_choice = input("请选择操作 (1: 语音录入, 2: 手动输入, Q: 退出): ").strip().lower()
                if menu_choice == '1':
                    return 'voice'
                elif menu_choice == '2':
                    return 'manual'
                elif menu_choice == 'q':
                    return 'quit'
                else:
                    return 'invalid'

            # 清空屏幕，显示白色背景
            self.screen.fill((255, 255, 255))

            screen_width, screen_height = self.screen_size

            # 显示标题
            title_text = "儿童绘本生成器"
            title_surface = self._render_text_to_surface(title_text, self.font_title, (50, 50, 50))
            title_rect = title_surface.get_rect(center=(screen_width // 2, screen_height // 4))
            self.screen.blit(title_surface, title_rect)

            # 显示欢迎信息
            welcome_text = "欢迎使用树莓派个性化儿童绘本生成器！"
            welcome_surface = self._render_text_to_surface(welcome_text, self.font_text, (100, 100, 100))
            welcome_rect = welcome_surface.get_rect(center=(screen_width // 2, screen_height // 4 + 60))
            self.screen.blit(welcome_surface, welcome_rect)

            # 创建按钮
            button_width = 200
            button_height = 50
            button_spacing = 20
            buttons_start_y = screen_height // 2

            buttons_config = [
                {"text": "语音录入", "value": "voice", "color": (70, 130, 180)},
                {"text": "手动输入", "value": "manual", "color": (40, 167, 69)},
                {"text": "退出程序", "value": "quit", "color": (220, 53, 69)}
            ]

            button_rects = []
            for i, button_config in enumerate(buttons_config):
                button_x = (screen_width - button_width) // 2
                button_y = buttons_start_y + i * (button_height + button_spacing)
                button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
                button_rects.append((button_rect, button_config))

                # 绘制按钮背景
                button_color = button_config.get("color", (70, 130, 180))
                pygame.draw.rect(self.screen, button_color, button_rect)
                pygame.draw.rect(self.screen, (50, 50, 50), button_rect, 3)

                # 渲染按钮文本
                button_text_surface = self._render_text_to_surface(
                    button_config["text"], self.font_text, (255, 255, 255), padding=0
                )
                button_text_rect = button_text_surface.get_rect(center=button_rect.center)
                self.screen.blit(button_text_surface, button_text_rect)

            # 刷新显示
            pygame.display.flip()

            # 等待用户交互
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return "quit"

                    if event.type == pygame.KEYDOWN:
                        # 键盘快捷键
                        if event.key == pygame.K_1:
                            return "voice"
                        elif event.key == pygame.K_2:
                            return "manual"
                        elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                            return "quit"

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:  # 左键点击
                            mouse_pos = event.pos

                            # 检查是否点击了某个按钮
                            for button_rect, button_config in button_rects:
                                if button_rect.collidepoint(mouse_pos):
                                    return button_config["value"]

                time.sleep(0.01)  # 减少CPU占用

    def show_text_input_dialog(self, message: str, title: str = "输入", placeholder: str = "",
                               popup_width: int = 400, popup_height: int = 250) -> str:
        """
        显示文本输入对话框

        Args:
            message: 提示消息
            title: 对话框标题
            placeholder: 输��框占位符文本
            popup_width: 对话框宽度
            popup_height: 对话框高度

        Returns:
            str: 用户输入的文本，如果取消则返回空字符串
        """
        if self.test_mode:
            print(f"\n{title}")
            print(f"{message}")
            user_input = input(f"请输入 ({placeholder}): ").strip()
            return user_input

        if not self.pygame_initialized:
            print("显示器未初始化，使用控制台输入。")
            user_input = input(f"{message} ({placeholder}): ").strip()
            return user_input

        screen_width, screen_height = self.screen_size

        # 计算对话框位置（居中）
        popup_x = (screen_width - popup_width) // 2
        popup_y = (screen_height - popup_height) // 2

        # 创建半透明遮罩层
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))

        # 输���框状态
        input_text = ""
        cursor_visible = True
        cursor_timer = 0
        input_active = True

        # 输入框样式
        input_box_width = popup_width - 40
        input_box_height = 40
        input_box_x = 20
        input_box_y = popup_height - 100

        while True:
            # 更新光标闪烁
            cursor_timer += 1
            if cursor_timer >= 30:  # 每30帧切换一次光标显示状态
                cursor_visible = not cursor_visible
                cursor_timer = 0

            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return ""

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return ""  # 取消输入
                    elif event.key == pygame.K_RETURN:
                        return input_text.strip()  # 确认输入
                    elif event.key == pygame.K_BACKSPACE:
                        if input_text:
                            input_text = input_text[:-1]
                    else:
                        # 添加字符到输入文本
                        if event.unicode and len(input_text) < 100:  # 限制最大长度
                            input_text += event.unicode

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键点击
                        mouse_pos = event.pos
                        relative_pos = (mouse_pos[0] - popup_x, mouse_pos[1] - popup_y)

                        # 检查是否点击了确定按钮
                        ok_button_rect = pygame.Rect(popup_width - 170, popup_height - 50, 70, 30)
                        if ok_button_rect.collidepoint(relative_pos):
                            return input_text.strip()

                        # 检查是否点击了取消按钮
                        cancel_button_rect = pygame.Rect(popup_width - 90, popup_height - 50, 70, 30)
                        if cancel_button_rect.collidepoint(relative_pos):
                            return ""

                        # 检查是否点击了输入框
                        input_rect = pygame.Rect(input_box_x, input_box_y, input_box_width, input_box_height)
                        if input_rect.collidepoint(relative_pos):
                            input_active = True
                        else:
                            input_active = False

            # 绘制对话框
            popup_surface = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
            pygame.draw.rect(popup_surface, (255, 255, 255), (0, 0, popup_width, popup_height))
            pygame.draw.rect(popup_surface, (100, 100, 100), (0, 0, popup_width, popup_height), 2)

            # 渲染标题
            title_surface = self._render_text_to_surface(title, self.font_title, (50, 50, 50))
            title_rect = title_surface.get_rect(center=(popup_width // 2, 30))
            popup_surface.blit(title_surface, title_rect)

            # 渲染提示消息
            wrapped_message_lines = self._wrap_text_for_display(message, self.font_text, popup_width - 40)
            message_start_y = 70
            line_height = 25

            for i, line in enumerate(wrapped_message_lines):
                line_surface = self._render_text_to_surface(line, self.font_text)
                line_rect = line_surface.get_rect(center=(popup_width // 2, message_start_y + i * line_height))
                popup_surface.blit(line_surface, line_rect)

            # 绘制输入框
            input_rect = pygame.Rect(input_box_x, input_box_y, input_box_width, input_box_height)
            input_color = (255, 255, 255) if input_active else (245, 245, 245)
            border_color = (70, 130, 180) if input_active else (200, 200, 200)

            pygame.draw.rect(popup_surface, input_color, input_rect)
            pygame.draw.rect(popup_surface, border_color, input_rect, 2)

            # 渲染输入文本或占位符
            display_text = input_text if input_text else placeholder
            text_color = (50, 50, 50) if input_text else (150, 150, 150)

            if display_text:
                # 确保文本不超出输入框
                max_text_width = input_box_width - 20
                if self.font_text.getlength(display_text) > max_text_width:
                    # 如果文本太长，只显示末尾部分
                    while display_text and self.font_text.getlength(display_text) > max_text_width:
                        display_text = display_text[1:]

                text_surface = self._render_text_to_surface(display_text, self.font_text, text_color, padding=0)
                text_rect = text_surface.get_rect(midleft=(input_box_x + 10, input_box_y + input_box_height // 2))
                popup_surface.blit(text_surface, text_rect)

            # 绘制光标
            if input_active and cursor_visible and input_text:
                cursor_x = input_box_x + 10 + self.font_text.getlength(input_text)
                if cursor_x < input_box_x + input_box_width - 10:
                    pygame.draw.line(popup_surface, (50, 50, 50),
                                   (cursor_x, input_box_y + 8),
                                   (cursor_x, input_box_y + input_box_height - 8), 2)

            # 绘制按钮
            # 确定按钮
            ok_button_rect = pygame.Rect(popup_width - 170, popup_height - 50, 70, 30)
            pygame.draw.rect(popup_surface, (70, 130, 180), ok_button_rect)
            pygame.draw.rect(popup_surface, (50, 50, 50), ok_button_rect, 2)
            ok_text = self._render_text_to_surface("确定", self.font_text, (255, 255, 255), padding=0)
            ok_text_rect = ok_text.get_rect(center=ok_button_rect.center)
            popup_surface.blit(ok_text, ok_text_rect)

            # 取消按钮
            cancel_button_rect = pygame.Rect(popup_width - 90, popup_height - 50, 70, 30)
            pygame.draw.rect(popup_surface, (150, 150, 150), cancel_button_rect)
            pygame.draw.rect(popup_surface, (50, 50, 50), cancel_button_rect, 2)
            cancel_text = self._render_text_to_surface("取消", self.font_text, (255, 255, 255), padding=0)
            cancel_text_rect = cancel_text.get_rect(center=cancel_button_rect.center)
            popup_surface.blit(cancel_text, cancel_text_rect)

            # 显示对话框
            self.screen.blit(overlay, (0, 0))
            self.screen.blit(popup_surface, (popup_x, popup_y))
            pygame.display.flip()

            time.sleep(0.016)  # 约60 FPS

    def show_status_screen(self, message: str, title: str = "状态") -> None:
        """
        显示全屏状态信息界面

        Args:
            message: 状态消息内容
            title: 状态标题（可选）
        """
        if self.test_mode:
            print(f"\n[状态] {title}: {message}")
            return

        if not self.pygame_initialized:
            print(f"[状态] {title}: {message}")
            return

        # 清空屏幕，显示白色背景
        self.screen.fill((255, 255, 255))

        screen_width, screen_height = self.screen_size

        # 如果有标题，在上方显示
        if title and title != "状态":
            title_surface = self._render_text_to_surface(title, self.font_title, (100, 100, 100))
            title_rect = title_surface.get_rect(center=(screen_width // 2, screen_height // 2 - 50))
            self.screen.blit(title_surface, title_rect)

        # 在屏幕中央显示主要消息
        message_surface = self._render_text_to_surface(message, self.font_title, (50, 50, 50))
        message_rect = message_surface.get_rect(center=(screen_width // 2, screen_height // 2))
        self.screen.blit(message_surface, message_rect)

        # 添加一个简单的加载动画指示（可选的点点点）
        dots_text = "..."
        dots_surface = self._render_text_to_surface(dots_text, self.font_text, (150, 150, 150))
        dots_rect = dots_surface.get_rect(center=(screen_width // 2, screen_height // 2 + 40))
        self.screen.blit(dots_surface, dots_rect)

        # 刷新显示
        pygame.display.flip()
