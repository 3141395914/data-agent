"""数据分析 Agent 的配置。"""

import os

# DeepSeek 接口
API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"
TIMEOUT = 120

# Agent 最多尝试几轮（模型写代码 -> 执行 -> 看结果）
MAX_ROUNDS = 6

# 生成的代码最多执行多少秒
CODE_TIMEOUT = 15

# 图表输出目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
