"""
CLIAdapter - Claude Code CLI / Codex CLI 统一调用适配器

该模块提供对 Claude Code CLI 和 Codex CLI 的统一封装，
支持单次调用和会话模式两种方式。

Author: Nexus AI Test Agent Team
Date: 2025-11-29
"""

import subprocess
import json
import os
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CLIType(Enum):
    """支持的 CLI 类型"""
    CLAUDE_CODE = "claude"
    CODEX = "codex"


class ExecutionMode(Enum):
    """执行模式"""
    SINGLE = "single"      # 单次调用，无状态
    SESSION = "session"    # 会话模式，保持上下文


@dataclass
class CLIResult:
    """CLI 执行结果"""
    success: bool
    output: Optional[str] = None
    parsed_output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    exit_code: int = 0
    execution_time: float = 0.0
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "parsed_output": self.parsed_output,
            "error": self.error,
            "exit_code": self.exit_code,
            "execution_time": self.execution_time,
            "session_id": self.session_id
        }


@dataclass
class CLIConfig:
    """CLI 配置"""
    cli_type: CLIType = CLIType.CLAUDE_CODE
    timeout: int = 300  # 默认5分钟超时
    working_dir: Optional[str] = None
    allowed_tools: List[str] = field(default_factory=lambda: ["Read", "Write", "Edit", "Bash"])
    output_format: str = "json"
    max_retries: int = 3
    retry_delay: float = 1.0


class BaseCLIAdapter(ABC):
    """CLI 适配器基类"""

    def __init__(self, config: CLIConfig):
        self.config = config
        self.session_id: Optional[str] = None

    @abstractmethod
    def execute(self, prompt: str, mode: ExecutionMode = ExecutionMode.SINGLE) -> CLIResult:
        """执行 CLI 命令"""
        pass

    @abstractmethod
    def build_command(self, prompt: str, mode: ExecutionMode) -> List[str]:
        """构建命令行参数"""
        pass


