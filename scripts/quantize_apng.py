#!/usr/bin/env python3
"""
quantize_apng.py - APNG 颜色量化（使用系统 Python）
参考 Tinify 原理：将 24 位 APNG 转换为 8 位索引色
"""

import argparse
import os
import sys
import subprocess
import tempfile
import shutil
import zipfile
from PIL import Image, ImageSequence

def quantize_apng(input_path, output_path, colors=256):
    """量化 APNG 颜色"""
    print(f"🎨 开始量化 APNG...")
    print(f"  输入: {input_path}")
    print(f"  输出: {output_path}")
    print(f"  目标色数: {colors}")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="apng_quant_")
    frames_dir = os.path.join(temp_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    try:
        # 1. 打开 APNG
        print("  📂 读取 APNG 帧...")
        apng = Image.open(input_path)
        frames = []
        durations = []
        
        for i, frame in enumerate(ImageSequence.Iterator(apng)):
            frames.append(frame.copy())
            # 获取帧持续时间
            if hasattr(apng, 'info') and 'duration' in apng.info:
                durations.append(apng.info['duration'])
        
        if not durations:
            durations = [100] * len(frames)  # 默认 100ms
        
        print(f"  总帧数: {len(frames)}")
        print(f"  帧尺寸: {frames[0].size}")
        
        # 2. 量化每一帧
        print(f"  🎨 量化颜色（{colors} 色）...")
        
        for i, frame in enumerate(frames):
            # 转换为 RGBA
            if frame.mode != 'RGBA':
                frame = frame.convert('RGBA')
            
            # 量化颜色（RGBA 需要用 FASTOCTREE 方法）
            if colors < 256:
                quantized = frame.quantize(colors=colors, method=Image.FASTOCTREE)
                quantized = quantized.convert('RGBA')
            else:
                quantized = frame
            
            # 保存为临时 PNG
            frame_path = os.path.join(frames_dir, f"frame_{i:04d}.png")
            quantized.save(frame_path, 'PNG')
            
            if (i + 1) % 10 == 0 or i == len(frames) - 1:
                print(f"  已处理 {i+1}/{len(frames)} 帧")
        
        # 3. 打包成 zip 文件
        print("  📦 打包帧文件...")
        frames_zip = os.path.join(temp_dir, "frames.zip")
        with zipfile.ZipFile(frames_zip, 'w') as zf:
            for i in range(len(frames)):
                frame_path = os.path.join(frames_dir, f"frame_{i:04d}.png")
                zf.write(frame_path, f"frame_{i:04d}.png")
        
        # 4. 重新合成 APNG
        print("  🎬 重新合成 APNG...")
        
        # 计算 FPS（使用第一帧的持续时间）
        avg_duration = sum(durations) / len(durations)
        fps = int(1000 / avg_duration) if avg_duration > 0 else 15
        
        compose_script = os.path.join(os.path.dirname(__file__), "compose.py")
        
        # 使用托管 Python 运行 compose.py（需要 pypng）
        compose_cmd = [
            "/Users/honghaoxiang/.workbuddy/binaries/python/envs/png2apng3/bin/python3",
            compose_script,
            frames_zip,
            output_path,
            "--format", "apng",
            "--fps", str(fps),
            "--loops", "0"
        ]
        
        result = subprocess.run(compose_cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"❌ 合成失败:")
            print(result.stderr)
            sys.exit(1)
        
        # 5. 输出结果
        orig_size = os.path.getsize(input_path)
        new_size = os.path.getsize(output_path)
        ratio = (1 - new_size / orig_size) * 100
        
        print(f"")
        print(f"✅ 量化完成!")
        print(f"  原大小: {orig_size/1024:.1f} KB")
        print(f"  新大小: {new_size/1024:.1f} KB")
        print(f"  压缩比: {ratio:.1f}%")
        
    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description='APNG 颜色量化')
    parser.add_argument('input', help='输入的 APNG 文件')
    parser.add_argument('output', help='输出的 APNG 文件')
    parser.add_argument('--colors', type=int, default=256, help='目标色数（默认 256）')
    args = parser.parse_args()
    
    quantize_apng(args.input, args.output, colors=args.colors)


if __name__ == '__main__':
    main()
