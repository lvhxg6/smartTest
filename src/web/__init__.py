# Web UI module
"""
Flask Web Application for Nexus AI Test Agent

启动方式:
    python -m src.web.app

或者:
    from src.web import app, socketio, run_server
    run_server(host='0.0.0.0', port=5000)
"""

from .app import app, socketio, run_server

__all__ = ['app', 'socketio', 'run_server']