class ClaudeCodeAdapter(BaseCLIAdapter):
    """Claude Code CLI 适配器"""

    def __init__(self, config: Optional[CLIConfig] = None):
        super().__init__(config or CLIConfig())
        self._validate_cli_available()

    def _validate_cli_available(self) -> None:
        """验证 CLI 是否可用"""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"Claude Code CLI available: {result.stdout.strip()}")
            else:
                logger.warning(f"Claude Code CLI check failed: {result.stderr}")
        except FileNotFoundError:
            logger.error("Claude Code CLI not found. Please install it first.")
            raise RuntimeError("Claude Code CLI not installed")
        except subprocess.TimeoutExpired:
            logger.error("Claude Code CLI version check timed out")

    def build_command(self, prompt: str, mode: ExecutionMode) -> List[str]:
        """构建 Claude Code CLI 命令

        Claude CLI 参数格式：
        claude [options] [prompt]

        关键参数：
        - -p, --print: 非交互模式
        - --output-format: 输出格式 (text/json/stream-json)
        - --allowedTools: 允许的工具列表
        - -c, --continue: 继续最近对话
        - -r, --resume [sessionId]: 恢复指定会话
        """
        cmd = ["claude"]

        # 非交互模式
        cmd.append("-p")

        # 输出格式
        if self.config.output_format:
            cmd.extend(["--output-format", self.config.output_format])

        # 允许的工具
        if self.config.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(self.config.allowed_tools)])

        # 会话模式
        if mode == ExecutionMode.SESSION:
            if self.session_id:
                cmd.extend(["--resume", self.session_id])
            else:
                cmd.append("--continue")

        # Prompt 作为最后的位置参数
        cmd.append(prompt)

        return cmd

    def execute(self, prompt: str, mode: ExecutionMode = ExecutionMode.SINGLE) -> CLIResult:
        """执行 Claude Code CLI"""
        cmd = self.build_command(prompt, mode)
        logger.info(f"Executing command: {' '.join(cmd[:3])}...")  # 只打印前几个参数

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                cwd=self.config.working_dir
            )

            execution_time = time.time() - start_time

            # 解析输出
            parsed_output = None
            actual_result = result.stdout
            is_error = False
            session_id = None

            if result.stdout and self.config.output_format == "json":
                try:
                    parsed_output = json.loads(result.stdout)
                    # 从 JSON 输出中提取关键信息
                    # Claude CLI JSON 格式: {"type":"result", "result":"...", "session_id":"...", ...}
                    actual_result = parsed_output.get("result", result.stdout)
                    is_error = parsed_output.get("is_error", False)
                    session_id = parsed_output.get("session_id")
                    if session_id:
                        self.session_id = session_id
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON output, using raw text")

            return CLIResult(
                success=result.returncode == 0 and not is_error,
                output=actual_result,
                parsed_output=parsed_output,
                error=result.stderr if result.returncode != 0 else None,
                exit_code=result.returncode,
                execution_time=execution_time,
                session_id=self.session_id
            )

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            logger.error(f"Command timed out after {self.config.timeout}s")
            return CLIResult(
                success=False,
                error=f"Timeout after {self.config.timeout} seconds",
                exit_code=-1,
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Command execution failed: {str(e)}")
            return CLIResult(
                success=False,
                error=str(e),
                exit_code=-1,
                execution_time=execution_time
            )

    def execute_with_retry(self, prompt: str, mode: ExecutionMode = ExecutionMode.SINGLE) -> CLIResult:
        """带重试机制的执行"""
        last_result = None

        for attempt in range(self.config.max_retries):
            result = self.execute(prompt, mode)

            if result.success:
                return result

            last_result = result
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {self.config.retry_delay}s...")
            time.sleep(self.config.retry_delay)

        logger.error(f"All {self.config.max_retries} attempts failed")
        return last_result


class ClaudeSession:
    """Claude Code 会话管理器

    用于需要多轮交互的场景，如自愈循环。
    保持上下文，支持连续对话。
    """

    def __init__(self, adapter: ClaudeCodeAdapter):
        self.adapter = adapter
        self.history: List[Dict[str, Any]] = []
        self.is_active = False

    def start(self, initial_prompt: str) -> CLIResult:
        """启动新会话"""
        logger.info("Starting new Claude session...")
        result = self.adapter.execute(initial_prompt, ExecutionMode.SINGLE)

        if result.success:
            self.is_active = True
            self.history.append({
                "role": "user",
                "content": initial_prompt,
                "result": result.to_dict()
            })

        return result

    def continue_session(self, follow_up: str) -> CLIResult:
        """继续当前会话"""
        if not self.is_active:
            logger.warning("No active session, starting new one...")
            return self.start(follow_up)

        logger.info("Continuing session...")
        result = self.adapter.execute(follow_up, ExecutionMode.SESSION)

        self.history.append({
            "role": "user",
            "content": follow_up,
            "result": result.to_dict()
        })

        return result

    def end(self) -> None:
        """结束会话"""
        logger.info("Ending session...")
        self.is_active = False
        self.adapter.session_id = None

    def get_history(self) -> List[Dict[str, Any]]:
        """获取会话历史"""
        return self.history.copy()


class CLIAdapterFactory:
    """CLI 适配器工厂"""

    @staticmethod
    def create(cli_type: CLIType, config: Optional[CLIConfig] = None) -> BaseCLIAdapter:
        """创建 CLI 适配器实例"""
        if config is None:
            config = CLIConfig(cli_type=cli_type)

        if cli_type == CLIType.CLAUDE_CODE:
            return ClaudeCodeAdapter(config)
        elif cli_type == CLIType.CODEX:
            # TODO: 实现 Codex CLI 适配器
            raise NotImplementedError("Codex CLI adapter not implemented yet")
        else:
            raise ValueError(f"Unknown CLI type: {cli_type}")


# 便捷函数
def create_claude_adapter(
    timeout: int = 300,
    working_dir: Optional[str] = None,
    allowed_tools: Optional[List[str]] = None
) -> ClaudeCodeAdapter:
    """创建 Claude Code 适配器的便捷函数"""
    config = CLIConfig(
        cli_type=CLIType.CLAUDE_CODE,
        timeout=timeout,
        working_dir=working_dir,
        allowed_tools=allowed_tools or ["Read", "Write", "Edit", "Bash"]
    )
    return ClaudeCodeAdapter(config)


if __name__ == "__main__":
    # 简单测试
    print("Testing CLIAdapter module...")

    try:
        adapter = create_claude_adapter(timeout=60)
        print("✅ Claude Code adapter created successfully")

        # 测试简单命令
        result = adapter.execute("echo 'Hello from Claude Code CLI test'")
        print(f"✅ Execution completed: success={result.success}, time={result.execution_time:.2f}s")

        if result.output:
            print(f"   Output preview: {result.output[:200]}...")

    except Exception as e:
        print(f"❌ Test failed: {e}")
