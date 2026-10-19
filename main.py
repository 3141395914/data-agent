"""命令行入口。

用法：
    python main.py data.csv "哪个城市岗位最多？"
"""

import sys

from agent import run


def main():
    if len(sys.argv) < 3:
        print('用法：python main.py <csv路径> "你的问题"')
        return

    csv_path = sys.argv[1]
    question = " ".join(sys.argv[2:])

    answer, steps = run(question, csv_path)

    print("\n" + "=" * 60)
    print("最终回答：")
    print(answer)
    print(f"\n共执行 {len(steps)} 段代码")


if __name__ == "__main__":
    main()
