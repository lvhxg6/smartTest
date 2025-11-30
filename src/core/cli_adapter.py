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
import tempfile
import os
import select
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
    timeout: int = 1200             # 默认 20 分钟 (复杂任务需要足够时间)
    working_dir: Optional[str] = None
    allowed_tools: List[str] = field(default_factory=lambda: [
        "Read", "Write", "Edit", "Bash", "Glob", "Grep"
    ])
    output_format: str = "stream-json"  # 流式输出，支持实时进度
    max_retries: int = 3
    retry_delay: float = 2.0
    # 日志回调 (用于 Web UI 实时输出)
    on_output: Optional[Callable[[str], None]] = None
    # Todo 更新回调 (用于 Web UI 展示任务进度)
    on_todo_update: Optional[Callable[[List[Dict[str, Any]]], None]] = None
    # 取消事件（由上层注入），用于中断长时间的 CLI 调用
    cancel_event: Optional[Any] = None


class CLIAdapter:
    """Claude Code CLI 适配器

    负责调用 Claude Code CLI 并解析结果。
    支持单次调用和会话模式。
    """

    def __init__(self, config: Optional[CLIConfig] = None):
        self.config = config or CLIConfig()
        self.session_id: Optional[str] = None
        # 追踪上一次 todos 状态，用于检测变化
        self._last_todos: List[Dict[str, Any]] = []
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

    def build_command(self, mode: ExecutionMode) -> List[str]:
        """构建 Claude Code CLI 命令

        命令格式：
        echo "prompt" | claude -p --output-format json --dangerously-skip-permissions --allowedTools Tool1,Tool2 [--resume sessionId]

        注意：Prompt 通过 stdin 传递，避免命令行参数过长
        """
        cmd = ["claude"]

        # 非交互模式 (从 stdin 读取)
        cmd.append("-p")

        # 输出格式
        cmd.extend(["--output-format", self.config.output_format])

        # stream-json 格式需要 --verbose
        if self.config.output_format == "stream-json":
            cmd.append("--verbose")

        # 跳过权限确认 (非交互模式必需)
        cmd.append("--dangerously-skip-permissions")

        # 允许的工具
        if self.config.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(self.config.allowed_tools)])

        # 会话模式
        if mode == ExecutionMode.SESSION and self.session_id:
            cmd.extend(["--resume", self.session_id])

        # Prompt 通过 stdin 传递，不再作为命令行参数

        return cmd

    def _emit_chunk(self, content: str) -> None:
        """将模型输出的片段写入回调"""
        if not self.config.on_output:
            return

        if not content:
            return

        cleaned = str(content).strip()
        if not cleaned:
            return

        # 检查是否是多行内容（如列表、优先级分布等）
        if "\n" in cleaned:
            lines = cleaned.split("\n")
            for line in lines:
                line = line.strip()
                if line:
                    # 单行最大 500 字符
                    if len(line) > 500:
                        line = line[:500] + "..."
                    self.config.on_output(f"→ {line}")
        else:
            # 单行内容，限制 500 字符
            if len(cleaned) > 500:
                cleaned = cleaned[:500] + "..."
            self.config.on_output(f"→ {cleaned}")

    def _extract_text(self, event: Dict[str, Any]) -> str:
        """从 stream-json 事件中提取文本内容"""
        # content_block_delta / message_delta
        delta = event.get("delta", {})
        if isinstance(delta, dict):
            if isinstance(delta.get("text"), str):
                return delta["text"]
            if delta.get("type") == "text_delta" and isinstance(delta.get("text"), str):
                return delta["text"]
            inner = delta.get("text_delta")
            if isinstance(inner, dict) and isinstance(inner.get("text"), str):
                return inner["text"]

        # content_block_start / content_block
        content_block = event.get("content_block")
        if isinstance(content_block, dict) and isinstance(content_block.get("text"), str):
            return content_block["text"]

        # message.* 结构
        message = event.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                texts = [
                    c.get("text")
                    for c in content
                    if isinstance(c, dict) and isinstance(c.get("text"), str)
                ]
                if texts:
                    return " ".join(texts)

        # 兜底直接取 text 字段
        if isinstance(event.get("text"), str):
            return event["text"]

        return ""

    def _format_tool_input(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """格式化工具输入参数，生成简洁的描述"""
        if not isinstance(tool_input, dict):
            return ""

        # 根据不同工具类型提取关键信息
        if tool_name == "Write":
            file_path = tool_input.get("file_path", "")
            file_name = file_path.split("/")[-1] if "/" in file_path else file_path
            return f"写入 {file_name}"
        elif tool_name == "Read":
            file_path = tool_input.get("file_path", "")
            file_name = file_path.split("/")[-1] if "/" in file_path else file_path
            return f"读取 {file_name}"
        elif tool_name == "Edit":
            file_path = tool_input.get("file_path", "")
            file_name = file_path.split("/")[-1] if "/" in file_path else file_path
            return f"编辑 {file_name}"
        elif tool_name == "Bash":
            command = tool_input.get("command", "")
            # 截取命令前 50 字符
            cmd_preview = command[:50] + "..." if len(command) > 50 else command
            return f"执行: {cmd_preview}"
        elif tool_name == "Glob":
            pattern = tool_input.get("pattern", "")
            return f"搜索: {pattern}"
        elif tool_name == "Grep":
            pattern = tool_input.get("pattern", "")
            return f"搜索: {pattern}"
        elif tool_name == "TodoWrite":
            todos = tool_input.get("todos", [])
            if todos:
                total = len(todos)

                # 更新缓存
                self._last_todos = [dict(t) if isinstance(t, dict) else {} for t in todos]

                # 找到当前正在进行的任务
                current_idx = 0
                current_todo = None
                for i, t in enumerate(todos):
                    if isinstance(t, dict) and t.get("status") == "in_progress":
                        current_idx = i + 1  # 1-based index
                        current_todo = t
                        break
                if current_todo is None:
                    # 没有 in_progress，显示第一个未完成的
                    for i, t in enumerate(todos):
                        if isinstance(t, dict) and t.get("status") != "completed":
                            current_idx = i + 1
                            current_todo = t
                            break
                if current_todo is None and todos:
                    # 所有任务都完成，显示最后一个
                    current_idx = total
                    current_todo = todos[-1] if isinstance(todos[-1], dict) else {}

                # 只显示当前任务
                if current_todo:
                    content = current_todo.get("content", "") or current_todo.get("activeForm", "")
                    preview = content[:25] + "..." if len(content) > 25 else content
                    status = current_todo.get("status", "pending")
                    prefix = "✓ " if status == "completed" else ""
                    return f"{prefix}{current_idx}/{total}: {preview}"
            return ""
        elif "file_path" in tool_input:
            file_path = tool_input["file_path"]
            file_name = file_path.split("/")[-1] if "/" in file_path else file_path
            return file_name

        return ""

    def _handle_stream_event(self, event: Dict[str, Any]) -> None:
        """处理流式事件，只回调关键节点

        stream-json 格式:
        - system: 初始化信息
        - assistant: Claude 回复，message.content[] 包含 tool_use 或 text
        - user: 工具执行结果 (tool_use_result)
        - result: 最终结果
        """
        if not self.config.on_output:
            return

        event_type = event.get("type", "")

        if event_type == "system":
            # 系统初始化事件 - 显示会话信息
            subtype = event.get("subtype", "")
            if subtype == "init":
                model = event.get("model", "unknown")
                session_id = event.get("session_id", "")[:8] if event.get("session_id") else ""
                tools_count = len(event.get("tools", []))
                self.config.on_output(f"→ 会话初始化: 模型={model}, 工具数={tools_count}")
            else:
                self.config.on_output(f"→ 系统事件: {subtype or 'init'}")

        elif event_type == "assistant":
            # Claude 的回复
            message = event.get("message", {})
            if not isinstance(message, dict):
                message = {}
            content_list = message.get("content", [])

            if isinstance(content_list, list):
                for content_item in content_list:
                    if not isinstance(content_item, dict):
                        continue
                    item_type = content_item.get("type", "")

                    if item_type == "tool_use":
                        tool_name = content_item.get("name", "unknown")
                        tool_input = content_item.get("input", {})
                        # 特殊处理 TodoWrite：推送 todo 列表（不输出冗长 raw）
                        if tool_name == "TodoWrite":
                            if self.config.on_todo_update and isinstance(tool_input, dict):
                                todos = tool_input.get("todos", [])
                                if todos:
                                    self.config.on_todo_update(todos)
                        # 获取工具输入的详细描述
                        detail = self._format_tool_input(tool_name, tool_input)
                        if detail:
                            self.config.on_output(f"→ 工具调用: {tool_name} - {detail}")
                        else:
                            self.config.on_output(f"→ 工具调用: {tool_name}")
                    elif item_type == "text":
                        text = content_item.get("text", "")
                        if text:
                            self._emit_chunk(text)
            else:
                text = self._extract_text(event)
                if text:
                    self._emit_chunk(text)

        elif event_type in {"message_start", "content_block_start"} or str(event_type).endswith("_start"):
            # 新版 stream-json 开头事件
            text = self._extract_text(event)
            if text:
                self._emit_chunk(text)

        elif event_type in {"content_block_delta", "message_delta", "delta"} or str(event_type).endswith("delta"):
            # 新版增量事件，直接透出
            text = self._extract_text(event)
            if text:
                self._emit_chunk(text)

        elif event_type == "user":
            # 工具执行结果
            tool_result = event.get("tool_use_result", {})
            if tool_result and isinstance(tool_result, dict):
                result_type = tool_result.get("type", "")
                file_path = tool_result.get("filePath", "")
                file_name = file_path.split("/")[-1] if file_path and "/" in file_path else file_path
                if result_type == "create":
                    self.config.on_output(f"→ 文件创建成功: {file_name}")
                elif result_type == "edit":
                    self.config.on_output(f"→ 文件编辑成功: {file_name}")
                elif result_type:
                    self.config.on_output(f"→ 工具执行完成: {result_type}")
            else:
                # 可能是其他类型的 user 消息（如工具返回的文本结果）
                message = event.get("message", {})
                if isinstance(message, dict):
                    content = message.get("content", [])
                else:
                    content = []
                if isinstance(content, list) and content:
                    first = content[0]
                    if isinstance(first, dict) and first.get("type") == "tool_result":
                        result_content = first.get("content", "")
                        if isinstance(result_content, str) and result_content:
                            preview = result_content[:80] + "..." if len(result_content) > 80 else result_content
                            self.config.on_output(f"→ 工具返回: {preview}")

        elif event_type == "tool_use":
            # 新版独立的 tool_use 事件
            tool_name = event.get("tool", event.get("name", "unknown"))
            self.config.on_output(f"→ 工具调用: {tool_name}")

        elif event_type == "tool_result":
            tool_name = event.get("tool", event.get("name", "unknown"))
            is_error = event.get("is_error", False)
            status = "失败" if is_error else "成功"
            self.config.on_output(f"→ 工具完成: {tool_name} {status}")

        elif event_type == "result":
            # 最终结果
            cost = event.get("total_cost_usd", event.get("cost_usd", 0))
            num_turns = event.get("num_turns", 0)
            duration = event.get("duration_ms", 0) / 1000  # 转换为秒
            self.config.on_output(f"→ 执行完成 (轮次: {num_turns}, 耗时: {duration:.1f}s, 费用: ${cost:.4f})")

        else:
            # 兜底处理未知事件，避免静默导致前端看起来“卡住”
            text = self._extract_text(event)
            if text:
                self._emit_chunk(text)
            else:
                unknown = event_type or "unknown"
                self.config.on_output(f"→ 事件: {unknown}")

    def execute(
        self,
        prompt: str,
        mode: ExecutionMode = ExecutionMode.SINGLE
    ) -> CLIResult:
        """执行 Claude Code CLI (流式输出版本)

        Args:
            prompt: 发送给 Claude 的 Prompt
            mode: 执行模式 (SINGLE/SESSION)

        Returns:
            CLIResult 包含执行结果
        """
        cmd = self.build_command(mode)

        # 重置 todo 追踪状态
        self._last_todos = []

        # 日志只显示命令前缀，不暴露完整 prompt
        logger.info(f"Executing CLI: claude -p ... (mode={mode.value}, prompt_len={len(prompt)})")

        start_time = time.time()
        final_result = None
        all_events = []
        stderr_output = ""
        cancelled = False
        cancel_event = getattr(self.config, "cancel_event", None)

        # 创建临时文件存储 prompt，避免管道缓冲区问题
        prompt_file = None
        try:
            # 写入 prompt 到临时文件
            prompt_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                delete=False,
                encoding='utf-8'
            )
            prompt_file.write(prompt)
            prompt_file.close()

            # 使用 shell 重定向从文件读取
            shell_cmd = f"{' '.join(cmd)} < {prompt_file.name}"
            logger.debug(f"Shell command: claude -p ... < {prompt_file.name}")

            process = subprocess.Popen(
                shell_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.config.working_dir,
                start_new_session=True  # 创建新进程组，防止信号传播导致父进程终止
            )

            # 逐行读取 stream-json 输出（可取消）
            stdout = process.stdout
            buffer = ""
            while True:
                # 检查取消信号
                if cancel_event and getattr(cancel_event, "is_set", lambda: False)():
                    cancelled = True
                    if self.config.on_output:
                        self.config.on_output("→ 任务取消，正在终止 CLI 进程...")
                    try:
                        process.kill()
                    except Exception:
                        pass
                    break

                # 若子进程已退出且缓冲为空，结束循环
                if process.poll() is not None and not buffer:
                    break

                # 使用 select 轮询，避免阻塞
                ready, _, _ = select.select([stdout], [], [], 0.2)
                if not ready:
                    continue

                chunk = stdout.readline()
                if not chunk:
                    continue

                buffer += chunk
                # 按行处理
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                        if isinstance(event, dict):
                            all_events.append(event)
                            # 处理关键节点回调
                            self._handle_stream_event(event)
                            # 保存最终结果
                            if event.get("type") == "result":
                                final_result = event
                        else:
                            logger.debug(f"Ignored non-dict event: {line[:80]}")
                    except json.JSONDecodeError:
                        logger.debug(f"Non-JSON line: {line[:100]}")
                        # 透传原始输出，兼容 CLI 输出格式变化
                        if self.config.on_output:
                            preview = line[:400]
                            self.config.on_output(f"→ CLI: {preview}")

            # 读取 stderr
            stderr_output = process.stderr.read()

            # 若在循环外收到取消信号，再次尝试终止
            if cancel_event and getattr(cancel_event, "is_set", lambda: False)():
                cancelled = True
                if process.poll() is None:
                    try:
                        process.kill()
                    except Exception:
                        pass

            # 等待进程结束，带超时
            try:
                return_code = process.wait(timeout=self.config.timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                raise

            execution_time = time.time() - start_time

            if cancelled:
                if self.config.on_output:
                    self.config.on_output("→ CLI 已终止")
                return CLIResult(
                    success=False,
                    error="任务已取消",
                    exit_code=-2,
                    execution_time=execution_time,
                    session_id=self.session_id
                )

            # 解析最终结果
            if final_result:
                actual_result = final_result.get("result", "")
                is_error = final_result.get("is_error", False)
                session_id = final_result.get("session_id")
                cost_usd = final_result.get("total_cost_usd", final_result.get("cost_usd", 0.0))

                if session_id:
                    self.session_id = session_id

                # 提取更有用的错误信息
                error_msg = None
                if is_error:
                    error_msg = actual_result or final_result.get("error") or stderr_output
                    # 兜底使用返回码描述
                    if not error_msg and return_code != 0:
                        error_msg = f"CLI exited with code {return_code}"

                return CLIResult(
                    success=return_code == 0 and not is_error,
                    output=actual_result,
                    parsed_output=final_result,
                    error=error_msg if error_msg else (stderr_output if return_code != 0 else None),
                    exit_code=return_code,
                    execution_time=execution_time,
                    session_id=self.session_id,
                    cost_usd=cost_usd
                )
            else:
                # 没有收到 result 事件
                return CLIResult(
                    success=False,
                    output="",
                    error=stderr_output or "No result received from CLI",
                    exit_code=return_code,
                    execution_time=execution_time
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
        finally:
            # 清理临时文件
            if prompt_file and os.path.exists(prompt_file.name):
                try:
                    os.unlink(prompt_file.name)
                except Exception:
                    pass

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
    timeout: int = 1200,
    working_dir: Optional[str] = None,
    allowed_tools: Optional[List[str]] = None,
    on_output: Optional[Callable[[str], None]] = None
) -> CLIAdapter:
    """创建 CLI 适配器的便捷函数

    Args:
        timeout: 超时时间 (秒)，默认 20 分钟
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
