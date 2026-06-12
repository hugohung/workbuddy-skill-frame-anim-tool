#!/usr/bin/env python3
"""
compress.py - APNG/GIF 压缩（支持颜色量化）

用法:
    python3 compress.py input.gif [--info]           # 检测信息
    python3 compress.py input.gif output.gif [...]     # 压缩
    python3 compress.py input.apng [output.apng] [...] # 压缩 APNG
"""

import argparse
import os
import sys
import struct
import zlib
import subprocess
import tempfile
import shutil
from PIL import Image, ImageSequence

def quality_to_compress_level(q):
    """将质量百分比映射为 zlib 压缩级别"""
    if q >= 95: return 1
    elif q >= 80: return 3
    elif q >= 60: return 6
    elif q >= 40: return 7
    else: return 9


def detect_gif_info(gif_path):
    """用 gifsicle -I 检测 GIF 信息（色数、帧数、尺寸）"""
    gifsicle = "/Users/honghaoxiang/.workbuddy/binaries/node/workspace/node_modules/gifsicle/vendor/gifsicle"
    try:
        result = subprocess.run([gifsicle, "-I", gif_path],
                               capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
    except Exception as e:
        return {"error": str(e)}

    info = {"path": gif_path, "colors": None, "frames": None,
            "width": None, "height": None, "has_transparency": False}

    for line in output.splitlines():
        if " images" in line and line.strip().startswith("*"):
            try:
                parts = line.strip().split()
                info["frames"] = int(parts[2])
            except: pass
        if "logical screen" in line:
            try:
                wh = line.split("logical screen")[1].strip()
                w, h = wh.split("x")
                info["width"] = int(w)
                info["height"] = int(h)
            except: pass
        if "global color table" in line:
            try:
                c = line.split("[")[1].split("]")[0]
                info["colors"] = int(c)
            except: pass
        if "transparent" in line:
            info["has_transparency"] = True

    return info


def detect_apng_info(apng_path):
    """检测 APNG 信息"""
    info = {"path": apng_path, "colors": None, "frames": None,
            "width": None, "height": None, "has_transparency": False}
    try:
        with open(apng_path, 'rb') as f:
            sig = f.read(8)
            if sig != b'\x89PNG\r\n\x1a\n':
                return info
            while True:
                length_bytes = f.read(4)
                if len(length_bytes) < 4: break
                length = struct.unpack('>I', length_bytes)[0]
                chunk_type = f.read(4)
                data = f.read(length)
                f.read(4)
                if chunk_type == b'IHDR':
                    w, h = struct.unpack('>II', data[:8])
                    ct = data[8]
                    info["width"] = w
                    info["height"] = h
                    info["has_transparency"] = (ct in [4, 6])
                elif chunk_type == b'acTL':
                    num_frames = struct.unpack('>I', data[:4])[0]
                    info["frames"] = num_frames
    except: pass
    return info


def print_info(info):
    """打印文件信息"""
    print(f"📊 文件信息: {os.path.basename(info['path'])}")
    if info.get("error"):
        print(f"  ❌ {info['error']}")
        return
    if info['width']:
        print(f"  尺寸: {info['width']} x {info['height']}")
    if info['frames']:
        print(f"  帧数: {info['frames']}")
    if info.get('colors') and isinstance(info['colors'], int):
        print(f"  色数: {info['colors']}")
    print(f"  透明通道: {'是' if info['has_transparency'] else '否'}")


def quantize_apng(input_path, output_path, colors=256):
    """量化 APNG 颜色（参考 Tinify 原理）
    
    将 24 位 APNG 转换为 8 位索引色 APNG，大幅减小文件体积
    使用系统 Python（避免托管 Python 的代码签名问题）
    """
    print(f"🗜️  量化 APNG: {os.path.basename(input_path)}")
    print(f"  目标色数: {colors}")
    
    # 使用系统 Python 运行量化脚本
    script_path = os.path.join(os.path.dirname(__file__), "quantize_apng.py")
    
    if not os.path.exists(script_path):
        print(f"❌ 量化脚本未找到: {script_path}")
        print(f"   请先创建 quantize_apng.py")
        sys.exit(1)
    
    cmd = ["/usr/bin/python3", script_path, input_path, output_path, "--colors", str(colors)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    
    if result.returncode != 0:
        print(f"❌ 量化失败:")
        print(result.stderr)
        sys.exit(1)
    
    # 输出量化结果
    orig_size = os.path.getsize(input_path)
    new_size = os.path.getsize(output_path)
    ratio = (1 - new_size / orig_size) * 100
    
    print(f"  ✅ 量化完成")
    print(f"  原大小: {orig_size/1024:.1f} KB")
    print(f"  新大小: {new_size/1024:.1f} KB")
    if abs(ratio) > 0.5:
        print(f"  压缩比: {ratio:.1f}%")


def compress_apng(input_path, output_path, quality=80, colors=None):
    """压缩 APNG
    
    - colors: 指定目标色数（如 256, 128, 64），实现颜色量化
    - quality: zlib 压缩质量（1-100）
    """
    # 如果指定了 colors，使用量化方法（效果更好）
    if colors and colors < 256:
        quantize_apng(input_path, output_path, colors=colors)
        return
    
    # 否则只调整 zlib 压缩级别
    print(f"🗜️  压缩 APNG: {os.path.basename(input_path)}")
    print(f"  质量: {quality}%")

    with open(input_path, 'rb') as f:
        sig = f.read(8)
        if sig != b'\x89PNG\r\n\x1a\n':
            print("❌ 不是有效的 PNG/APNG 文件")
            sys.exit(1)

        # 读取所有 chunk
        chunks = []
        while True:
            length_bytes = f.read(4)
            if not length_bytes:
                break
            length = struct.unpack('>I', length_bytes)[0]
            chunk_type = f.read(4)
            data = f.read(length)
            crc = f.read(4)
            chunks.append((chunk_type, data))

    # 检查是否是 APNG
    is_apng = any(ct == b'acTL' for ct, _ in chunks)
    if not is_apng:
        print("⚠️  这不是 APNG 文件，跳过压缩")
        return

    compress_level = quality_to_compress_level(quality)

    # 重新构建 APNG，正确重新压缩数据块
    new_chunks = []
    next_seq = 0  # 全局序列号（fcTL 和 fdAT 共享）

    i = 0
    while i < len(chunks):
        ct, data = chunks[i]

        if ct == b'fcTL':
            # fcTL：更新序列号，保留其他数据
            new_data = struct.pack('>I', next_seq) + data[4:]
            new_chunks.append((b'fcTL', new_data))
            next_seq += 1
            i += 1

        elif ct == b'IDAT':
            # 拼接所有连续的 IDAT chunk 数据（属于同一个 zlib 流）
            all_data = b''
            while i < len(chunks) and chunks[i][0] == b'IDAT':
                all_data += chunks[i][1]
                i += 1

            # 解压 → 重新压缩
            raw = zlib.decompress(all_data)
            new_compressed = zlib.compress(raw, compress_level)

            # 拆分回 65535 字节的 chunk
            for j in range(0, len(new_compressed), 65535):
                new_chunks.append((b'IDAT', new_compressed[j:j+65535]))

        elif ct == b'fdAT':
            # 拼接所有连续的 fdAT chunk 数据（跳过每个 chunk 前 4 字节的序列号）
            all_data = b''
            while i < len(chunks) and chunks[i][0] == b'fdAT':
                all_data += chunks[i][1][4:]  # 跳过序列号
                i += 1

            # 解压 → 重新压缩
            raw = zlib.decompress(all_data)
            new_compressed = zlib.compress(raw, compress_level)

            # 拆分回 chunk，加上新的序列号
            for j in range(0, len(new_compressed), 65535):
                seq_bytes = struct.pack('>I', next_seq)
                next_seq += 1
                new_chunks.append((b'fdAT', seq_bytes + new_compressed[j:j+65535]))

        else:
            # 其他 chunk 原样保留
            new_chunks.append((ct, data))
            i += 1

    # 写入新文件
    with open(output_path, 'wb') as out:
        out.write(sig)
        for ct, data in new_chunks:
            _write_chunk(out, ct, data)

    orig_size = os.path.getsize(input_path)
    new_size = os.path.getsize(output_path)
    ratio = (1 - new_size / orig_size) * 100
    print(f"  ✅ 压缩完成")
    print(f"  原大小: {orig_size/1024:.1f} KB")
    print(f"  新大小: {new_size/1024:.1f} KB")
    if abs(ratio) > 0.5:
        print(f"  压缩比: {ratio:.1f}%")


def compress_gif(input_path, output_path, colors=None):
    """压缩 GIF：调用 gifsicle（直接操作二进制结构，只减色）
    """
    print(f"🗜️  压缩 GIF: {os.path.basename(input_path)}")

    gifsicle = "/Users/honghaoxiang/.workbuddy/binaries/node/workspace/node_modules/gifsicle/vendor/gifsicle"

    if not os.path.exists(gifsicle):
        print(f"❌ gifsicle 未找到: {gifsicle}")
        print(f"   请运行: npm install gifsicle")
        sys.exit(1)

    cmd = [gifsicle, "--optimize=3"]
    if colors:
        cmd.extend(["--colors", str(colors)])
        print(f"  色数: {colors}")
    cmd.extend(["-o", output_path, input_path])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ gifsicle 执行失败:")
        print(result.stderr)
        sys.exit(1)

    orig_size = os.path.getsize(input_path)
    new_size = os.path.getsize(output_path)
    ratio = (1 - new_size / orig_size) * 100 if orig_size > 0 else 0
    print(f"  ✅ 压缩完成")
    print(f"  原大小: {orig_size/1024:.1f} KB")
    print(f"  新大小: {new_size/1024:.1f} KB")
    if abs(ratio) > 0.5:
        print(f"  压缩比: {ratio:.1f}%")


def _write_chunk(f, chunk_type, data):
    """写 PNG chunk（含 CRC）"""
    f.write(struct.pack('>I', len(data)))
    f.write(chunk_type)
    f.write(data)
    crc = 0xFFFFFFFF
    for b in chunk_type + data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
    f.write(struct.pack('>I', 0xFFFFFFFF & ~crc))


def main():
    parser = argparse.ArgumentParser(description='APNG/GIF 压缩（支持颜色量化）')
    parser.add_argument('input', help='输入的 APNG/GIF 文件路径')
    parser.add_argument('output', nargs='?', help='输出路径（默认加 _compressed）')
    parser.add_argument('--info', action='store_true', help='只检测文件信息，不压缩')
    parser.add_argument('--colors', type=int, help='颜色量化（APNG/GIF 通用，如 256/128/64）')
    parser.add_argument('--quality', type=int, default=80, help='APNG zlib 画质 1-100（默认 80）')
    args = parser.parse_args()

    ext = os.path.splitext(args.input)[1].lower()

    # --info 模式：只检测信息
    if args.info:
        if ext == '.gif':
            info = detect_gif_info(args.input)
        elif ext in ['.apng', '.png']:
            info = detect_apng_info(args.input)
        else:
            print(f"❌ 不支持的文件格式: {ext}")
            sys.exit(1)
        print_info(info)
        return

    # 压缩模式
    if not args.output:
        base = os.path.splitext(args.input)[0]
        suffix = f"_c{args.colors}" if args.colors else "_compressed"
        args.output = f"{base}{suffix}{ext}"

    if ext == '.gif':
        compress_gif(args.input, args.output, colors=args.colors)
    elif ext in ['.apng', '.png']:
        info = detect_apng_info(args.input)
        if info.get('frames'):
            compress_apng(args.input, args.output, quality=args.quality, colors=args.colors)
        else:
            print("⚠️  这不是 APNG，跳过压缩")
    else:
        print(f"❌ 不支持的文件格式: {ext}")
        sys.exit(1)

    print(f"\n✅ 输出: {args.output}")


if __name__ == '__main__':
    main()
