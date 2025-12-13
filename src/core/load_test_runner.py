"""
LoadTestRunner - 压力测试执行器

负责:
- 调用 LLM 生成 locustfile.py
- 执行 Locust 压测 (headless 模式)
- 实时收集进度
- 解析结果
"""

import subprocess
import json
import csv
import time
import signal
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List

from .cli_adapter import CLIAdapter, CLIConfig, ExecutionMode
from .prompt_builder import PromptBuilder
from ..models import (
    LoadTestConfig, LoadTestResult, LoadTestProgress, LoadTestStatus
)

logger = logging.getLogger(__name__)


class LoadTestRunner:
    """压力测试执行器

    使用 Locust 执行 API 压力测试。
    """

    def __init__(
        self,
        config: LoadTestConfig,
        base_url: str,
        auth_token: Optional[str] = None,
        on_progress: Optional[Callable[[LoadTestProgress], None]] = None,
        on_log: Optional[Callable[[str], None]] = None,
        cancel_event: Optional[Any] = None
    ):
        self.config = config
        self.base_url = base_url
        self.auth_token = auth_token
        self.on_progress = on_progress
        self.on_log = on_log
        self.cancel_event = cancel_event
        self._process: Optional[subprocess.Popen] = None

    def run(self, output_dir: str, swagger_content: str) -> LoadTestResult:
        """执行压力测试

        Args:
            output_dir: 输出目录 (应包含功能测试结果)
            swagger_content: Swagger JSON 内容

        Returns:
            LoadTestResult 压测结果
        """
        output_path = Path(output_dir)
        load_test_dir = output_path / "load_test"
        load_test_dir.mkdir(parents=True, exist_ok=True)

        result = LoadTestResult(status=LoadTestStatus.PENDING)
        result.start_time = datetime.now().isoformat()

        try:
            # 步骤 1: 生成 locustfile.py
            self._log("info", "正在生成压测脚本...")
            result.status = LoadTestStatus.GENERATING
            locustfile = self._generate_locustfile(
                output_dir, load_test_dir, swagger_content
            )
            result.locustfile_path = str(locustfile)

            if not locustfile.exists():
                raise RuntimeError("压测脚本生成失败")

            # 检查是否取消
            if self._is_cancelled():
                result.status = LoadTestStatus.STOPPED
                return result

            # 步骤 2: 执行 Locust
            self._log("info", f"正在执行压测 ({self.config.concurrent_users} 并发, {self.config.duration} 秒)...")
            result.status = LoadTestStatus.RUNNING
            self._run_locust(locustfile, load_test_dir)

            # 检查是否取消
            if self._is_cancelled():
                result.status = LoadTestStatus.STOPPED
                return result

            # 步骤 3: 解析结果
            self._log("info", "正在解析压测结果...")
            result = self._parse_results(load_test_dir, result)
            result.status = LoadTestStatus.COMPLETED
            result.end_time = datetime.now().isoformat()

            self._log("info", f"压测完成: {result.total_requests} 请求, QPS={result.requests_per_second:.2f}, 错误率={result.error_rate}%")

        except Exception as e:
            logger.error(f"压测失败: {e}")
            result.status = LoadTestStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now().isoformat()

        return result

    def stop(self) -> None:
        """停止压测"""
        if self._process and self._process.poll() is None:
            self._log("info", "正在停止压测...")
            self._process.send_signal(signal.SIGINT)
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()

    def _is_cancelled(self) -> bool:
        """检查是否被取消"""
        if self.cancel_event and hasattr(self.cancel_event, 'is_set'):
            return self.cancel_event.is_set()
        return False

    def _log(self, level: str, message: str) -> None:
        """输出日志"""
        if self.on_log:
            self.on_log(message)
        logger.info(message)

    def _generate_locustfile(
        self,
        output_dir: str,
        load_test_dir: Path,
        swagger_content: str
    ) -> Path:
        """生成 locustfile.py

        使用 Claude CLI 生成智能压测脚本
        """
        locustfile_path = load_test_dir / "locustfile.py"

        # 读取探测数据（如果存在）
        explored_data = {}
        explored_data_path = Path(output_dir) / "explored_data.json"
        if explored_data_path.exists():
            try:
                explored_data = json.loads(explored_data_path.read_text(encoding='utf-8'))
            except Exception:
                pass

        # 读取功能测试结果（如果存在）
        test_results = {}
        results_xml_path = Path(output_dir) / "reports" / "results.xml"
        if results_xml_path.exists():
            test_results = self._parse_test_results(results_xml_path)

        # 构建 prompt
        prompt = self._build_prompt(swagger_content, explored_data, test_results)

        # 调用 Claude CLI 生成
        cli_config = CLIConfig(
            timeout=300,  # 5 分钟超时
            working_dir=str(load_test_dir),
            allowed_tools=["Read", "Write", "Edit"],
            on_output=lambda msg: self._log("debug", msg)
        )
        cli = CLIAdapter(cli_config)

        try:
            result = cli.invoke(prompt, mode=ExecutionMode.SINGLE)
            if result.success:
                self._log("info", "压测脚本生成成功")
            else:
                logger.warning(f"CLI 调用返回非成功状态: {result.error}")
        except Exception as e:
            logger.error(f"CLI 调用失败: {e}")
            # 如果 LLM 调用失败，生成默认脚本
            self._generate_default_locustfile(locustfile_path, swagger_content)

        return locustfile_path

    def _build_prompt(
        self,
        swagger_content: str,
        explored_data: Dict[str, Any],
        test_results: Dict[str, Any]
    ) -> str:
        """构建 LLM prompt"""
        # 解析 Swagger 获取接口摘要
        try:
            swagger = json.loads(swagger_content)
            endpoints = []
            paths = swagger.get('paths', {})
            for path, methods in paths.items():
                for method in ['get', 'post', 'put', 'delete', 'patch']:
                    if method in methods:
                        endpoints.append(f"{method.upper()} {path}")
        except Exception:
            endpoints = ["无法解析 Swagger"]

        # 构建探测数据摘要
        explored_summary = "无探测数据"
        if explored_data:
            resources = explored_data.get('extracted_resources', {})
            if resources:
                explored_summary = json.dumps(resources, indent=2, ensure_ascii=False)

        # 清理 auth_token
        clean_token = ''
        if self.auth_token:
            clean_token = ''.join(c for c in self.auth_token if ord(c) < 128)

        prompt = f"""你是一个专业的性能测试工程师。请生成一个 Locust 压测脚本。

## 目标 API
- Base URL: {self.base_url}
- 认证 Token: {clean_token[:50]}... (已截断)

## 接口列表
{chr(10).join(f'- {e}' for e in endpoints[:20])}
{f'... 还有 {len(endpoints) - 20} 个接口' if len(endpoints) > 20 else ''}

## 探测到的真实数据
```json
{explored_summary[:2000]}
```

## 要求
1. 在当前目录生成 locustfile.py 文件
2. 继承 HttpUser 类
3. 为主要接口创建 @task，GET 接口权重高，写接口权重低
4. 使用探测到的真实 ID (如果有)
5. 正确设置认证头和 SSL (verify=False)
6. 使用 catch_response=True 进行响应验证

请直接生成 locustfile.py 文件。"""

        return prompt

    def _generate_default_locustfile(self, path: Path, swagger_content: str) -> None:
        """生成默认的 locustfile.py (当 LLM 失败时使用)"""
        # 解析 Swagger
        try:
            swagger = json.loads(swagger_content)
            paths = swagger.get('paths', {})
        except Exception:
            paths = {}

        # 生成任务
        tasks = []
        task_id = 0
        for endpoint, methods in list(paths.items())[:10]:  # 最多 10 个接口
            for method in ['get', 'post', 'put', 'delete']:
                if method in methods:
                    task_id += 1
                    weight = 5 if method == 'get' else 1
                    func_name = f"task_{task_id}_{method}"
                    tasks.append(f'''
    @task({weight})
    def {func_name}(self):
        """自动生成: {method.upper()} {endpoint}"""
        self.client.{method}("{endpoint}")
''')

        # 清理 auth_token
        clean_token = ''
        if self.auth_token:
            clean_token = ''.join(c for c in self.auth_token if ord(c) < 128)

        content = f'''"""自动生成的 Locust 压测脚本 (默认模板)"""
from locust import HttpUser, task, between
import urllib3

urllib3.disable_warnings()


class APIUser(HttpUser):
    """API 压测用户"""
    wait_time = between(0.5, 2)
    host = "{self.base_url}"

    def on_start(self):
        """初始化: 设置认证头"""
        self.client.headers = {{
            "Content-Type": "application/json",
            "authorization": "{clean_token}"
        }}
        self.client.verify = False
{''.join(tasks) if tasks else '''
    @task
    def default_task(self):
        """默认任务"""
        self.client.get("/")
