#!/usr/bin/env python3
"""
decompose.py - APNG/GIF → PNG 序列帧

用法:
    python3 decompose.py input.apng [output_dir]
    python3 decompose.py input.gif [output_dir]
"""

import argparse
import os
import sys
import struct
import shutil
import zipfile


def decompose_apng(apng_path, output_dir):
    """拆解 APNG 为 PNG 序列帧"""
    print(f"📂 拆解 APNG: {os.path.basename(apng_path)}")

    with open(apng_path, 'rb') as f:
        sig = f.read(8)
        if sig != b'\x89PNG\r\n\x1a\n':
            print("❌ 不是有效的 PNG/APNG 文件")
            sys.exit(1)

        # 解析 chunk
        ihdr = None
        actl = None
        frames = []
        idat_data = b''
        current_seq = 0

        while True:
            length_bytes = f.read(4)
            if len(length_bytes) == 0:
                break
            length = struct.unpack('>I', length_bytes)[0]
            chunk_type = f.read(4)
            data = f.read(length)
            crc = f.read(4)

            if chunk_type == b'IHDR':
                w, h, bd, ct, comp, filt, inter = struct.unpack('>IIBBBBB', data)
                ihdr = {'w': w, 'h': h, 'bd': bd, 'ct': ct}
                print(f"  尺寸: {w}x{h}")
            elif chunk_type == b'acTL':
                num_frames, num_plays = struct.unpack('>II', data)
                actl = {'frames': num_frames, 'plays': num_plays}
                print(f"  帧数: {num_frames}, 循环: {num_plays if num_plays > 0 else '无限'}")
            elif chunk_type == b'fcTL':
                seq, w, h, xo, yo, dn, dd, dis, blend = struct.unpack('>IIIIIHHBB', data)
                delay_ms = int(dn / dd * 1000) if dd > 0 else 100
                frames.append({
                    'seq': seq,
                    'fcTL': {'w': w, 'h': h, 'delay_ms': delay_ms, 'dispose': dis, 'blend': blend},
                    'data': b''
                })
            elif chunk_type == b'IDAT':
                if frames:
                    frames[-1]['data'] += data
                else:
                    idat_data += data
            elif chunk_type == b'fdAT':
                seq = struct.unpack('>I', data[:4])[0]
                if frames:
                    frames[-1]['data'] += data[4:]

        if not actl:
            print("❌ 这不是 APNG 文件（缺少 acTL chunk）")
            sys.exit(1)

    # 解压每帧数据并保存为 PNG
    import zlib

    os.makedirs(output_dir, exist_ok=True)
    print(f"  输出目录: {output_dir}")

    for i, frame in enumerate(frames):
        frame_data = frame['data']
        if not frame_data:
            print(f"  ⚠️  帧 {i+1} 无数据，跳过")
            continue

        try:
            raw = zlib.decompress(frame_data)
        except Exception:
            print(f"  ⚠️  帧 {i+1} 解压失败")
            continue

        out_path = os.path.join(output_dir, f"frame_{i+1:04d}.png")
        try:
            import png
            w = ihdr['w']
            h = ihdr['h']
            has_alpha = (ihdr['ct'] in [4, 6])

            rows = []
            idx = 0
            bytes_per_pixel = 4 if has_alpha else 3
            row_size = 1 + w * bytes_per_pixel
            for y in range(h):
                if idx + row_size > len(raw):
                    break
                row = []
                for x in range(w):
                    px_idx = idx + 1 + x * bytes_per_pixel
                    if has_alpha:
                        row.extend(raw[px_idx:px_idx+4])
                    else:
                        row.extend(raw[px_idx:px_idx+3])
                rows.append(row)
                idx += row_size

            if has_alpha:
                writer = png.Writer(w, h, greyscale=False, alpha=True, bitdepth=8)
            else:
                writer = png.Writer(w, h, greyscale=False, alpha=False, bitdepth=8)
            with open(out_path, 'wb') as out:
                writer.write(out, rows)
            print(f"  ✅ 帧 {i+1}: {os.path.basename(out_path)}")
        except Exception as e:
            print(f"  ⚠️  帧 {i+1} 保存失败: {e}")

    print(f"\n✅ 共导出 {len(frames)} 帧到: {output_dir}")
    return output_dir


