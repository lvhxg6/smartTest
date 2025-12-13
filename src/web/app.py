"""
Flask Web Application - Smart Dev Mantis

提供:
- Web UI 页面
- REST API (启动测试、查询状态、下载报告)
- WebSocket 实时日志推送
"""

import os
import json
import uuid
import logging
import threading
import zipfile
from io import BytesIO
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_socketio import SocketIO, emit

from ..core import InputParser, WorkflowEngine, WorkflowConfig, WorkflowState
from ..core.load_test_runner import LoadTestRunner
from ..models import FinalReport, LoadTestConfig, LoadTestResult, LoadTestStatus

logger = logging.getLogger(__name__)

# Flask 应用
app = Flask(__name__,
    template_folder=str(Path(__file__).parent / "templates"),
    static_folder=str(Path(__file__).parent / "static")
)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'smart-dev-mantis-secret')
app.config['TEMPLATES_AUTO_RELOAD'] = True  # 禁用模板缓存

# WebSocket
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 任务存储 (内存)
tasks: Dict[str, Dict[str, Any]] = {}

# 压测任务存储 (内存)
load_tests: Dict[str, Dict[str, Any]] = {}


class TaskManager:
    """任务管理器"""

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.status = "pending"
        self.report: Optional[FinalReport] = None
        self.error: Optional[str] = None
        self.output_dir: Optional[str] = None

    def emit_log(self, level: str, phase: str, message: str) -> None:
        """通过 WebSocket 发送日志"""
        socketio.emit('log', {
            'task_id': self.task_id,
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'phase': phase,
            'message': message
        }, namespace='/ws')

    def emit_state(self, state: WorkflowState, message: str) -> None:
        """通过 WebSocket 发送状态变更"""
        self.status = state.value
        socketio.emit('state', {
            'task_id': self.task_id,
            'state': state.value,
            'message': message
        }, namespace='/ws')

    def emit_result(self, report: FinalReport) -> None:
        """通过 WebSocket 发送最终结果"""
        socketio.emit('result', {
            'task_id': self.task_id,
            'summary': report.get_summary(),
            'success': report.success
        }, namespace='/ws')

    def emit_todos(self, todos: List[Dict[str, Any]]) -> None:
        """通过 WebSocket 发送 Todo 列表"""
        socketio.emit('todos', {
            'task_id': self.task_id,
            'todos': todos
        }, namespace='/ws')


