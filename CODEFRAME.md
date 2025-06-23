### **树莓派个性化儿童绘本/故事生成器 - 课程设计规划**

#### **一、项目目标回顾**

本项目旨在开发一个基于树莓派的智能绘本生成器。通过结合 Google Gemini AI 模型，实现用户提供主题后，系统能够自动生成故事情节，并为每个故事段落生成对应的插画图片，最终在屏幕上进行图文并茂的呈现。音频朗读功能将作为后期扩展实现。

#### **二、核心模块功能规划与模型分配**

我们将对之前定义的各个模块进行细化，明确其职责和采用的模型。

1.  **`config.py` - 配置 (Configuration)**
    * **职责：** 集中管理项目的所有可配置参数和 API Key。
    * **关键配置：**
        * `GOOGLE_GENAI_API_KEY`: 您的 Google Gen AI API Key。
        * `STORY_MAX_WORDS`: 故事最大长度（推荐 200-300 token）。
        * `STORY_TEMPERATURE`: 故事生成温度（推荐 0.7-0.9）。
        * `ASSETS_IMAGE_DIR`: 生成图片保存路径，如 `"assets/generated_images"`。
    * **模型名称：**
        * `GEMINI_TEXT_MODEL = "gemini-2.5-flash"`
        * `GEMINI_IMAGE_GENERATION_MODEL = "gemini-2.0-flash-preview-image-generation"`

2.  **`llm_client.py` - 文本生成 API 客户端 (Text Generation API Client)**
    * **职责：** 专门负责调用 `gemini-2.5-flash` 模型，根据文本提示生成故事情节。
    * **核心方法：** `generate_story(prompt_text, model_name="gemini-2.5-flash", ...)`
    * **实现要点：**
        * 使用 `from google import genai` 导包。
        * 初始化 `self.client = genai.Client(api_key=api_key)`。
        * 调用 `self.client.models.generate_content(model=model_name, contents=prompt_text, ...)`。
        * 处理 `response.text` 获取生成的故事文本。

3.  **`image_gen_client.py` - 图像生成 API 客户端 (Image Generation API Client)**
    * **职责：** 专门负责调用 `gemini-2.0-flash-preview-image-generation` 模型，根据文本提示生成图片。
    * **核心方法：** `generate_image(prompt_text, model_name="gemini-2.0-flash-preview-image-generation", output_dir=..., ...)`
    * **实现要点：**
        * 使用 `from google import genai` 和 `from google.generativeai import types` 导包。
        * 初始化 `self.client = genai.Client(api_key=api_key)`。
        * 调用 `self.client.models.generate_content(model=model_name, contents=prompt_text, config=types.GenerateContentConfig(response_modalities=['IMAGE']), ...)`。
        * 解析 `response.candidates[0].content.parts` 中的 `inline_data`，进行 Base64 解码并使用 `PIL.Image` 保存图片。

4.  **`story_generator.py` - 故事生成逻辑 (Story Generation Logic)**
    * **职责：** 编排整个故事的生成流程，包括定义故事结构、构建详细的 Prompt，并调用 `llm_client.py` 获取结构化故事数据。
    * **核心概念：** 采用您提供的**结构化输出设计思路**，定义 `StorySegment` 和 `StoryResponse` 的 `TypedDict` 结构。
    * **核心方法：** `generate_structured_story(theme, pages)`
    * **实现要点：**
        * 构建详细的 Prompt，指导 `gemini-2.5-flash` 模型生成包含 `image_prompt` 和 `audio_text` 等字段的 JSON 格式故事序列。
        * 将 `response_mime_type': 'application/json'` 和 `response_schema': list[StoryResponse]` 参数传递给 `llm_client.generate_story()` 方法。
        * 解析返回的 JSON 字符串，提取出结构化的故事段落列表。

