# Raspberry Pi Story Generator
# 图文故事生成器
***
**申请 API：https://aistudio.google.com/app/apikey**

**API文档：https://ai.google.dev/api?hl=zh-cn&lang=python**
***

### **项目配件清单与型号要求**

本项目旨在构建一个基于树莓派的智能绘本生成器，其硬件系统由核心计算单元、输入/输出设备及辅助配件构成，旨在实现多模态（语音、图像）交互和内容呈现。

#### **一、核心计算单元**

| 配件类别   | 要求                      | 型号/已选型号                 | 备注                                     |
| :--------- | :------------------------ | :-------------------------- | :--------------------------------------- |
| **主控板** | 性能强大，至少 4GB RAM，支持多媒体和网络连接 | **Raspberry Pi 4 Model B (4GB RAM)** | 已购，项目核心，提供计算和控制能力。       |
| **电源** | 5.1V 3A，USB-C 接口，稳定供电 | **树莓派官方电源适配器** | 已购，确保树莓派稳定运行。               |
| **外壳与散热** | 兼容 Pi 4B，自带或预留风扇位，利于散热 | **含散热风扇的兼容外壳** | 已购，保护主板，防止过热降频或损坏。     |

#### **二、存储设备**

| 配件类别   | 要求                 | 型号/已选型号                   | 备注                                       |
| :--------- | :------------------- | :---------------------------- | :----------------------------------------- |
| **操作系统存储** | 高速，至少 32GB 容量 | **32GB 高速 MicroSD 卡 (TF卡)** | 已购，树莓派的系统盘和存储空间。             |
| **卡片读写** | 支持 MicroSD 卡读写  | **MicroSD 卡读卡器** | 已购，用于将操作系统烧录到 MicroSD 卡。      |

#### **三、输入设备**

| 配件类别   | 要求                     | 型号/已选型号               | 备注                                           |
| :--------- | :----------------------- | :-------------------------- | :--------------------------------------------- |
| **语音输入** | USB 接口，免驱，拾音清晰 | **一体式 USB 免驱麦克风** | 已购，用于用户语音指令或故事灵感输入。         |
| **人机交互** | USB 接口，标准键鼠套装   | **USB 键盘和鼠标** | 已购，用于首次系统配置和日常调试。             |

#### **四、输出设备**

| 配件类别   | 要求                                   | 型号/已选型号                       | 备注                                             |
| :--------- | :------------------------------------- | :---------------------------------- | :----------------------------------------------- |
| **屏幕显示** | 4.3寸左右，HDMI 输入，分辨率适中，可触摸优先 | **4.3寸高清触摸屏 (800x480分辨率)** | 已购，项目主要的视觉输出界面，用于显示绘本内容。 |
| **屏幕连接** | DSI软排线                 | **购置屏幕附送**| 已购，连接树莓派与显示器。                       |
| **音频输出** | USB 接口，免驱，音质清晰               | **迷你电脑 USB 小音响** | 已购，用于播放故事语音朗读。                     |

---

### **项目结构**

raspberry_pi_story_generator/  
├── assets/  
│ ├── generated_audios/  
│ └── generated_images/  
├── modules/  
│ ├── api_clients/  
│ ├── image_generator.py  
│ ├── input_handler.py  
│ ├── presentation_manager.py  
│ └── story_generator.py  
├── test/  
├── .gitignore  
├── config.py  
├── main.py  
└── requirements.txt

- **main.py**: 应用程序主入口与中央控制器，负责初始化、主事件循环和模块调度。
- **config.py**: 全局配置中心，用于管理 API 密钥及其他可配置参数。
- **modules/**: 核心业务逻辑目录。
  - **input_handler.py**: 用户输入处理器，负责处理语音和文本输入。
  - **story_generator.py**: 叙事内容生成引擎，通过 Prompt 工程调用 LLM 生成结构化故事。
  - **image_generator.py**: 视觉内容生成器，为每个故事页面生成插画。
  - **presentation_manager.py**: 图形用户界面（GUI）管理器，负责所有界面的绘制和交互。
  - **api_clients/**: API 通信客户端集合，封装了与所有外部云服务（Gemini, Imagen, STT, TTS）的底层通信逻辑。
- **assets/**: 静态资源目录，存放 AI 生成的图片和音频文件。
- **test/**: 存放所有单元测试和集成测试脚本。
- **requirements.txt**: 项目的 Python 依赖库列表。

### **使用**

#### **1\. 环境准备 (Prerequisites)**

**硬件**:

- 树莓派 4B (推荐 4GB RAM)
- MicroSD 卡 (32GB+, Class 10\)
- 稳定的电源 (5V/3A)
- HDMI 显示屏
- USB 麦克风
- USB 音响或耳机

**软件**:

- Raspberry Pi OS (64-bit) with Desktop
- Python 3.11

#### **2\. 安装步骤 (Installation)**

1. **克隆代码库**  
   git clone https://github.com/your-username/raspberry\_pi\_story\_generator.git  
   cd raspberry_pi_story_generator

2. **设置 Python 虚拟环境**  
   python3 \-m venv venv  
   source venv/bin/activate

3. **安装系统依赖** (针对 PyAudio)  
   sudo apt-get update && sudo apt-get install \-y portaudio19-dev

4. **安装 Python 依赖库**  
   pip install \-r requirements.txt

5. **配置 API 密钥**
   - 复制 config.py.example (如果提供) 或手动创建 config.py 文件。
   - 在 config.py 文件中填入您的 Google AI Studio API 密钥：  
     \# config.py  
     API_KEY \= "YOUR_GOOGLE_AI_API_KEY"

#### **3\. 运行程序 (Usage)**

一切准备就绪后，在项目根目录下运行主程序：

python3 main.py

