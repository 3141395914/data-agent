"""数据分析 Agent 的主循环：模型写代码 -> 执行 -> 看结果 -> 继续。"""

import json
import os

import requests
from dotenv import load_dotenv

from config import API_URL, MAX_ROUNDS, MODEL, TIMEOUT
from tools import run_code

load_dotenv()

SYSTEM_PROMPT = """你是一个数据分析助手。用户会给你一个 CSV 文件和一个问题。
数据已经读进变量 df，你可以反复执行 Python 代码来分析它。

环境里可以直接使用：
- df：pandas DataFrame
- pd：pandas
- plt：matplotlib.pyplot，用来画图

重要规则：
1. 不要写 import 语句，上面这些已经准备好了。
2. 不要读写文件、不要访问网络、不要使用 open。
3. 画图用 plt.savefig("output/图表名.png", dpi=120)，绝对不要用 plt.show()。
4. 每次只回复一个 JSON 对象，格式二选一：
   执行代码：{"action": "run_code", "code": "这里写 Python 代码"}
   给出答案：{"action": "answer", "answer": "这里写自然语言答案"}
5. 先查看数据结构和列名，再分析，不要凭空猜列名。
6. 如果代码报错，根据报错修改后重试。
7. 最终回答用中文，数字要具体，不要笼统。
"""


def call_model(messages):
    """调用 DeepSeek，返回模型的原始回复。"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("没有找到 DEEPSEEK_API_KEY，请检查 .env 文件")

    payload = {"model": MODEL, "messages": messages, "temperature": 0}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(API_URL, headers=headers, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def parse_action(reply):
    """从模型回复里取出 JSON 动作，顺手容忍它多写的解释。"""
    text = reply.strip()
    if text.startswith("```"):
        text = text.strip("`").replace("json\n", "", 1)
    start = text.find("{")
    if start == -1:
        raise ValueError(f"模型没有返回 JSON：{text[:100]}")
    action, _ = json.JSONDecoder().raw_decode(text[start:])
    return action


def format_observation(result):
    """把执行结果整理成一段话，喂回给模型。"""
    if result["ok"]:
        output = result["output"].strip() or "（代码执行了，但没有 print 任何东西）"
        return f"代码执行成功，输出：\n{output}"
    return f"代码执行失败，报错：\n{result['error']}"


def run(question, csv_path, verbose=True):
    """跑一轮 Agent，返回 (最终答案, 执行过的步骤列表)。"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"CSV 路径：{csv_path}\n\n问题：{question}"},
    ]
    steps = []

    for round_no in range(1, MAX_ROUNDS + 1):
        reply = call_model(messages)
        action = parse_action(reply)

        if action.get("action") == "answer":
            return action.get("answer", ""), steps

        code = (action.get("code") or "").strip()
        if not code:
            messages.append({"role": "assistant", "content": reply})
            messages.append(
                {"role": "user", "content": "你没有给出代码，请按约定重新回复 JSON。"}
            )
            continue

        result = run_code(code, csv_path)
        steps.append({"code": code, "result": result})

        if verbose:
            print(f"\n[第 {round_no} 轮] 执行代码：")
            print(code)
            if result["ok"]:
                preview = result["output"].strip()[:500] or "（没有输出）"
                print(f"输出：{preview}")
            else:
                print(f"报错：{result['error']}")

        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": format_observation(result)})

    return "达到最大轮数，Agent 没有得出结论", steps
