"""执行模型生成的 Python 代码。

安全上做了三件事：
1. 在单独的子进程里执行，超时可以直接杀掉，不会卡死主程序。
2. 只提供白名单里的内置函数，删掉 open、eval、exec、import 这些危险入口。
3. 环境里不放 os、sys，模型碰不到文件系统和系统命令。
"""

import io
import multiprocessing as mp
import os
import queue
import contextlib

from config import CODE_TIMEOUT, OUTPUT_DIR

# 允许模型使用的内置函数。open、eval、exec、__import__ 都不在里面。
SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "print": print,
    "range": range,
    "round": round,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
}


def _worker(code, csv_path, out_queue):
    """子进程里真正执行代码的地方。"""
    try:
        import matplotlib

        matplotlib.use("Agg")  # 不弹窗，只往文件里画
        matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
        matplotlib.rcParams["axes.unicode_minus"] = False

        import matplotlib.pyplot as plt
        import pandas as pd

        df = pd.read_csv(csv_path)

        env = {
            "__builtins__": SAFE_BUILTINS,
            "df": df,
            "pd": pd,
            "plt": plt,
        }

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exec(code, env)

        out_queue.put({"ok": True, "output": buffer.getvalue(), "error": ""})
    except Exception as e:
        out_queue.put(
            {"ok": False, "output": "", "error": f"{type(e).__name__}: {e}"}
        )


def run_code(code, csv_path):
    """执行一段代码，返回 {ok, output, error}。"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    csv_path = os.path.abspath(csv_path)

    out_queue = mp.Queue()
    process = mp.Process(target=_worker, args=(code, csv_path, out_queue))
    process.start()
    process.join(CODE_TIMEOUT)

    if process.is_alive():
        process.terminate()
        process.join()
        return {
            "ok": False,
            "output": "",
            "error": f"执行超时（超过 {CODE_TIMEOUT} 秒），可能有死循环",
        }

    try:
        return out_queue.get_nowait()
    except queue.Empty:
        return {"ok": False, "output": "", "error": "代码执行完毕但没有返回结果"}
