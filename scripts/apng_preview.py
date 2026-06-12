#!/usr/bin/env python3
"""
APNG 预览服务器 - 启动本地 HTTP 服务展示 APNG 动画预览页面
支持中文界面和下载按钮

用法:
    python apng_preview.py <apng_file> [--port 8767]
"""

import argparse
import base64
import http.server
import socketserver
import os
import sys
import struct
import signal


def get_apng_info(filepath):
    """读取 APNG 文件的基本信息"""
    file_size = os.path.getsize(filepath)
    frames = 0
    fps = 0
    width = 0
    height = 0
    loops = 0

    with open(filepath, 'rb') as f:
        sig = f.read(8)
        if sig != b'\x89PNG\r\n\x1a\n':
            return None

        while True:
            length_bytes = f.read(4)
            if len(length_bytes) == 0:
                break
            length = struct.unpack('>I', length_bytes)[0]
            chunk_type = f.read(4)
            data = f.read(length)
            f.read(4)  # CRC

            if chunk_type == b'IHDR':
                width, height = struct.unpack('>II', data[:8])
            elif chunk_type == b'acTL':
                frames, loops = struct.unpack('>II', data[:8])
            elif chunk_type == b'fcTL':
                if fps == 0 and len(data) >= 26:
                    seq, w, h, xo, yo, delay_num, delay_den, dispose, blend = struct.unpack('>IIIIIHHBB', data[:26])
                    if delay_den > 0 and delay_num > 0:
                        fps = round(1000 / (delay_num / delay_den))

    if fps == 0:
        fps = 15

    duration = round(frames / fps, 2) if fps > 0 else 0
    filename = os.path.basename(filepath)

    return {
        'filename': filename,
        'frames': frames,
        'fps': fps,
        'width': width,
        'height': height,
        'duration': duration,
        'loops': '无限循环' if loops == 0 else f'{loops} 次',
        'size_kb': round(file_size / 1024, 1),
        'size_display': f'{round(file_size / 1024, 1)} KB' if file_size < 1024 * 1024 else f'{round(file_size / 1024 / 1024, 2)} MB',
    }


def generate_html(apng_path, info):
    """生成预览页面的 HTML"""
    with open(apng_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>APNG 动画预览</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    min-height: 100vh; background: #1a1a2e; color: #e0e0e0;
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
}}
.container {{
    background: #252540; border-radius: 16px; padding: 32px 40px; text-align: center;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4); max-width: 520px; width: 90%;
}}
h2 {{ font-size: 22px; font-weight: 600; margin-bottom: 6px; color: #fff; }}
.subtitle {{ color: #888; font-size: 13px; margin-bottom: 24px; }}
.preview-area {{
    background: repeating-conic-gradient(#e8e8e8 0% 25%, #fff 0% 50%) 50% / 16px 16px;
    border-radius: 10px; padding: 16px; margin-bottom: 24px;
    display: flex; align-items: center; justify-content: center;
}}
.preview-area img {{
    max-width: 100%; max-height: 400px; border-radius: 6px;
    image-rendering: auto;
}}
.params {{
    display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; margin-bottom: 24px;
}}
.param {{
    background: #35355a; padding: 6px 14px; border-radius: 8px; font-size: 13px;
}}
.param b {{ color: #7c9aff; }}
.btn-download {{
    display: inline-flex; align-items: center; gap: 8px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff; border: none; padding: 12px 32px; border-radius: 10px;
    font-size: 15px; font-weight: 500; cursor: pointer;
    transition: transform 0.15s, box-shadow 0.15s;
    text-decoration: none;
}}
.btn-download:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102,126,234,0.4);
}}
.btn-download:active {{ transform: translateY(0); }}
.btn-download svg {{ width: 18px; height: 18px; }}
</style>
</head>
<body>
<div class="container">
    <h2>APNG 动画预览</h2>
    <p class="subtitle">{info['filename']}</p>
    <div class="preview-area">
        <img src="data:image/png;base64,{b64}" alt="APNG 动画">
    </div>
    <div class="params">
        <div class="param">帧数 <b>{info['frames']}</b></div>
        <div class="param">帧率 <b>{info['fps']} FPS</b></div>
        <div class="param">尺寸 <b>{info['width']}×{info['height']}</b></div>
        <div class="param">时长 <b>{info['duration']}s</b></div>
        <div class="param">循环 <b>{info['loops']}</b></div>
        <div class="param">大小 <b>{info['size_display']}</b></div>
    </div>
    <a class="btn-download" href="/download" download="{info['filename']}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        下载 APNG 文件
    </a>
</div>
</body>
</html>'''
    return html


def main():
    parser = argparse.ArgumentParser(description='APNG 预览服务器')
    parser.add_argument('apng_file', help='APNG 文件路径')
    parser.add_argument('--port', type=int, default=8767, help='端口号，默认 8767')
    args = parser.parse_args()

    if not os.path.exists(args.apng_file):
        print(f"Error: 文件不存在: {args.apng_file}", file=sys.stderr)
        sys.exit(1)

    info = get_apng_info(args.apng_file)
    if not info:
        print(f"Error: 无法解析 APNG 文件: {args.apng_file}", file=sys.stderr)
        sys.exit(1)

    html_content = generate_html(args.apng_file, info).encode()
    apng_data = open(args.apng_file, 'rb').read()
    download_filename = info['filename']

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html_content)
            elif self.path == '/download':
                self.send_response(200)
                self.send_header('Content-type', 'image/apng')
                self.send_header('Content-Disposition', f'attachment; filename="{download_filename}"')
                self.send_header('Content-Length', str(len(apng_data)))
                self.end_headers()
                self.wfile.write(apng_data)
            else:
                self.send_error(404)

        def log_message(self, format, *args):
            pass

    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    with ReusableTCPServer(("", args.port), Handler) as httpd:
        url = f"http://localhost:{args.port}"
        print(f"预览服务已启动: {url}")
        print(f"APNG 文件: {args.apng_file}")
        print(f"帧数: {info['frames']}, 帧率: {info['fps']} FPS, 大小: {info['size_display']}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务已停止")


if __name__ == '__main__':
    main()
