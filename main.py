"""命令行入口。

用法：
    python main.py data.csv "哪个城市岗位最多？"
"""

import os
import sys

from agent import run


def main():
    if len(sys.argv) < 3:
        print('用法：python main.py <csv路径> "你的问题"')
        return

    csv_path = sys.argv[1]
    question = " ".join(sys.argv[2:])

    # 文件不存在就别浪费模型调用，直接告诉用户
    if not os.path.isfile(csv_path):
        print(f"找不到文件：{csv_path}")
        print("请检查路径，或者把 CSV 放到项目目录下再传相对路径。")
        return

    answer, steps = run(question, csv_path)

    print("\n" + "=" * 60)
    print("最终回答：")
    print(answer)
    print(f"\n共执行 {len(steps)} 段代码")


if __name__ == "__main__":
    main()
