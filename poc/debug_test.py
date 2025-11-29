#!/usr/bin/env python3
"""调试测试脚本 - 找出 CLIAdapter 的问题"""

import subprocess
import json
import sys
import os

def test_basic_subprocess():
    """基础 subprocess 测试"""
    print("=" * 50)
    print("测试 1: 基础 subprocess.run")
    print("=" * 50)

    cmd = ["claude", "-p", "--output-format", "json", "回复: OK"]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60
    )

    print(f"Return code: {result.returncode}")
    print(f"Stdout length: {len(result.stdout)}")
    print(f"Stderr length: {len(result.stderr)}")

    if result.returncode == 0:
        data = json.loads(result.stdout)
        print(f"Result: {data.get('result')}")
        print("✅ 基础测试通过")
        return True
    else:
        print(f"❌ 基础测试失败")
        return False


def test_with_cwd():
    """带 cwd 参数的测试"""
    print("\n" + "=" * 50)
    print("测试 2: 带 cwd 参数")
    print("=" * 50)

    cmd = ["claude", "-p", "--output-format", "json", "回复: OK"]
    cwd = os.getcwd()

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
        cwd=cwd
    )

    print(f"CWD: {cwd}")
    print(f"Return code: {result.returncode}")

    if result.returncode == 0:
        print("✅ CWD 测试通过")
        return True
    else:
        print(f"❌ CWD 测试失败: {result.stderr[:200]}")
        return False


def test_with_allowed_tools():
    """带 allowedTools 参数的测试"""
    print("\n" + "=" * 50)
    print("测试 3: 带 --allowedTools 参数")
    print("=" * 50)

    cmd = [
        "claude", "-p",
        "--output-format", "json",
        "--allowedTools", "Read,Write,Edit,Bash",
        "回复: OK"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60
    )

    print(f"Return code: {result.returncode}")

    if result.returncode == 0:
        print("✅ allowedTools 测试通过")
        return True
    else:
        print(f"❌ allowedTools 测试失败: {result.stderr[:200]}")
        return False


def test_cli_adapter_step_by_step():
    """逐步测试 CLIAdapter"""
    print("\n" + "=" * 50)
    print("测试 4: CLIAdapter 逐步测试")
    print("=" * 50)

    # 添加当前目录到 path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from cli_adapter import ClaudeCodeAdapter, CLIConfig, CLIType

    print("Step 1: 创建配置...")
    config = CLIConfig(
        cli_type=CLIType.CLAUDE_CODE,
        timeout=60,
        working_dir=None,  # 不设置 working_dir
        allowed_tools=[],  # 不限制 tools
        output_format="json"
    )
    print(f"  Config: timeout={config.timeout}, format={config.output_format}")

    print("Step 2: 创建适配器...")
    adapter = ClaudeCodeAdapter(config)
    print("  Adapter created")

    print("Step 3: 构建命令...")
    from cli_adapter import ExecutionMode
    cmd = adapter.build_command("回复: OK", ExecutionMode.SINGLE)
    print(f"  Command: {cmd}")

    print("Step 4: 执行命令...")
    result = adapter.execute("回复: OK")
    print(f"  Success: {result.success}")
    print(f"  Exit code: {result.exit_code}")
    print(f"  Output: {result.output}")
    print(f"  Error: {result.error}")

    if result.success:
        print("✅ CLIAdapter 测试通过")
        return True
    else:
        print("❌ CLIAdapter 测试失败")
        return False


if __name__ == "__main__":
    results = []

    results.append(("基础 subprocess", test_basic_subprocess()))
    results.append(("带 cwd 参数", test_with_cwd()))
    results.append(("带 allowedTools", test_with_allowed_tools()))
    results.append(("CLIAdapter", test_cli_adapter_step_by_step()))

    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
