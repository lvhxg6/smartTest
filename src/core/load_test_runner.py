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
        """构建 LLM prompt

        根据配置实现智能筛选：
        - only_passed=True: 仅压测功能测试通过的接口
        - target_endpoints: 指定要压测的接口列表
        """
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

        # 智能筛选：根据配置确定要压测的接口
        target_endpoints = []
        filter_note = ""

        if getattr(self.config, 'only_passed', False) and test_results:
            # 仅压测通过的接口
            passed_tests = test_results.get('passed_endpoints', [])
            if passed_tests:
                target_endpoints = passed_tests
                filter_note = f"""
## 功能测试结果（智能筛选）
- 总测试数: {test_results.get('total', 0)}
- 通过数: {len(passed_tests)}
- 失败数: {len(test_results.get('failed_endpoints', []))}
- 通过率: {test_results.get('pass_rate', 0):.1%}

**筛选模式**: 仅压测通过的接口 ({len(passed_tests)} 个)

### 通过的测试用例
{chr(10).join(f'- {t}' for t in passed_tests[:20])}
{f'... 还有 {len(passed_tests) - 20} 个' if len(passed_tests) > 20 else ''}
"""
                logger.info(f"智能筛选: 仅压测 {len(passed_tests)} 个通过的接口")
            else:
                filter_note = "\n## 功能测试结果\n没有通过的测试用例，将压测所有接口。\n"
                logger.warning("功能测试没有通过的用例，回退到压测所有接口")

        elif getattr(self.config, 'target_endpoints', None):
            # 使用指定的接口列表
            target_endpoints = self.config.target_endpoints
            filter_note = f"""
## 指定压测接口
仅压测以下指定的 {len(target_endpoints)} 个接口:
{chr(10).join(f'- {e}' for e in target_endpoints)}
"""
            logger.info(f"使用指定接口: {len(target_endpoints)} 个")

        elif test_results and test_results.get('total', 0) > 0:
            # 有测试结果但不筛选
            filter_note = f"""
## 功能测试结果（参考）
- 总测试数: {test_results.get('total', 0)}
- 通过数: {len(test_results.get('passed_endpoints', []))}
- 失败数: {len(test_results.get('failed_endpoints', []))}
- 通过率: {test_results.get('pass_rate', 0):.1%}

**筛选模式**: 压测所有接口
"""

        prompt = f"""你是一个专业的性能测试工程师。请生成一个 Locust 压测脚本。

## 目标 API
- Base URL: {self.base_url}
- 认证 Token: {clean_token[:50]}... (已截断)
{filter_note}
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
3. {'仅为上述「通过的测试用例」相关接口创建 @task' if target_endpoints else '为主要接口创建 @task'}
4. GET 接口权重高，写接口权重低
5. 使用探测到的真实 ID (如果有)
6. 正确设置认证头和 SSL (verify=False)
7. 使用 catch_response=True 进行响应验证
8. 并发用户: {self.config.concurrent_users}
9. 生成速率: {self.config.spawn_rate}/秒
10. 持续时间: {self.config.duration}秒

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
        """解析 JUnit XML 测试结果，提取通过/失败的接口

        Returns:
            Dict 包含:
            - passed_endpoints: 通过的测试用例名称列表
            - failed_endpoints: 失败的测试用例名称列表
            - total: 总测试数
            - pass_rate: 通过率
        """
        if not xml_path.exists():
            logger.warning(f"测试结果文件不存在: {xml_path}")
            return {"passed_endpoints": [], "failed_endpoints": [], "total": 0, "pass_rate": 0}

        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(xml_path)
            root = tree.getroot()

            passed = []
            failed = []

            # 遍历所有 testcase 元素
            for testcase in root.iter('testcase'):
                name = testcase.get('name', '')
                classname = testcase.get('classname', '')

                # 构建完整测试标识
                full_name = f"{classname}::{name}" if classname else name

                # 检查是否有 failure 或 error 子元素
                has_failure = testcase.find('failure') is not None
                has_error = testcase.find('error') is not None
                has_skipped = testcase.find('skipped') is not None

                if has_failure or has_error:
                    failed.append(full_name)
                elif not has_skipped:  # 跳过的测试不计入
                    passed.append(full_name)

            total = len(passed) + len(failed)
            pass_rate = len(passed) / max(total, 1)

            logger.info(f"解析测试结果: {len(passed)} 通过, {len(failed)} 失败, 通过率 {pass_rate:.1%}")

            return {
                "passed_endpoints": passed,
                "failed_endpoints": failed,
                "total": total,
                "pass_rate": pass_rate
            }

        except Exception as e:
            logger.error(f"解析 JUnit XML 失败: {e}")
            return {"passed_endpoints": [], "failed_endpoints": [], "total": 0, "pass_rate": 0}
