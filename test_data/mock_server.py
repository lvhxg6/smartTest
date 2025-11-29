#!/usr/bin/env python3
"""
Mock API Server - 用于测试 Nexus AI Test Agent

提供简单的用户管理 CRUD 接口
"""

from flask import Flask, jsonify, request

app = Flask(__name__)

# 模拟数据库
users_db = {
    1: {"id": 1, "name": "张三", "email": "zhangsan@example.com", "age": 25},
    2: {"id": 2, "name": "李四", "email": "lisi@example.com", "age": 30},
    3: {"id": 3, "name": "王五", "email": "wangwu@example.com", "age": 28},
}
next_id = 4


@app.route('/api/users', methods=['GET'])
def get_users():
    """获取用户列表"""
    return jsonify(list(users_db.values()))


@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """根据ID获取用户"""
    if user_id not in users_db:
        return jsonify({"code": 404, "message": "用户不存在"}), 404
    return jsonify(users_db[user_id])


@app.route('/api/users', methods=['POST'])
def create_user():
    """创建新用户"""
    global next_id

    data = request.get_json()

    # 参数验证
    if not data:
        return jsonify({"code": 400, "message": "请求体不能为空"}), 400

    if not data.get('name'):
        return jsonify({"code": 400, "message": "name 是必填字段"}), 400

    if not data.get('email'):
        return jsonify({"code": 400, "message": "email 是必填字段"}), 400

    if len(data.get('name', '')) < 2:
        return jsonify({"code": 400, "message": "name 长度不能少于2个字符"}), 400

    # 检查邮箱格式
    email = data.get('email', '')
    if '@' not in email:
        return jsonify({"code": 400, "message": "email 格式不正确"}), 400

    # 检查年龄范围
    age = data.get('age')
    if age is not None:
        if not isinstance(age, int) or age < 0 or age > 150:
            return jsonify({"code": 400, "message": "age 必须是0-150之间的整数"}), 400

    # 创建用户
    new_user = {
        "id": next_id,
        "name": data['name'],
        "email": data['email'],
        "age": data.get('age', 0)
    }
    users_db[next_id] = new_user
    next_id += 1

    return jsonify(new_user), 201


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """删除用户"""
    if user_id not in users_db:
        return jsonify({"code": 404, "message": "用户不存在"}), 404

    del users_db[user_id]
    return '', 204


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════╗
║         Mock API Server v1.0              ║
║         http://localhost:3001             ║
╚═══════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=3001, debug=True)