'''}
'''
        path.write_text(content, encoding='utf-8')
        logger.info(f"生成默认压测脚本: {path}")

    def _run_locust(self, locustfile: Path, output_dir: Path) -> None:
        """执行 Locust 压测"""
        csv_prefix = output_dir / "load_test"
        html_report = output_dir / "load_test.html"

        cmd = [
            "locust",
            "-f", str(locustfile),
            "--host", self.base_url,
            "--users", str(self.config.concurrent_users),
            "--spawn-rate", str(self.config.spawn_rate),
            "--run-time", f"{self.config.duration}s",
            "--headless",
            "--csv", str(csv_prefix),
            "--html", str(html_report),
            "--only-summary"
        ]

        logger.info(f"执行 Locust: {' '.join(cmd)}")

        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=str(output_dir)
        )

        # 实时读取输出
        progress = LoadTestProgress()
        start_time = time.time()

        for line in self._process.stdout:
            line = line.strip()
            if line:
                logger.debug(f"[locust] {line}")
                self._log("debug", line)

                # 解析进度
                progress.elapsed_time = time.time() - start_time
                self._parse_locust_output(line, progress)

                if self.on_progress:
                    self.on_progress(progress)

            # 检查是否取消
            if self._is_cancelled():
                self.stop()
                break

        self._process.wait()

    def _parse_locust_output(self, line: str, progress: LoadTestProgress) -> None:
        """解析 Locust 输出更新进度"""
        # 匹配类似: "Aggregated 1000 5 100.0 50.5"
        # 或者: "Name  # reqs  # fails  |  Avg  ..."
        try:
            # 匹配用户数
            users_match = re.search(r'(\d+)\s+users', line, re.IGNORECASE)
            if users_match:
                progress.current_users = int(users_match.group(1))

            # 匹配 RPS
            rps_match = re.search(r'(\d+\.?\d*)\s*(?:req/s|RPS)', line, re.IGNORECASE)
            if rps_match:
                progress.requests_per_second = float(rps_match.group(1))

            # 匹配请求数
            reqs_match = re.search(r'(\d+)\s+(?:requests?|reqs?)', line, re.IGNORECASE)
            if reqs_match:
                progress.total_requests = int(reqs_match.group(1))

            # 匹配失败数
            fails_match = re.search(r'(\d+)\s+fail', line, re.IGNORECASE)
            if fails_match:
                progress.failed_requests = int(fails_match.group(1))

        except Exception:
            pass

    def _parse_results(self, output_dir: Path, result: LoadTestResult) -> LoadTestResult:
        """解析 Locust CSV 结果"""
        stats_file = output_dir / "load_test_stats.csv"
        history_file = output_dir / "load_test_stats_history.csv"

        # 设置报告路径
        result.report_path = str(output_dir / "load_test.html")
        result.csv_path = str(stats_file)

        if not stats_file.exists():
            logger.warning(f"未找到结果文件: {stats_file}")
            return result

        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('Name') == 'Aggregated':
                        result.total_requests = int(row.get('Request Count', 0))
                        result.failed_requests = int(row.get('Failure Count', 0))
                        result.avg_response_time = float(row.get('Average Response Time', 0))
                        result.min_response_time = float(row.get('Min Response Time', 0))
                        result.max_response_time = float(row.get('Max Response Time', 0))
                        result.p50_response_time = float(row.get('50%', 0))
                        result.p95_response_time = float(row.get('95%', 0))
                        result.p99_response_time = float(row.get('99%', 0))
                        result.requests_per_second = float(row.get('Requests/s', 0))
                        result.duration = self.config.duration
                    else:
                        # 按接口统计
                        name = row.get('Name', 'unknown')
                        if name:
                            result.endpoint_stats[name] = {
                                'requests': int(row.get('Request Count', 0)),
                                'failures': int(row.get('Failure Count', 0)),
                                'avg_time': float(row.get('Average Response Time', 0)),
                                'p95_time': float(row.get('95%', 0)),
                            }

        except Exception as e:
            logger.error(f"解析结果失败: {e}")

        return result

    def _parse_test_results(self, xml_path: Path) -> Dict[str, Any]:
        """解析 JUnit XML 测试结果"""
        # 简化实现，返回空字典
        return {}