5.  **`image_generator.py` - 图像处理与整合 (Image Processing & Integration)**
    * **职责：** 负责为每个故事段落生成对应的插画。
    * **核心方法：** `generate_illustrations_for_story(story_segments)`
    * **实现要点：**
        * 接收来自 `story_generator.py` 的结构化故事段落列表。
        * 遍历每个 `StorySegment`，提取其中的 `image_prompt`。
        * 调用 `image_gen_client.py` 中的 `generate_image()` 方法来生成图片。
        * 管理图片保存路径，并将生成的图片路径与对应的故事段落关联起来，方便后续呈现。

6.  **`presentation_manager.py` - 内容呈现 (Content Presentation)**
    * **职责：** 将故事文本和生成的插画在屏幕上进行图文并茂的展示。音频部分暂不实现。
    * **核心方法：** `display_story_page(text, image_path)`
    * **实现要点：**
        * 接收故事文本和图片路径。
        * 使用 `Pillow` 库加载图片。
        * 将图片和文本内容渲染到树莓派连接的显示器上（例如使用 `pygame` 或 `tkinter` 进行简单 GUI ）。
        * **注意：** 音频朗读（调用 `tts_client.py`）部分在此阶段将作为占位符或暂不调用。

7.  **`input_handler.py` - 用户输入 (User Input)**
    * **职责：** 负责获取用户的故事主题输入。
    * **核心方法：** `get_story_theme_input()`
    * **实现要点：**
        * **语音输入：** 调用 `stt_client.py` 将麦克风捕获的语音转换为文本。
        * **图片输入（作为灵感）：** 捕捉摄像头图片。如果需要图片描述，可以考虑 `google-genai` 库的多模态输入能力，将图片和提示（如“描述这张图片”）发送给 `gemini-2.5-flash` 模型，获取文本描述。

8.  **`main.py` - 主程序流程 (Main Program Flow)**
    * **职责：** 作为整个项目的入口，协调所有模块的调用顺序，并管理主要的流程。
    * **实现要点：**
        * 初始化各个客户端和模块。
        * 调用 `input_handler` 获取主题。
        * 调用 `story_generator` 生成结构化故事。
        * 调用 `image_generator` 生成插画。
        * 调用 `presentation_manager` 逐页/段显示故事。

#### **三、开发路线图与优先级**

我们将分阶段进行，确保核心功能逐步完善。

* **阶段一：API 客户端与核心生成逻辑 (文本与图像)**
    * **目标：** 确保 `llm_client.py` 和 `image_gen_client.py` 能够独立工作，成功调用 Google Gen AI API 进行文本生成和图像生成。同时，实现 `story_generator.py` 的核心逻辑（构建 Prompt 和解析结构化输出）。
    * **优先级：** **最高。** 这是项目的功能基石。
    * **测试：** 重点测试 `test_api_clients.py` 和 `story_generator.py` 中的生成函数。

* **阶段二：整合生成与基础呈现**
    * **目标：** 实现 `image_generator.py` 整合图片生成，并让 `presentation_manager.py` 能够在屏幕上图文并茂地显示故事。
    * **优先级：** 高。
    * **测试：** 编写一个简单的 `main.py` 来串联 `story_generator`、`image_generator` 和 `presentation_manager` 的基本功能。

* **阶段三：输入模块与总流程**
    * **目标：** 实现 `input_handler.py` 的语音和图片输入功能，并完善 `main.py` 的整个流程。
    * **优先级：** 中。
    * **测试：** 完整测试从输入到最终显示的整个流程。

* **阶段四：后期优化与音频补充**
    * **目标：** 实现 `tts_client.py` 和 `presentation_manager.py` 中的音频朗读功能，进行错误处理、性能优化、用户体验改进等。
    * **优先级：** 低（待核心功能完成后）。

---

这个规划旨在帮助您清晰地了解每一步需要做什么，以及这些步骤之间的依赖关系。我们将从最重要的 API 客户端测试开始。