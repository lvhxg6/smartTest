"""
CLIAdapter - Claude Code CLI 调用适配器

封装 Claude Code CLI 的调用，支持:
- 单次调用模式
- 会话模式 (保持上下文用于自愈循环)
- 自动重试机制
"""

import subprocess
import json
import time
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from enum import Enum

from ..models import CLIResult

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """执行模式"""
    SINGLE = "single"      # 单次调用，无状态
    SESSION = "session"    # 会话模式，保持上下文


@dataclass
class CLIConfig:
    """CLI 配置"""
    timeout: int = 180              # 默认 180s (技术文档规定)
    working_dir: Optional[str] = None
    allowed_tools: List[str] = field(default_factory=lambda: [
        "Read", "Write", "Edit", "Bash", "Glob", "Grep"
    ])
    output_format: str = "json"
    max_retries: int = 3
    retry_delay: float = 2.0
    # 日志回调 (用于 Web UI 实时输出)
    on_output: Optional[Callable[[str], None]] = None


class CLIAdapter:
    """Claude Code CLI 适配器

    负责调用 Claude Code CLI 并解析结果。
    支持单次调用和会话模式。
    """

    def __init__(self, config: Optional[CLIConfig] = None):
        self.config = config or CLIConfig()
        self.session_id: Optional[str] = None
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
            logger.warning("Claude Code CLI version check timed out")

    def build_command(self, prompt: str, mode: ExecutionMode) -> List[str]:
        """构建 Claude Code CLI 命令

        命令格式：
        claude -p --output-format json --allowedTools Tool1,Tool2 [--resume sessionId] "prompt"
        """
        cmd = ["claude"]

        # 非交互模式
        cmd.append("-p")

        # 输出格式
        cmd.extend(["--output-format", self.config.output_format])

        # 允许的工具
        if self.config.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(self.config.allowed_tools)])

        # 会话模式
        if mode == ExecutionMode.SESSION and self.session_id:
            cmd.extend(["--resume", self.session_id])

        # Prompt 作为最后的位置参数
        cmd.append(prompt)

        return cmd

    def execute(
        self,
        prompt: str,
        mode: ExecutionMode = ExecutionMode.SINGLE
    ) -> CLIResult:
        """执行 Claude Code CLI

        Args:
            prompt: 发送给 Claude 的 Prompt
            mode: 执行模式 (SINGLE/SESSION)

        Returns:
            CLIResult 包含执行结果
        """
        cmd = self.build_command(prompt, mode)

        # 日志只显示命令前缀，不暴露完整 prompt
        logger.info(f"Executing CLI: claude -p ... (mode={mode.value})")

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
            cost_usd = 0.0

            if result.stdout and self.config.output_format == "json":
                try:
                    parsed_output = json.loads(result.stdout)
                    # Claude CLI JSON 格式:
                    # {"type":"result", "result":"...", "session_id":"...", "cost_usd":...}
                    actual_result = parsed_output.get("result", result.stdout)
                    is_error = parsed_output.get("is_error", False)
                    session_id = parsed_output.get("session_id")
                    cost_usd = parsed_output.get("cost_usd", 0.0)

                    if session_id:
                        self.session_id = session_id

                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON output, using raw text")

            # 回调输出
            if self.config.on_output and actual_result:
                self.config.on_output(actual_result)

            return CLIResult(
                success=result.returncode == 0 and not is_error,
                output=actual_result,
                parsed_output=parsed_output,
                error=result.stderr if result.returncode != 0 else None,
                exit_code=result.returncode,
                execution_time=execution_time,
                session_id=self.session_id,
                cost_usd=cost_usd
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

    def execute_with_retry(
        self,
        prompt: str,
        mode: ExecutionMode = ExecutionMode.SINGLE
    ) -> CLIResult:
        """带重试机制的执行

        失败时自动重试，直到成功或达到最大重试次数
        """
        last_result = None

        for attempt in range(self.config.max_retries):
            result = self.execute(prompt, mode)

            if result.success:
                return result

            last_result = result

            if attempt < self.config.max_retries - 1:
                logger.warning(
                    f"Attempt {attempt + 1}/{self.config.max_retries} failed, "
                    f"retrying in {self.config.retry_delay}s..."
                )
                time.sleep(self.config.retry_delay)

        logger.error(f"All {self.config.max_retries} attempts failed")
        return last_result

    def reset_session(self) -> None:
        """重置会话状态"""
        self.session_id = None
        logger.info("Session reset")


class CLISession:
    """CLI 会话管理器

    用于需要多轮交互的场景，如自愈循环。
    保持上下文，支持连续对话。

    使用方式:
        session = CLISession(adapter)
        result = session.start("生成测试代码...")

        # 发生错误时继续对话修复
        result = session.send("修复上面的错误...")

        session.end()
    """

    def __init__(self, adapter: CLIAdapter):
        self.adapter = adapter
        self.history: List[Dict[str, Any]] = []
        self.is_active = False
        self.total_cost: float = 0.0

    def start(self, initial_prompt: str) -> CLIResult:
        """启动新会话"""
        logger.info("Starting new CLI session...")

        # 重置之前的会话
        self.adapter.reset_session()
        self.history = []
        self.total_cost = 0.0

        result = self.adapter.execute(initial_prompt, ExecutionMode.SINGLE)

        if result.success:
            self.is_active = True

        self._record_turn("user", initial_prompt, result)
        return result

    def send(self, message: str) -> CLIResult:
        """发送后续消息 (继续当前会话)"""
        if not self.is_active:
            logger.warning("No active session, starting new one...")
            return self.start(message)

        logger.info("Continuing session...")
        result = self.adapter.execute(message, ExecutionMode.SESSION)

        self._record_turn("user", message, result)
        return result

    def _record_turn(self, role: str, content: str, result: CLIResult) -> None:
        """记录对话轮次"""
        self.history.append({
            "role": role,
            "content": content,
            "result": result.to_dict(),
            "timestamp": time.time()
        })
        self.total_cost += result.cost_usd

    def end(self) -> None:
        """结束会话"""
        logger.info(f"Ending session. Total cost: ${self.total_cost:.4f}")
        self.is_active = False
        self.adapter.reset_session()

    def get_history(self) -> List[Dict[str, Any]]:
        """获取会话历史"""
        return self.history.copy()

    @property
    def session_id(self) -> Optional[str]:
        """获取当前会话 ID"""
        return self.adapter.session_id


# 便捷函数
def create_adapter(
    timeout: int = 180,
    working_dir: Optional[str] = None,
    allowed_tools: Optional[List[str]] = None,
    on_output: Optional[Callable[[str], None]] = None
) -> CLIAdapter:
    """创建 CLI 适配器的便捷函数

    Args:
        timeout: 超时时间 (秒)
        working_dir: 工作目录
        allowed_tools: 允许的工具列表
        on_output: 输出回调函数 (用于实时日志)

    Returns:
        配置好的 CLIAdapter 实例
    """
    config = CLIConfig(
        timeout=timeout,
        working_dir=working_dir,
        allowed_tools=allowed_tools or ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        on_output=on_output
    )
    return CLIAdapter(config)
