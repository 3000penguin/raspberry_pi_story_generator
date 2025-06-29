import os
import pygame
from PIL import Image, ImageDraw, ImageFont
import typing
import time
from typing import cast, Literal


# noinspection PyMethodMayBeStatic
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
        self.font_size_title = 28
        self.font_size_text = 20

        # 初始化按钮相关属性
        self.left_button_rect = None
        self.right_button_rect = None
        self.left_button_image = None
        self.right_button_image = None

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
                self.font_title = ImageFont.truetype(self.font_path, self.font_size_title)
                self.font_text = ImageFont.truetype(self.font_path, self.font_size_text)

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
        """测试字体是否支持中文字符"""
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
                self.font_title = ImageFont.truetype(self.font_path, self.font_size_title)
                self.font_text = ImageFont.truetype(self.font_path, self.font_size_text)
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
        根据指定宽度和字体，对中文文本进行智能换行。
        适用于中文、英文文本，按字符逐个检查宽度，支持中英文混合。
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

    def display_story_page(self, page_text: str, image_path: str | None, page_number: int | None = None):
        """
        在屏幕上显示一个故事页面（图片和文本）。
        根据屏幕尺寸自动判断横屏和竖屏模式：
        - 横屏模式（宽>高）：图片和文字左侧布局
        - 竖屏模式（高>宽）：图片和文字上下布局

        page_text: 故事段落的文本内容。
        image_path: 插画图片的文件路径。
        page_number: 当前页码 (可选)。
        """
        if self.test_mode:
            # 测试模式：只在控制台输出信息
            print(f"\n===== 第 {page_number or '?'} 页 =====")
            print(f"文本内容: {page_text}")
            print(f"图片路径: {image_path}")
            if image_path and os.path.exists(image_path):
                print(f"图片存在: {image_path}")
            else:
                print(f"图片不存在或路径为空: {image_path}")
            print("=" * 50)
            return

        if not self.pygame_initialized:
            print("显示器未初始化，无法呈现内容。")
            return

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
                text_surface_pil = Image.new('RGBA',
                                             (int(self.font_text.getlength(line) + 5),
                                                   int(self.font_text.getbbox(line)[3] - self.font_text.getbbox(line)[1] + 5)),
                                             (255, 255, 255, 0))

                ImageDraw.Draw(text_surface_pil).text((0, 0),
                                                      line,
                                                      font=self.font_text,
                                                      fill=(0, 0, 0))

                text_surface_pygame = pygame.image.fromstring(text_surface_pil.tobytes(),
                                                              text_surface_pil.size,
                                                              'RGBA' if text_surface_pil.mode == 'RGBA' else 'RGB'
                                                              ).convert_alpha()

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

        # 显示页码
        if page_number is not None:
            page_num_text = f"第 {page_number} 页"
            bbox = self.font_text.getbbox(page_num_text)
            page_num_surface_pil = Image.new('RGBA', (int(self.font_text.getlength(page_num_text) + 5),
                                                      bbox[3] - bbox[1] + 5), (255, 255, 255, 0))
            ImageDraw.Draw(page_num_surface_pil).text((0, 0), page_num_text, font=self.font_text, fill=(100, 100, 100))
            page_num_surface_pygame = pygame.image.fromstring(page_num_surface_pil.tobytes(),
                                                              page_num_surface_pil.size,
                                                             'RGBA' if page_num_surface_pil.mode == 'RGBA' else 'RGB').convert_alpha()

            page_num_rect = page_num_surface_pygame.get_rect(
                bottomright=(screen_width - 10, screen_height - 10))
            self.screen.blit(page_num_surface_pygame, page_num_rect)

        # 显示翻页按钮
        self._draw_page_buttons()

        pygame.display.flip()

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
                        print("检测到 ↑ (向上滚动)")
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
        """加载按钮图片"""
        try:
            # 获取当前文件的目录
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
                print(f"未找到右箭��按钮图片: {right_button_path}")
                self.right_button_image = self._create_arrow_button('right')

        except Exception as e:
            print(f"加载按钮图片失败: {e}")
            # 创建默认按钮
            self.left_button_image = self._create_arrow_button('left')
            self.right_button_image = self._create_arrow_button('right')

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
