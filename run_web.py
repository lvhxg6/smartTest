#!/usr/bin/env python3
"""
启动 Smart Dev Mantis Web 服务

使用方式:
    python run_web.py
    python run_web.py --port 8080
    python run_web.py --debug
"""

import argparse
import logging

from src.web import run_server

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Smart Dev Mantis Web Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print(f"""
╔═══════════════════════════════════════════╗
║       Smart Dev Mantis v1.0               ║
║       Web Server Starting...              ║
╚═══════════════════════════════════════════╝

    URL: http://{args.host}:{args.port}
    Debug: {args.debug}

    Press Ctrl+C to stop
    """)

    run_server(host=args.host, port=args.port, debug=args.debug)
