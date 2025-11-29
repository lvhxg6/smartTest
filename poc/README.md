# CLIAdapter PoC - Claude Code CLI 调用验证

## 概述

本 PoC 验证 Python Driver 与 Claude Code CLI 的通信方案，采用 `subprocess + 非交互模式` 作为主要调用方式。

## 文件结构

```
poc/
├── cli_adapter.py       # 核心适配器实现
├── test_cli_adapter.py  # 验证测试脚本
└── README.md            # 本文档
```

## 核心组件

### 1. CLIAdapter

统一的 CLI 调用适配器，支持：

- **单次调用模式** (`ExecutionMode.SINGLE`): 每次调用独立，无状态
- **会话模式** (`ExecutionMode.SESSION`): 保持上下文，支持多轮对话

```python
from cli_adapter import create_claude_adapter

# 创建适配器
adapter = create_claude_adapter(
    timeout=120,
    working_dir="/path/to/project",
    allowed_tools=["Read", "Write", "Edit", "Bash"]
)

# 执行命令
result = adapter.execute("请生成一个 Python 函数")

print(result.success)      # True/False
print(result.output)       # CLI 输出内容
print(result.exit_code)    # 退出码
```

### 2. ClaudeSession

会话管理器，用于需要多轮交互的场景（如自愈循环）：

```python
from cli_adapter import ClaudeSession, create_claude_adapter

adapter = create_claude_adapter()
session = ClaudeSession(adapter)

# 启动会话
result1 = session.start("请分析这段代码...")

# 继续会话（保持上下文）
result2 = session.continue_session("请修复刚才发现的问题")

# 结束会话
session.end()
```

### 3. CLIResult

执行结果的数据结构：

```python
@dataclass
class CLIResult:
    success: bool                           # 是否成功
    output: Optional[str]                   # 原始输出
    parsed_output: Optional[Dict[str, Any]] # 解析后的 JSON
    error: Optional[str]                    # 错误信息
    exit_code: int                          # 退出码
    execution_time: float                   # 执行时间(秒)
    session_id: Optional[str]               # 会话ID
```

## 快速开始

### 前置条件

1. 安装 Claude Code CLI:
   ```bash
   # 参考官方文档安装
   npm install -g @anthropic/claude-code
   ```

2. 确认 CLI 可用:
   ```bash
   claude --version
   ```

### 运行测试

```bash
cd poc

# 运行所有测试
python test_cli_adapter.py

# 运行指定测试
python test_cli_adapter.py --test-name basic
python test_cli_adapter.py --test-name pytest

# 输出结果到文件
python test_cli_adapter.py --output results.json
```

### 可用测试

| 测试名称 | 说明 |
|---------|------|
| `basic` | 基础命令执行 |
| `read` | 文件读取能力 |
| `write` | 文件写入能力 |
| `codegen` | 代码生成能力 |
| `bash` | Bash 命令执行 |
| `error` | 错误处理 |
| `session` | 会话管理 |
| `pytest` | Pytest 测试生成（核心） |
| `retry` | 重试机制 |
| `complex` | 复杂 Prompt 处理 |

## 架构说明

```
┌─────────────────────────────────────────────────────────────┐
│                    Python Driver                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    CLIAdapter                            ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ││
│  │  │ build_command│  │   execute    │  │ parse_result │  ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘  ││
│  └─────────────────────────────────────────────────────────┘│
│                            │                                 │
│               subprocess.run(["claude", "-p", ...])          │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   Claude Code CLI                            │
│                                                              │
│  接收: Prompt + 工作目录                                      │
│  执行: 代码生成 / 文件操作 / Bash 命令                        │
│  返回: JSON 格式结果                                          │
└─────────────────────────────────────────────────────────────┘
```

## 关键设计决策

### 为什么选择 subprocess 而非 pexpect？

| 考量点 | subprocess | pexpect |
|--------|------------|---------|
| 复杂度 | 低 | 高 |
| 跨平台 | ✅ 全平台 | ⚠️ Linux/Mac |
| 输出解析 | JSON 易解析 | 需处理 ANSI |
| 超时控制 | 简单 | 复杂 |
| 调试难度 | 低 | 高 |

### 非交互模式的优势

```bash
# Claude Code CLI 支持非交互模式
claude -p "your prompt" --output-format json
```

- 每次调用干净，无状态残留
- JSON 输出结构化，易于程序处理
- 超时控制简单（subprocess timeout 参数）
- 错误处理清晰（通过 exit code 判断）

## 下一步计划

1. **验证会话恢复机制**: 测试 `--continue` 参数的实际行为
2. **扩展 Codex CLI 支持**: 实现 `CodexAdapter`
3. **集成到主流程**: 与 PromptBuilder、ResultParser 整合
4. **性能优化**: 连接池、并发调用

## 常见问题

### Q: Claude Code CLI 未安装怎么办？

```bash
# 安装 Node.js (如果没有)
brew install node  # macOS
# 或 apt install nodejs  # Ubuntu

# 安装 Claude Code CLI
npm install -g @anthropic/claude-code

# 验证安装
claude --version
```

### Q: 执行超时怎么处理？

调整 `timeout` 参数：

```python
adapter = create_claude_adapter(timeout=600)  # 10分钟
```

### Q: 如何查看详细日志？

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```
