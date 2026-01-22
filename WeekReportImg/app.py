#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
周报图片生成器 - Web 服务
从多行文本框获取数据，生成 SVG 并展示最近 5 次生成记录。
"""

import json
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import BadRequest

ROOT = Path(__file__).resolve().parent
from weeKReportImgGen import WeekReportImageGenerator

app = Flask(__name__)
HISTORY_PATH = ROOT / 'output' / 'history.json'
HISTORY_MAX = 5
DEFAULT_DATA_PATH = ROOT / 'data.txt'


def _load_history() -> list:
    if not HISTORY_PATH.exists():
        return []
    try:
        with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_history(history: list) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
        json.dump(history[:HISTORY_MAX], f, ensure_ascii=False, indent=2)


def _add_history(entry: dict) -> None:
    history = _load_history()
    history.insert(0, entry)
    _save_history(history)


@app.route('/')
def index():
    return send_from_directory(ROOT, 'index.html')


@app.route('/output/<path:filename>')
def serve_output(filename):
    return send_from_directory(ROOT / 'output', filename)


@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json(force=True, silent=True) or {}
    content = data.get('content') or ''
    content = (content or '').strip()
    if not content:
        raise BadRequest('请填写周报数据内容')

    suffix = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    gen = WeekReportImageGenerator(str(DEFAULT_DATA_PATH))
    try:
        path_a, path_b = gen.generate_from_content(content, suffix)
    except ValueError as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

    name_a = Path(path_a).name
    name_b = Path(path_b).name

    entry = {
        'viewA': name_a,
        'viewB': name_b,
        'generatedAt': generated_at,
    }
    _add_history(entry)

    return jsonify({
        'ok': True,
        'viewA': f'/output/{name_a}',
        'viewB': f'/output/{name_b}',
        'generatedAt': generated_at,
    })


@app.route('/api/history')
def history():
    h = _load_history()
    return jsonify(h)


@app.route('/api/default-data')
def default_data():
    if not DEFAULT_DATA_PATH.exists():
        return jsonify({'content': ''})
    with open(DEFAULT_DATA_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    return jsonify({'content': content})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=True)
