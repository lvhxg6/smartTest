#!/usr/bin/env python3
"""
Smart Dev Mantis - CLI 入口

使用方式:
    python -m src.main --swagger api.json --base-url https://api.example.com

    # 完整模式 (带业务规则)
    python -m src.main --swagger api.json --base-url https://api.example.com \
        --requirements rules.md --data data.md --token "Bearer xxx"

    # 指定输出目录
    python -m src.main --swagger api.json --base-url https://api.example.com \
        --output ./my_output
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .core import InputParser, WorkflowEngine, WorkflowConfig, WorkflowState
from .models import FinalReport

# 配置 Rich Console
console = Console()


def setup_logging(verbose: bool = False) -> None:
    """配置日志"""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(
            console=console,
            show_path=False,
            rich_tracebacks=True
        )]
    )


def create_output_dir(base_dir: str) -> str:
    """创建带时间戳的输出目录"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = Path(base_dir) / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir)


def print_banner() -> None:
    """打印启动横幅"""
    banner = """
[bold blue]╔═══════════════════════════════════════════╗
║       Smart Dev Mantis v1.0               ║
║       Powered by Claude Code CLI          ║
╚═══════════════════════════════════════════╝[/bold blue]
    """
    console.print(banner)


def print_report(report: FinalReport) -> None:
    """打印最终报告"""
    status_icon = "✅" if report.success else "❌"
    status_color = "green" if report.success else "red"

    summary = f"""
[bold]{status_icon} 测试执行完成[/bold]

[bold]统计:[/bold]
  总用例数: {report.total_cases}
  通过: [green]{report.passed}[/green]
  失败: [red]{report.failed}[/red]
  通过率: [{status_color}]{report.pass_rate:.1f}%[/{status_color}]
  发现Bug: {report.bugs_found}
  自愈成功: {report.healed_count}
  总耗时: {report.total_duration:.1f}s

[bold]输出文件:[/bold]
  用例文档: {report.testcases_file}
  HTML报告: {report.report_html}
  Bug报告: {report.bug_report_file}
    """

    console.print(Panel(summary, title="执行报告", border_style=status_color))


def on_state_change(state: WorkflowState, message: str) -> None:
    """状态变更回调"""
    state_icons = {
        WorkflowState.INIT: "🔄",
        WorkflowState.PLANNING: "📋",
        WorkflowState.GENERATING: "⚙️",
        WorkflowState.EXECUTING: "🧪",
        WorkflowState.HEALING: "🔧",
        WorkflowState.FINALIZING: "📊",
        WorkflowState.COMPLETED: "✅",
        WorkflowState.FAILED: "❌"
    }
    icon = state_icons.get(state, "▶")
    console.print(f"{icon} [bold]{state.value}[/bold] {message}")


def on_log(level: str, phase: str, message: str) -> None:
    """日志回调"""
    level_styles = {
        "info": "blue",
        "warning": "yellow",
        "error": "red"
    }
    style = level_styles.get(level.lower(), "white")
    console.print(f"  [{style}][{phase}][/{style}] {message}")


def main() -> int:
    """主入口"""
    parser = argparse.ArgumentParser(
        description="Smart Dev Mantis - LLM驱动的API自动化测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 轻量模式 (仅Swagger)
  python -m src.main --swagger api.json --base-url https://api.example.com

  # 完整模式 (带业务规则)
  python -m src.main --swagger api.json --base-url https://api.example.com \\
      --requirements rules.md --data data.md

  # 带认证
  python -m src.main --swagger api.json --base-url https://api.example.com \\
      --token "Bearer eyJ..."
        """
    )

    # 必填参数
    parser.add_argument(
        "--swagger", "-s",
        required=True,
        help="Swagger/OpenAPI 文件路径"
    )
    parser.add_argument(
        "--base-url", "-u",
        required=True,
        help="API 基础 URL"
    )

    # 可选参数
    parser.add_argument(
        "--requirements", "-r",
        help="业务规则文件路径 (Markdown)"
    )
    parser.add_argument(
        "--data", "-d",
        help="测试数据文件路径 (Markdown)"
    )
    parser.add_argument(
        "--token", "-t",
        help="认证 Token (如 'Bearer xxx')"
    )
    parser.add_argument(
        "--output", "-o",
        default="./output",
        help="输出目录 (默认: ./output)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="单个测试用例超时时间(秒) (默认: 120)"
    )
    parser.add_argument(
        "--max-healing",
        type=int,
        default=3,
        help="最大自愈尝试次数 (默认: 3)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )

    args = parser.parse_args()

    # 配置日志
    setup_logging(args.verbose)

    # 打印横幅
    print_banner()

    try:
        # 创建输出目录
        output_dir = create_output_dir(args.output)
        console.print(f"📁 输出目录: {output_dir}\n")

        # 解析输入
        console.print("🔍 解析输入文件...")
        input_parser = InputParser()
        context = input_parser.parse(
            swagger_input=args.swagger,
            base_url=args.base_url,
            auth_token=args.token,
            requirements_input=args.requirements,
            data_assets_input=args.data,
            output_dir=output_dir
        )

        console.print(f"  Swagger: {context.swagger.title} ({context.swagger.endpoint_count} 端点)")
        console.print(f"  模式: {context.test_mode.value}")
        console.print()

        # 配置工作流
        workflow_config = WorkflowConfig(
            max_healing_attempts=args.max_healing,
            test_timeout=args.timeout,
            on_state_change=on_state_change,
            on_log=on_log
        )

        # 运行工作流
        engine = WorkflowEngine(context, workflow_config)
        report = engine.run()

        # 打印报告
        console.print()
        print_report(report)

        return 0 if report.success else 1

    except FileNotFoundError as e:
        console.print(f"[red]❌ 文件未找到: {e}[/red]")
        return 1
    except Exception as e:
        console.print(f"[red]❌ 执行失败: {e}[/red]")
        if args.verbose:
            console.print_exception()
        return 1


if __name__ == "__main__":
    sys.exit(main())
