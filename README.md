# 数据分析 Agent

给一个 CSV 和一个自然语言问题，Agent 自己写 Python 代码分析数据，
执行后看结果，出错就改代码重试，最后用中文回答。

## 运行效果

```
$ python main.py "result.csv" "哪个城市岗位最多？"

[第 1 轮] 执行代码：
print(df.shape)
print(df.columns.tolist())
print(df.head())
输出：(47, 6)
['url', 'company', 'job_title', 'salary', 'education', 'location']

[第 2 轮] 执行代码：
print(df['location'].value_counts())
输出：全国 36，上海市浦东新区 6，四川省成都市 2 ...

最终回答：
按原始 location 字段统计，出现最多的是"全国"（36 个岗位），但它不是具体城市。
若只看具体城市，上海市最多：浦东新区 6 个、长宁区 1 个、虹口区 1 个，合计 8 个。
```

画图也能做：

```
$ python main.py "result.csv" "统计各城市的岗位数量，画一个柱状图"
...
柱状图已保存为 output/城市岗位数量.png
```

## 工作原理

核心是一个循环，最多跑 6 轮：

```
模型思考 → 输出一段 Python 代码 → 程序执行 → 把输出或报错发回模型 → 模型继续思考
```

模型每次只回复一个 JSON，两种动作二选一：

```json
{"action": "run_code", "code": "df['location'].value_counts()"}
{"action": "answer", "answer": "岗位最多的是……"}
```

代码报错不会中断流程，报错信息会原样发回给模型，让它自己改。

实际跑的时候遇到过一个真实案例：模型写了 `import re`，被安全白名单拦下，
收到 `ImportError: __import__ not found` 之后，它改成了不用 import 的字符串处理写法，
重试成功并生成了图表。

## 安全设计

模型生成的代码是不可信的，所以加了三道闸：

**子进程隔离**：代码在单独的子进程里执行，超过 15 秒直接杀掉，死循环不会卡住主程序。

**内置函数白名单**：只开放 len、range、sum、sorted 这类安全的函数，
`open`、`eval`、`exec`、`__import__` 全部不提供，模型无法读写文件或导入模块。

**不提供系统模块**：执行环境里没有 `os`、`sys`，碰不到文件系统和系统命令。

环境里只放了三样东西：`df`（DataFrame）、`pd`（pandas）、`plt`（matplotlib）。

## 安装与运行

```bash
pip install -r requirements.txt
```

复制 `.env.example` 为 `.env`，填入 DeepSeek 的 Key。

运行：

```bash
python main.py "你的数据.csv" "你的问题"
```

图表保存在 `output/` 目录。

## 目录结构

```
config.py     接口地址、最大轮数、代码超时时间
tools.py      在子进程里执行代码，带白名单和超时保护
agent.py      Agent 循环：调模型、解析动作、执行、把结果喂回去
main.py       命令行入口
output/       生成的图表
```

## 已知限制与下一步

- 只支持单表 CSV，不支持多表关联和 Excel 多 sheet。
- 没有多轮对话记忆，每次提问都是从零开始。
- 没有缓存成功的问题和代码，相同问题会重新生成。
- 安全性依赖黑名单思路，真要上线还需要容器级隔离，比如 Docker 或 gVisor。
- 没有评测集，下一步可以准备一批问题和标准答案，测执行成功率和答案准确率。
