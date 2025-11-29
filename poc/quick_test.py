#!/usr/bin/env python3
"""快速验证脚本"""

import subprocess
import json
import sys

def test_direct_call():
    """直接调用 Claude CLI"""
    print("测试 1: 直接 subprocess 调用")
    print("-" * 40)

    cmd = [
        "claude", "-p",
        "--output-format", "json",
        "回复两个字: 成功"
    ]

    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        print(f"Return code: {result.returncode}")

        if result.stdout:
            data = json.loads(result.stdout)
            print(f"Success: {not data.get('is_error', False)}")
            print(f"Result: {data.get('result', 'N/A')}")
            print(f"Session ID: {data.get('session_id', 'N/A')}")
            print(f"Cost: ${data.get('total_cost_usd', 0):.4f}")

        if result.stderr:
            print(f"Stderr: {result.stderr[:200]}")

    except subprocess.TimeoutExpired:
        print("ERROR: Timeout")
    except Exception as e:
        print(f"ERROR: {e}")

def test_adapter():
    """测试 CLIAdapter"""
    print("\n测试 2: CLIAdapter 调用")
    print("-" * 40)

    from cli_adapter import create_claude_adapter

    adapter = create_claude_adapter(timeout=60)
    result = adapter.execute("回复: 测试通过")

    print(f"Success: {result.success}")
    print(f"Output: {result.output}")
    print(f"Session ID: {result.session_id}")
    print(f"Time: {result.execution_time:.2f}s")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "adapter":
        test_adapter()
    else:
        test_direct_call()
