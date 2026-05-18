# Dictation Dad

爸爸虽然不在家，但是依然给你们准备了听写作业。

一款支持多种听写任务的本地化听写软件，运行在本地笔记本上，使用 PyWebview 提供 GUI 界面。

## 功能特性

- **词表管理**：支持多级目录浏览，面包屑导航，创建目录和上传 CSV 词表文件
- **三种听写模式**：
  - 🇨🇳 中文生词（`.ch_word.csv`）
  - 🇬🇧 英文生词（`.en_word.csv`）
  - 🀄 古文释义（`.ch_classical.csv`）
- **TTS 音频生成**：使用 Edge-TTS，自动缓存到本地，避免重复生成
- **顺序/乱序听写**：支持两种听写顺序选择
- **自定义设置**：可调整音频时长系数、等待时间、倒计时提示音次数等参数
- **听写回顾**：听写完成后可查看所有答案

## 安装与运行

### 环境要求

- Python >= 3.12
- macOS / Windows / Linux

### 安装依赖

```bash
uv sync
```

或

```bash
pip install -e ".[dev]"
```

### 运行程序

```bash
uv run python main.py
```

或

```bash
python main.py
```

### 运行测试

```bash
uv run pytest tests/ -v
```

## 词表文件格式

词表文件为 CSV 格式，需使用 UTF-8 编码：

| 文件类型 | 必需列 | 示例 |
|---------|--------|------|
| `.ch_word.csv` | `speech` | 葡萄 |
| `.en_word.csv` | `speech`, `answer` | 苹果, apple |
| `.ch_classical.csv` | `speech`, `answer` | 一狼假寐的"寐", 睡觉 |

## 项目结构

```
dictation_dad/
├── __init__.py
├── settings.py       # 设置管理（YAML 持久化）
├── file_manager.py   # 文件浏览、创建、删除、保存
├── strategies.py     # 听写策略（策略模式）
├── tts.py            # Edge-TTS 音频生成与缓存
├── api.py            # PyWebview JS API
└── app.py            # 应用入口
static/
├── index.html        # 主页面
├── css/
│   └── style.css     # 样式
└── js/
    └── app.js        # 前端逻辑
tests/                # 单元测试（104 个，全覆盖）
```

## 配置说明

设置保存在 `./settings.yaml` 中，包含以下参数：

- `audio_duration_factor`：音频时长系数（默认 1.5）
- `extra_wait_time`：额外等待时间，单位秒（默认 3.0）
- `min_wait_time`：最短等待时间，单位秒（默认 5.0）
- `countdown_beep_count`：倒计时提示音次数（默认 3）

等待时间计算公式：
```
最终等待时间 = ceil(max(音频时长 * 音频时长系数 + 额外等待时间, 最短等待时间))
```
