#!/usr/bin/env python3
"""
compose.py - PNG 序列帧 → APNG / GIF

用法:
    python3 compose.py input.zip output [--format apng] [--fps 15] [--loops 0] [--quality 100]
"""

import argparse
import os
import sys
import subprocess
import zipfile
import shutil


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = '/Users/honghaoxiang/.workbuddy/binaries/python/envs/png2apng3/bin/python3'
NODE = '/Users/honghaoxiang/.workbuddy/binaries/node/versions/22.22.2/bin/node'
NODE_MODULES = '/Users/honghaoxiang/.workbuddy/binaries/node/workspace/node_modules'


def extract_frames(zip_path, extract_to):
    """解压 zip 中的 PNG 帧，返回排序后的路径列表"""
    if os.path.exists(extract_to):
        shutil.rmtree(extract_to)
    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        png_names = sorted([
            f for f in zf.namelist()
            if f.lower().endswith('.png') and not f.startswith('__MACOSX')
        ])
        if not png_names:
            print("❌ 未在压缩包中找到 PNG 文件")
            sys.exit(1)
        for name in png_names:
            safe_name = os.path.basename(name)
            dest = os.path.join(extract_to, safe_name)
            with zf.open(name) as src, open(dest, 'wb') as dst:
                shutil.copyfileobj(src, dst)
    frames = sorted([
        os.path.join(extract_to, f) for f in os.listdir(extract_to)
        if f.lower().endswith('.png')
    ])
    return frames


def compose_apng(frames, output_path, fps=15, loops=0, quality=100):
    """合成 APNG（调用已验证的 png2apng.py）"""
    tmp_zip = '/tmp/_compose_tmp.zip'
    with zipfile.ZipFile(tmp_zip, 'w') as zf:
        for f in frames:
            zf.write(f, os.path.basename(f))

    cmd = [PYTHON, os.path.join(SCRIPT_DIR, 'png2apng.py'),
            tmp_zip, output_path,
            '--fps', str(fps),
            '--loops', str(loops),
            '--quality', str(quality)]
    print(f"  调用: png2apng.py")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ APNG 合成失败:\n{result.stderr}")
        sys.exit(1)
    for line in result.stdout.strip().split('\n'):
        if line.strip():
            print(f"  {line}")
    return output_path


def compose_gif(frames, output_path, fps=15, loops=0, quality=100):
    """合成 GIF（调用 Node.js gif-encoder-2 + jimp）"""
    delay = round(1000 / fps)

    node_script = f"""
const GIFEncoder = require('{NODE_MODULES}/gif-encoder-2');
const {{ Jimp }} = require('{NODE_MODULES}/jimp');
const fs = require('fs');

const frames = {json.dumps(frames)};
const delay = {delay};
const loops = {loops};
const quality = {quality};

async function main() {{
  const firstImg = await Jimp.read(frames[0]);
  const width = firstImg.bitmap.width;
  const height = firstImg.bitmap.height;

  const encoder = new GIFEncoder(width, height);
  encoder.start();
  encoder.setRepeat(loops === 0 ? 0 : loops);
  encoder.setDelay(delay);
  encoder.setQuality(Math.max(1, Math.round((100 - quality) / 10)));

  for (const f of frames) {{
    const img = await Jimp.read(f);
    const rgba = Buffer.from(img.bitmap.data);
    encoder.addFrame(rgba);
  }}

  encoder.finish();
  const output = encoder.out?.data;
  const buffer = Buffer.isBuffer(output) ? output : Buffer.from(output);
  fs.writeFileSync('{output_path}', buffer);
  console.log('GIF saved:', '{os.path.basename(output_path)}');
  console.log('Size:', (buffer.length / 1024).toFixed(1), 'KB');
}}

main().catch(e => {{ console.error(e.message || e); process.exit(1); }});
"""

    tmp_js = '/tmp/_compose_gif.js'
    with open(tmp_js, 'w') as f:
        f.write(node_script)

    print(f"  调用 Node.js 合成 GIF...")
    result = subprocess.run([NODE, tmp_js], capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"❌ GIF 合成失败:\n{result.stderr}")
        sys.exit(1)
    for line in result.stdout.strip().split('\n'):
        if line.strip():
            print(f"  {line}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description='PNG 序列帧 → APNG/GIF')
    parser.add_argument('input', help='输入的 zip 文件路径')
    parser.add_argument('output', help='输出文件路径（自动加扩展名）')
    parser.add_argument('--format', choices=['apng', 'gif'],
                        default='apng', help='输出格式')
    parser.add_argument('--fps', type=int, default=15, help='帧率（默认 15）')
    parser.add_argument('--loops', type=int, default=0, help='循环次数，0=无限（默认 0）')
    parser.add_argument('--quality', type=int, default=100, help='质量 1-100（默认 100）')
    args = parser.parse_args()

    # 解压帧
    print(f"📦 解压: {args.input}")
    frame_dir = '/tmp/_compose_frames'
    frames = extract_frames(args.input, frame_dir)
    print(f"  找到 {len(frames)} 帧")

    # 确定输出路径
    if not any(args.output.endswith(ext) for ext in ['.apng', '.gif']):
        ext_map = {'apng': '.apng', 'gif': '.gif'}
        output_path = args.output + ext_map[args.format]
    else:
        output_path = args.output

    print(f"\n🎬 合成 {args.format.upper()}:")
    print(f"  帧率: {args.fps} FPS")
    print(f"  循环: {'无限' if args.loops == 0 else str(args.loops) + ' 次'}")
    print(f"  质量: {args.quality}%")

    # 根据格式调用不同函数
    if args.format == 'apng':
        compose_apng(frames, output_path, args.fps, args.loops, args.quality)
    elif args.format == 'gif':
        compose_gif(frames, output_path, args.fps, args.loops, args.quality)

    size = os.path.getsize(output_path)
    print(f"\n✅ 完成! 输出: {output_path}")
    print(f"   大小: {size/1024:.1f} KB")
    return output_path


if __name__ == '__main__':
    main()