def decompose_gif(gif_path, output_dir):
    """拆解 GIF 为 PNG 序列帧（使用 Pillow，无需 imageio）"""
    print(f"📂 拆解 GIF: {os.path.basename(gif_path)}")
    
    try:
        from PIL import Image, ImageSequence
    except ImportError:
        print("❌ 缺少 Pillow 库")
        print("   请运行: pip install Pillow")
        sys.exit(1)
    
    try:
        gif = Image.open(gif_path)
        frames = []
        
        # 使用 ImageSequence.Iterator 遍历所有帧
        for i, frame in enumerate(ImageSequence.Iterator(gif)):
            frames.append(frame.copy())
        
        print(f"  总帧数: {len(frames)}")
        print(f"  尺寸: {frames[0].size[0]} x {frames[0].size[1]}")
        
        os.makedirs(output_dir, exist_ok=True)
        print(f"  输出目录: {output_dir}")
        
        for i, frame in enumerate(frames):
            out_path = os.path.join(output_dir, f"frame_{i+1:04d}.png")
            # 转换为 RGBA 以保留透明通道
            if frame.mode != 'RGBA':
                frame = frame.convert('RGBA')
            frame.save(out_path, 'PNG')
            if (i + 1) % 10 == 0 or i == len(frames) - 1:
                print(f"  已处理 {i+1}/{len(frames)} 帧")
        
        print(f"\n✅ 共导出 {len(frames)} 帧到: {output_dir}")
        return output_dir
        
    except Exception as e:
        print(f"❌ GIF 拆解失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='APNG/GIF → PNG 序列帧')
    parser.add_argument('input', help='输入的 APNG/GIF 文件路径')
    parser.add_argument('output_dir', nargs='?', help='输出目录（默认桌面）')
    args = parser.parse_args()

    # 默认输出到桌面
    if not args.output_dir:
        base = os.path.splitext(os.path.basename(args.input))[0]
        args.output_dir = os.path.join(os.path.expanduser('~'), 'Desktop', f"{base}_frames")

    # 确保输出目录存在（工作空间路径用 os.makedirs，桌面路径需由调用方预先创建）
    try:
        os.makedirs(args.output_dir, exist_ok=True)
    except PermissionError:
        if not os.path.exists(args.output_dir):
            print(f"❌ 输出目录不存在，请先创建: {args.output_dir}")
            print("   （桌面目录需由 Bash 工具预先创建）")
            sys.exit(1)

    ext = os.path.splitext(args.input)[1].lower()

    # 检查是否为 APNG（含 .png 扩展名）
    def is_apng(path):
        try:
            with open(path, 'rb') as f:
                sig = f.read(8)
                if sig != b'\x89PNG\r\n\x1a\n':
                    return False
                while True:
                    length_bytes = f.read(4)
                    if len(length_bytes) < 4:
                        break
                    length = struct.unpack('>I', length_bytes)[0]
                    chunk_type = f.read(4)
                    if chunk_type == b'acTL':
                        return True
                    f.read(length + 4)
            return False
        except Exception:
            return False

    if ext in ['.apng', '.png'] and is_apng(args.input):
        decompose_apng(args.input, args.output_dir)
    elif ext == '.gif':
        decompose_gif(args.input, args.output_dir)
    else:
        print(f"❌ 不支持的文件格式: {ext}")
        print("   支持: .apng, .png(APNG), .gif")
        sys.exit(1)

    print(f"\n📁 序列帧已保存到: {args.output_dir}")


if __name__ == '__main__':
    main()
