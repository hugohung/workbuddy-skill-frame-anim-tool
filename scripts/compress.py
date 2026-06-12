#!/usr/bin/env python3
"""
compress.py - APNG/GIF 压缩

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


def compress_apng(input_path, output_path, quality=80):
    """压缩 APNG：降低 zlib 压缩质量"""
    print(f"🗜️  压缩 APNG: {os.path.basename(input_path)}")
    print(f"  质量: {quality}%")

    with open(input_path, 'rb') as f:
        sig = f.read(8)
        if sig != b'\x89PNG\r\n\x1a\n':
            print("❌ 不是有效的 PNG/APNG 文件")
            sys.exit(1)

        chunks = []
        actl = None
        while True:
            length_bytes = f.read(4)
            if len(length_bytes) == 0: break
            length = struct.unpack('>I', length_bytes)[0]
            chunk_type = f.read(4)
            data = f.read(length)
            crc = f.read(4)
            chunks.append((chunk_type, data))
            if chunk_type == b'acTL':
                num_frames = struct.unpack('>I', data[:4])[0]
                actl = {'frames': num_frames}

    if not actl:
        print("⚠️  这不是 APNG 文件，跳过压缩")
        return

    compress_level = quality_to_compress_level(quality)
    with open(output_path, 'wb') as out:
        out.write(sig)
        for chunk_type, data in chunks:
            if chunk_type == b'IDAT' or chunk_type == b'fdAT':
                if chunk_type == b'fdAT':
                    seq = data[:4]
                    raw_data = zlib.decompress(data[4:])
                    new_data = seq + zlib.compress(raw_data, compress_level)
                else:
                    raw_data = zlib.decompress(data)
                    new_data = zlib.compress(raw_data, compress_level)
                _write_chunk(out, chunk_type, new_data)
            else:
                _write_chunk(out, chunk_type, data)

    orig_size = os.path.getsize(input_path)
    new_size = os.path.getsize(output_path)
    ratio = (1 - new_size / orig_size) * 100
    print(f"  ✅ 压缩完成")
    print(f"  原大小: {orig_size/1024:.1f} KB")
    print(f"  新大小: {new_size/1024:.1f} KB")
    print(f"  压缩比: {ratio:.1f}%")


def compress_gif(input_path, output_path, colors=None):
    """压缩 GIF：调用 gifsicle（直接操作二进制结构，只减色）

    - 减色：调用 gifsicle --colors（快，无乱码）
    - 不支持减帧（已移除）
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
    parser = argparse.ArgumentParser(description='APNG/GIF 压缩')
    parser.add_argument('input', help='输入的 APNG/GIF 文件路径')
    parser.add_argument('output', nargs='?', help='输出路径（默认加 _compressed）')
    parser.add_argument('--info', action='store_true', help='只检测文件信息，不压缩')
    parser.add_argument('--colors', type=int, help='GIF 色数（32/64/128/256）')
    parser.add_argument('--quality', type=int, default=80, help='APNG 画质 1-100（默认 80）')
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
        args.output = f"{base}_compressed{ext}"

    if ext == '.gif':
        compress_gif(args.input, args.output, colors=args.colors)
    elif ext in ['.apng', '.png']:
        info = detect_apng_info(args.input)
        if info.get('frames'):
            compress_apng(args.input, args.output, quality=args.quality)
        else:
            print("⚠️  这不是 APNG，跳过压缩")
    else:
        print(f"❌ 不支持的文件格式: {ext}")
        sys.exit(1)

    print(f"\n✅ 输出: {args.output}")


if __name__ == '__main__':
    main()
