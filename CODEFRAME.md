### **树莓派个性化儿童绘本/故事生成器 - 项目架构与规划**

#### **一、项目目标回顾**

本项目旨在开发一个基于树莓派的智能绘本生成器。通过结合 Google Gemini AI 模型，实现用户提供主题后，系统能够自动生成故事情节，并为每个故事段落生成对应的插画图片，最终在屏幕上进行图文并茂的呈现。音频朗读功能将作为后期扩展实现。

#### **二、核心模块功能规划与代码实现**

我们将对之前定义的各个模块进行细化，使其描述与当前代码实现保持一致。

1.  **`config.py` - 配置 (Configuration)**
    * **职责：** 集中管理项目的所有可配置参数和 API Key。
    * **关键配置：**
        * `GOOGLE_GENAI_API_KEY`: 您的 Google Gen AI API Key。
        * `STORY_MAX_WORDS`: 故事最大长度。
        * `STORY_TEMPERATURE`: 故事生成温度。
        * `ASSETS_IMAGE_DIR`: 生成图片保存路径。
        * `ASSETS_AUDIO_DIR`: 生成音频保存路径。
    * **模型名称：**
        * `GEMINI_TEXT_MODEL = "gemini-2.5-flash"`
        * `GEMINI_IMAGE_GENERATION_MODEL = "gemini-2.0-flash-preview-image-generation"`

2.  **`modules/api_clients/llm_client.py` - 文本生成 API 客户端**
    * **职责：** 专门负责调用 `gemini-2.5-flash` 模型，根据文本提示生成故事情节。
    * **核心方法：** `generate_text(prompt_text, model_name, max_tokens, temperature, ...)`
    * **实现要点：**
        * 使用 `from google import genai` 导包。
        * 初始化 `self.client = genai.Client(api_key=api_key)`。
        * 调用 `self.client.models.generate_content(model=model_name, contents=prompt_text, ...)`。
        * 处理 `response.text` 获取生成的故事文本。

3.  **`modules/api_clients/image_gen_client.py` - 图像生成 API 客户端**
    * **职责：** 专门负责调用图像生成模型，根据文本提示生成图片。
    * **核心方法：** `generate_image(prompt_text, model_name, ...)`
    * **实现要点：**
        * 使用 `from google import genai` 和 `from google.generativeai import types` 导包。
        * 初始化 `self.client = genai.Client(api_key=api_key)`。
        * 调用 `self.client.models.generate_content(...)`。
        * 解析响应，从 `inline_data` 中提取图片数据，并返回一个 `PIL.Image` 对象。

4.  **`modules/story_generator.py` - 故事生成逻辑**
    * **职责：** 编排整个故事的生成流程，包括定义故事结构、构建详细的 Prompt，并调用 `llm_client.py` 获取结构化故事数据。
    * **核心概念：** 定义 `StorySegment` 和 `StoryResponse` 的 `TypedDict` 结构，以实现结构化输出。
    * **核心方法：** `generate_structured_story(theme, num_pages)`
    * **实现要点：**
        * 构建详细的 Prompt，指导 `gemini-2.5-flash` 模型生成特定JSON格式的故事序列。
        * 调用 `llm_client.generate_text()` 方法获取包含JSON的字符串。
        * **手动解析**返回的JSON字符串，清理可能存在的前后缀（如\`\`\`json），并提取出结构化的故事段落列表。

5.  **`modules/image_generator.py` - 图像处理与整合**
    * **职责：** 负责为每个故事段落生成对应的插画。
    * **核心方法：** `generate_illustrations_for_story(story_segments)`
    * **实现要点：**
        * 接收来自 `story_generator.py` 的结构化故事段落列表。
        * 遍历每个 `StorySegment`，提取其中的 `image_prompt`。
        * 调用 `image_gen_client.py` 中的 `generate_image()` 方法来生成 `PIL.Image` 对象。
        * 将生成的图片保存到指定目录，并将文件路径与对应的故事段落关联起来。

6.  **`modules/presentation_manager.py` - 内容呈现 (Content Presentation)**
    * **职责：** 将故事文本和生成的插画在屏幕上进行图文并茂的展示。
    * **核心方法：** `display_story_page(text, image_path)`
    * **实现要点：**
        * (规划中) 使用 `pygame` 或 `tkinter` 库加载图片和渲染文本。
        * (规划中) 管理故事的翻页逻辑。
        * **注意：** 音频朗读部分在此阶段暂不实现。

7.  **`modules/input_handler.py` - 用户输入 (User Input)**
    * **职责：** 负责获取用户的故事主题输入。
    * **核心方法：** `record_audio()` 和 `audio_to_text_from_types()`
    * **实现要点：**
        * **语音输入：** 使用 `pyaudio` 实现动态录音，根据音量大小自动判断录音起止。
        * **语音转文本：** 直接使用 `SpeechRecognition` 库调用 Google 的语音识别服务，将录制的音频数据转换为文本。**（注意：当前未通过独立的 `stt_client.py` 模块）**

8.  **`main.py` - 主程序流程 (Main Program Flow)**
    * **职责：** 作为整个项目的入口，协调所有模块的调用顺序，并管理主要的流程。
    * **实现要点：** (当前为模板文件，最终目标如下)
        * 初始化各个模块。
        * 调用 `input_handler` 获取主题。
        * 调用 `story_generator` 生成结构化故事。
        * 调用 `image_generator` 生成插画。
        * 调用 `presentation_manager` 逐页/段显示故事。

#### **三、开发路线图与测试现状**

* **阶段一：API 客户端与核心生成逻辑 (已完成)**
    * **目标：** 确保 `llm_client.py` 和 `image_gen_client.py` 能够独立工作，`story_generator.py` 能够生成结构化故事。
    * **现状：** **已完成**。核心生成逻辑已通过测试。
    * **相关测试：**
        * `test/test_story_generate.py`: 验证 `llm_client` 生成结构化JSON的能力。
        * `test/test_core_gen.py`: 整合测试 `story_generator` 和 `image_generator`，确保从主题到图文数据能完整生成。

* **阶段二：输入模块与整合测试 (已部分完成)**
    * **目标：** 实现 `input_handler.py` 的语音输入功能，并与核心生成模块串联。
    * **现状：** 语音输入和转文本功能已实现并测试。
    * **相关测试：**
        * `test/test_dynamic_get_audio.py`: 验证动态录音功能。
        * `test/test_audio_to_text.py`: 验证完整的录音到文本转换流程。

* **阶段三：内容呈现与总流程**
    * **目标：** 实现 `presentation_manager.py`，并在 `main.py` 中串联完整流程。
    * **优先级：** **当前重点**。
    * **测试：** 编写一个简单的 `main.py` 来串联 `input_handler`, `story_generator`、`image_generator` 和 `presentation_manager` 的基本功能。

* **阶段四：后期优化与音频补充**
    * **目标：** 实现文本转语音（TTS）和音频播放功能，进行错误处理、性能优化等。
    * **优先级：** 低（待核心功能完成后）。

---

这个规划旨在帮助您清晰地了解每一步需要做什么，以及这些步骤之间的依赖关系。