def create_output_dir(base_dir: str = "./output") -> str:
    """创建带时间戳的输出目录"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    # 使用绝对路径，避免 Flask 工作目录导致的路径解析错误
    output_dir = Path(base_dir).resolve() / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir)


def run_workflow_task(task_id: str, params: Dict[str, Any], cancel_event: threading.Event) -> None:
    """在后台线程中运行工作流"""
    manager = TaskManager(task_id)
    tasks[task_id]['manager'] = manager

    try:
        manager.status = "running"
        manager.emit_log("info", "init", "任务启动...")

        # 创建输出目录
        output_dir = create_output_dir()
        manager.output_dir = output_dir
        tasks[task_id]['output_dir'] = output_dir

        # 解析输入
        manager.emit_log("info", "init", "解析输入参数...")
        input_parser = InputParser()

        context = input_parser.parse(
            swagger_input=params['swagger_content'],
            base_url=params['base_url'],
            auth_token=params.get('auth_token'),
            requirements_input=params.get('requirements'),
            data_assets_input=params.get('data_assets'),
            output_dir=output_dir
        )

        manager.emit_log("info", "init", f"Swagger: {context.swagger.title} ({context.swagger.endpoint_count} 端点)")
        manager.emit_log("info", "init", f"测试模式: {context.test_mode.value}")

        # 配置工作流
        workflow_config = WorkflowConfig(
            on_state_change=manager.emit_state,
            on_log=manager.emit_log,
            on_todo_update=manager.emit_todos,  # Todo 进度回调
            enable_exploration=params.get('enable_exploration', False),
            cancel_event=cancel_event
        )

        # 运行工作流
        engine = WorkflowEngine(context, workflow_config)
        report = engine.run()

        # 若返回 None，说明被用户取消
        if report is None:
            manager.status = "cancelled"
            tasks[task_id]['status'] = "cancelled"
            manager.emit_log("warning", "system", "任务已取消")
            return

        # 保存结果
        manager.report = report
        manager.status = "completed"
        tasks[task_id]['report'] = report.to_dict()
        tasks[task_id]['status'] = "completed"

        manager.emit_result(report)
        manager.emit_log("info", "complete", f"任务完成！通过率: {report.pass_rate:.1f}%")

    except Exception as e:
        is_cancel = cancel_event.is_set() or "取消" in str(e)
        if is_cancel:
            logger.warning(f"Task {task_id} cancelled: {e}")
            manager.status = "cancelled"
            tasks[task_id]['status'] = "cancelled"
            manager.emit_log("warning", "system", f"任务已取消: {str(e)}")
            socketio.emit('state', {
                'task_id': task_id,
                'state': "已取消",
                'message': str(e)
            }, namespace='/ws')
        else:
            logger.exception(f"Task {task_id} failed")
            manager.status = "failed"
            manager.error = str(e)
            tasks[task_id]['status'] = "failed"
            tasks[task_id]['error'] = str(e)

            manager.emit_log("error", "error", f"任务失败: {str(e)}")
            socketio.emit('error', {
                'task_id': task_id,
                'error': str(e)
            }, namespace='/ws')


# ============== 页面路由 ==============

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


# ============== API 路由 ==============

@app.route('/api/run', methods=['POST'])
def api_run():
    """启动测试任务

    Request Body:
    {
        "swagger": "<swagger json content or file path>",
        "base_url": "https://api.example.com",
        "auth_token": "Bearer xxx",  // optional
        "requirements": "...",        // optional
        "data_assets": "..."          // optional
    }
    """
    try:
        data = request.json

        # 验证必填参数
        if not data.get('swagger'):
            return jsonify({'error': 'swagger is required'}), 400
        if not data.get('base_url'):
            return jsonify({'error': 'base_url is required'}), 400

        # 创建任务
        task_id = str(uuid.uuid4())[:8]

        params = {
            'swagger_content': data['swagger'],
            'base_url': data['base_url'],
            'auth_token': data.get('auth_token'),
            'requirements': data.get('requirements'),
            'data_assets': data.get('data_assets'),
            'enable_exploration': bool(data.get('enable_exploration'))
        }

        cancel_event = threading.Event()

        tasks[task_id] = {
            'id': task_id,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'params': params,
            'cancel_event': cancel_event
        }

        # 启动后台任务
        thread = threading.Thread(
            target=run_workflow_task,
            args=(task_id, params, cancel_event)
        )
        thread.daemon = True
        tasks[task_id]['thread'] = thread
        thread.start()

        return jsonify({
            'task_id': task_id,
            'status': 'started',
            'message': '任务已启动，请通过 WebSocket 监听进度'
        })

    except Exception as e:
        logger.exception("Failed to start task")
        return jsonify({'error': str(e)}), 500


@app.route('/api/status/<task_id>')
def api_status(task_id: str):
    """查询任务状态"""
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404

    task = tasks[task_id]
    response = {
        'task_id': task_id,
        'status': task.get('status', 'unknown'),
        'created_at': task.get('created_at')
    }

    if task.get('status') == 'completed' and task.get('report'):
        response['report'] = task['report']

    if task.get('status') == 'failed':
        response['error'] = task.get('error')

    return jsonify(response)


@app.route('/api/download/<task_id>/<file_type>')
def api_download(task_id: str, file_type: str):
    """下载报告文件

    Args:
        task_id: 任务ID
        file_type: 文件类型 (html, xml, json, testcases, tests, business)
    """
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404

    task = tasks[task_id]
    output_dir = task.get('output_dir')

    if not output_dir:
        return jsonify({'error': 'Output directory not found'}), 404

    # 确保使用绝对路径
    output_path = Path(output_dir)
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path

    # 处理 tests 打包下载
    if file_type == 'tests':
        tests_dir = output_path / 'tests'
        if not tests_dir.exists():
            return jsonify({'error': 'Tests directory not found'}), 404

        # 打包 tests 目录为 zip
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in tests_dir.rglob('*'):
                if file.is_file():
                    arcname = file.relative_to(tests_dir)
                    zf.write(file, arcname)

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='tests.zip'
        )

    file_map = {
        'html': output_path / 'reports' / 'report.html',
        'xml': output_path / 'reports' / 'results.xml',
        'json': output_path / 'bug_report.json',
        'testcases': output_path / 'testcases.md',
        'business': output_path / 'reports' / 'business_report.html'
    }

    if file_type not in file_map:
        return jsonify({'error': f'Invalid file type: {file_type}'}), 400

    file_path = file_map[file_type]

    if not file_path.exists():
        return jsonify({'error': f'File not found: {file_type}'}), 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name=file_path.name
    )


@app.route('/api/tasks')
def api_tasks():
    """获取所有任务列表"""
    task_list = []
    for task_id, task in tasks.items():
        task_list.append({
            'task_id': task_id,
            'status': task.get('status'),
            'created_at': task.get('created_at')
        })
    return jsonify({'tasks': task_list})


@app.route('/api/cancel/<task_id>', methods=['POST'])
def api_cancel(task_id: str):
    """取消正在执行的任务"""
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    cancel_event = task.get('cancel_event')
    if cancel_event:
        cancel_event.set()
        task['status'] = 'cancelled'
        return jsonify({'message': 'Task cancellation requested'}), 200

    return jsonify({'error': 'Cancel event not available'}), 400


# ============== 压力测试 API ==============

def run_load_test_task(load_test_id: str, task_id: str, config: LoadTestConfig, cancel_event: threading.Event) -> None:
    """在后台线程中运行压力测试"""
    try:
        task = tasks.get(task_id)
        if not task:
            raise ValueError(f"功能测试任务不存在: {task_id}")

        output_dir = task.get('output_dir')
        if not output_dir:
            raise ValueError("功能测试输出目录不存在")

        params = task.get('params', {})
        base_url = params.get('base_url')
        auth_token = params.get('auth_token')
        swagger_content = params.get('swagger_content')

        if not base_url or not swagger_content:
            raise ValueError("缺少必要参数: base_url 或 swagger_content")

        load_tests[load_test_id]['status'] = 'running'

        # 进度回调
        def on_progress(progress):
            socketio.emit('load_test_progress', {
                'load_test_id': load_test_id,
                **progress.to_dict()
            }, namespace='/ws')

        # 日志回调
        def on_log(message):
            socketio.emit('load_test_log', {
                'load_test_id': load_test_id,
                'message': message
            }, namespace='/ws')

        # 创建 runner 并执行
        runner = LoadTestRunner(
            config=config,
            base_url=base_url,
            auth_token=auth_token,
            on_progress=on_progress,
            on_log=on_log,
            cancel_event=cancel_event
        )

        load_tests[load_test_id]['runner'] = runner
        result = runner.run(output_dir, swagger_content)

        # 保存结果
        load_tests[load_test_id]['result'] = result.to_dict()
        load_tests[load_test_id]['status'] = result.status.value

        # 发送完成事件
        socketio.emit('load_test_complete', {
            'load_test_id': load_test_id,
            'result': result.to_dict()
        }, namespace='/ws')

    except Exception as e:
        logger.exception(f"Load test {load_test_id} failed")
        load_tests[load_test_id]['status'] = 'failed'
        load_tests[load_test_id]['error'] = str(e)
        socketio.emit('load_test_error', {
            'load_test_id': load_test_id,
            'error': str(e)
        }, namespace='/ws')


@app.route('/api/load-test', methods=['POST'])
def api_start_load_test():
    """启动压力测试

    Request Body:
    {
        "task_id": "功能测试任务ID",
        "preset": "light|standard|heavy",  // 可选，预设配置
        "concurrent_users": 50,            // 可选，自定义并发数
        "spawn_rate": 10,                  // 可选，每秒启动用户数
        "duration": 60,                    // 可选，持续时间(秒)
        "only_passed": false               // 可选，仅测试通过的接口
    }
    """
    try:
        data = request.json

        task_id = data.get('task_id')
        if not task_id:
            return jsonify({'error': 'task_id is required'}), 400

        if task_id not in tasks:
            return jsonify({'error': 'Task not found'}), 404

        task = tasks[task_id]
        if task.get('status') != 'completed':
            return jsonify({'error': '功能测试尚未完成'}), 400

        # 解析配置
        preset = data.get('preset')
        if preset:
            config = LoadTestConfig.from_preset(preset)
        else:
            config = LoadTestConfig(
                concurrent_users=data.get('concurrent_users', 50),
                spawn_rate=data.get('spawn_rate', 10),
                duration=data.get('duration', 60),
                only_passed=data.get('only_passed', False)
            )

        # 创建压测任务
        load_test_id = str(uuid.uuid4())[:8]
        cancel_event = threading.Event()

        load_tests[load_test_id] = {
            'id': load_test_id,
            'task_id': task_id,
            'status': 'pending',
            'config': config.to_dict(),
            'created_at': datetime.now().isoformat(),
            'cancel_event': cancel_event
        }

        # 启动后台任务
        thread = threading.Thread(
            target=run_load_test_task,
            args=(load_test_id, task_id, config, cancel_event)
        )
        thread.daemon = True
        load_tests[load_test_id]['thread'] = thread
        thread.start()

        return jsonify({
            'load_test_id': load_test_id,
            'status': 'started',
            'config': config.to_dict(),
            'message': '压力测试已启动'
        })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.exception("Failed to start load test")
        return jsonify({'error': str(e)}), 500


@app.route('/api/load-test/<load_test_id>/status')
def api_load_test_status(load_test_id: str):
    """查询压测状态"""
    if load_test_id not in load_tests:
        return jsonify({'error': 'Load test not found'}), 404

    load_test = load_tests[load_test_id]
    response = {
        'load_test_id': load_test_id,
        'task_id': load_test.get('task_id'),
        'status': load_test.get('status'),
        'config': load_test.get('config'),
        'created_at': load_test.get('created_at')
    }

    if load_test.get('result'):
        response['result'] = load_test['result']

    if load_test.get('error'):
        response['error'] = load_test['error']

    return jsonify(response)


@app.route('/api/load-test/<load_test_id>/stop', methods=['POST'])
def api_stop_load_test(load_test_id: str):
    """停止压测"""
    if load_test_id not in load_tests:
        return jsonify({'error': 'Load test not found'}), 404

    load_test = load_tests[load_test_id]

    # 设置取消事件
    cancel_event = load_test.get('cancel_event')
    if cancel_event:
        cancel_event.set()

    # 调用 runner 的 stop 方法
    runner = load_test.get('runner')
    if runner:
        runner.stop()

    load_test['status'] = 'stopped'
    return jsonify({'message': '压测已停止'})


@app.route('/api/load-test/<load_test_id>/report')
def api_load_test_report(load_test_id: str):
    """获取压测报告"""
    if load_test_id not in load_tests:
        return jsonify({'error': 'Load test not found'}), 404

    load_test = load_tests[load_test_id]
    result = load_test.get('result')

    if not result:
        return jsonify({'error': '压测尚未完成'}), 400

    report_path = result.get('report_path')
    if report_path and Path(report_path).exists():
        return send_file(report_path, as_attachment=False)

    return jsonify({'error': '报告文件不存在'}), 404


# ============== WebSocket 事件 ==============

@socketio.on('connect', namespace='/ws')
def ws_connect():
    """WebSocket 连接"""
    logger.info(f"WebSocket client connected: {request.sid}")
    emit('connected', {'message': 'Connected to Smart Dev Mantis'})


@socketio.on('disconnect', namespace='/ws')
def ws_disconnect():
    """WebSocket 断开"""
    logger.info(f"WebSocket client disconnected: {request.sid}")


@socketio.on('subscribe', namespace='/ws')
def ws_subscribe(data):
    """订阅任务进度"""
    task_id = data.get('task_id')
    if task_id and task_id in tasks:
        emit('subscribed', {'task_id': task_id, 'status': tasks[task_id].get('status')})
    else:
        emit('error', {'message': 'Task not found'})


# ============== 启动函数 ==============

def run_server(host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
    """启动服务器"""
    logger.info(f"Starting Smart Dev Mantis Web Server on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_server(debug=True)
