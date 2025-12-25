# Smart Dev Mantis

<div align="center">

**AI 驱动的接口自动化测试平台**

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

</div>

---

## 项目简介

Smart Dev Mantis 是一个基于 LLM（大语言模型）的智能接口自动化测试平台。它通过 Claude Code CLI 将传统的手工测试流程转化为 AI 自动化工作流：

**用户输入 -> AI 生成测试用例 -> AI 执行测试 -> AI 自愈修复**

### 核心特性

- **AI 测试用例生成** - 基于 Swagger/OpenAPI 规范自动生成测试用例设计
- **智能代码生成** - 自动生成可执行的 Pytest 测试代码
- **自动自愈机制** - 执行失败时自动分析并修复语法和逻辑错误
- **业务规则支持** - 支持从 PRD 文档提取业务规则进行深度测试
- **负载测试集成** - 内置 Locust 支持进行性能压测
- **Web 可视化界面** - 提供友好的 Web UI 进行测试管理

---

## 快速开始

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/lvhxg6/smartTest.git
cd smartTest

# 安装 Python 依赖
pip install -r requirements.txt
```

### 启动 Web 服务

```bash
# 默认端口 5000
python run_web.py

# 指定端口
python run_web.py --port 8080

# 开启调试模式
python run_web.py --debug
```

访问 `http://localhost:5000` 即可使用 Web 界面。

### CLI 命令行模式

**轻量模式（仅 Swagger）:**

```bash
python -m src.main \
    --swagger api.json \
    --base-url https://api.example.com
```

**完整模式（含业务规则）:**

```bash
python -m src.main \
    --swagger api.json \
    --base-url https://api.example.com \
    --requirements rules.md \
    --data data.md \
    --token "Bearer your-token"
```

---

## 工作流程

Smart Dev Mantis 采用四阶段工作流引擎：

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Planning      │ -> │   Generating    │ -> │  Executing +    │ -> │   Finalizing    │
│   测试用例设计    │    │   代码生成      │    │  Healing 自愈   │    │   报告生成      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 1. Planning（规划阶段）
- 分析 Swagger API 定义
- 解析业务规则文档（如有）
- 生成测试用例设计文档 (`testcases.md`)

### 2. Generating（生成阶段）
- 基于测试用例设计生成 Pytest 测试代码
- 包含数据驱动测试支持
- 自动生成测试数据和断言

### 3. Executing + Healing（执行与自愈）
- 执行生成的测试代码
- **语法错误自愈** - 自动修复代码语法问题
- **逻辑错误分析** - 判断是 Bug 还是脚本问题
- 自动重试直到测试通过

### 4. Finalizing（报告阶段）
- 生成 Pytest HTML 测试报告
- 输出业务分析报告
- 生成 Bug 列表（如发现缺陷）

---

## 项目结构

```
smartTest/
├── src/
│   ├── core/                    # 核心模块
│   │   ├── workflow_engine.py   # 四阶段工作流引擎
│   │   ├── cli_adapter.py       # Claude Code CLI 适配器
│   │   ├── prompt_builder.py    # Prompt 模板构建器
│   │   ├── pytest_runner.py     # Pytest 执行器
│   │   ├── result_judge.py      # 结果判定器（自愈决策）
│   │   ├── dependency_analyzer.py # API 依赖分析器
│   │   ├── load_test_runner.py  # 负载测试运行器
│   │   ├── data_loader.py       # 数据加载器
│   │   ├── input_parser.py      # 输入解析器
│   │   └── prd_parser.py        # PRD 文档解析器
│   ├── models/                  # 数据模型
│   │   └── context.py           # 任务上下文模型
│   ├── templates/               # Prompt 模板
│   │   ├── plan_prompt.txt      # 测试用例设计
│   │   ├── generate_prompt.txt  # 代码生成
│   │   ├── heal_syntax_prompt.txt  # 语法修复
│   │   ├── heal_logic_prompt.txt   # 逻辑分析
│   │   ├── business_plan_prompt.txt # 业务规划
│   │   └── load_test_prompt.txt  # 负载测试
│   └── web/                     # Web 服务
│       ├── app.py               # Flask 应用
│       └── templates/           # 前端模板
├── docs/                        # 项目文档
├── tests/                       # 测试数据文件
├── output/                      # 输出结果目录
├── run_web.py                   # Web 服务启动脚本
├── requirements.txt             # Python 依赖
└── README.md                    # 本文件
```

---

## 输出结构

每次执行会在 `output/` 目录下生成时间戳目录：

```
output/YYYY-MM-DD_HHMMSS/
├── testcases.md              # 测试用例设计文档
├── tests/                    # 生成的 Pytest 文件
│   ├── conftest.py
│   └── test_*.py
├── reports/
│   ├── report.html           # Pytest HTML 报告
│   └── results.xml           # JUnit XML 格式
├── dependency_analysis.json  # API 依赖分析
├── bug_report.json           # Bug 报告（如有）
└── business_report.html      # 业务分析报告
```

---

## 测试模式

### 轻量模式（Light Mode）
仅提供 Swagger 定义，断言失败直接标记为 Bug。

### 完整模式（Full Mode）
提供 Swagger + 业务规则文档，断言失败触发逻辑分析，智能判断是 Bug 还是脚本问题。

---

## 自愈机制

平台内置智能自愈系统，自动处理测试执行中的问题：

| 错误类型 | 自愈策略 |
|---------|---------|
| **语法错误** (SyntaxError, NameError, ImportError) | 自动修复代码 |
| **断言失败** (完整模式) | 逻辑分析判断 Bug 或脚本问题 |
| **连接错误** (ConnectionError) | 环境问题，不自愈 |

---

## 技术栈

- **Python 3.8+**
- **Claude Code CLI** - AI 编排核心
- **Pytest** - 测试执行框架
- **Flask + Flask-SocketIO** - Web 服务
- **Locust** - 负载测试
- **Rich** - 终端美化输出

---

## 文档

- [CLAUDE.md](CLAUDE.md) - Claude Code 开发指南
- [docs/技术选型与业务流程.md](docs/技术选型与业务流程.md) - 技术架构与流程说明
- [docs/用户体验需求.md](docs/用户体验需求.md) - 产品功能需求

---

## License

MIT License

---

## 联系方式

- GitHub: [https://github.com/lvhxg6/smartTest](https://github.com/lvhxg6/smartTest)

---

<div align="center">

**Made with intelligence by Smart Dev Mantis**

</div>
