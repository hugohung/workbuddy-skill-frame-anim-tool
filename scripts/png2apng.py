#!/usr/bin/env python3
"""
PNG Sequence to APNG Converter (Pure Python)

将 PNG 序列帧合成为 APNG 动画文件。
支持从 zip 压缩包中提取 PNG 帧，按文件名排序后合成。
纯 Python 实现，不依赖 Pillow 等含 C 扩展的库。

用法:
    python png2apng.py input.zip output.apng [--fps 15] [--loops 0] [--quality 100]

参数:
    input       输入的 zip 文件路径（包含 PNG 序列帧）
    output      输出的 APNG 文件路径
    --fps       帧率（每秒帧数），默认 15，推荐 10-30
    --loops     循环次数，0 表示无限循环，默认 0
    --quality   压缩质量 1-100，默认 100（无损），推荐 70-100
                质量越高图片越清晰，但文件越大
                （注：PNG 为无损压缩，此参数映射到压缩级别）
"""

import argparse
import os
import sys
import zipfile
import tempfile
import shutil
import struct
import zlib
import io

try:
    import png
except ImportError:
    print("Error: pypng is required. Install with: pip install pypng", file=sys.stderr)
    sys.exit(1)

PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'


def write_chunk(f, chunk_type, data):
    """写入一个 PNG chunk（含长度、类型、数据、CRC）"""
    f.write(struct.pack('>I', len(data)))
    f.write(chunk_type)
    f.write(data)
    crc = zlib.crc32(chunk_type + data) & 0xffffffff
    f.write(struct.pack('>I', crc))


def read_png_chunks(filepath):
    """读取 PNG 文件的所有原始 chunks"""
    chunks = []
    with open(filepath, 'rb') as f:
        sig = f.read(8)
        if sig != PNG_SIGNATURE:
            raise ValueError(f"Not a valid PNG file: {filepath}")
        while True:
            length_bytes = f.read(4)
            if len(length_bytes) == 0:
                break
            length = struct.unpack('>I', length_bytes)[0]
            chunk_type = f.read(4)
            data = f.read(length)
            crc = struct.unpack('>I', f.read(4))[0]
            # 验证 CRC
            expected_crc = zlib.crc32(chunk_type + data) & 0xffffffff
            if crc != expected_crc:
                print(f"Warning: CRC mismatch in {filepath}, chunk {chunk_type!r}", file=sys.stderr)
            chunks.append((chunk_type, data))
    return chunks


def get_ihdr_info(chunks):
    """从 chunks 中提取 IHDR 信息"""
    for ctype, data in chunks:
        if ctype == b'IHDR':
            return struct.unpack('>IIBBBBB', data)
    return None


def is_rgba8(chunks):
    """检查是否为标准的非隔行 RGBA8 PNG"""
    info = get_ihdr_info(chunks)
    if info is None:
        return False
    width, height, bitdepth, colortype, compression, filter_method, interlace = info
    return bitdepth == 8 and colortype == 6 and interlace == 0


def encode_frame_to_png(pixel_rows, width, height):
    """用 pypng Writer 将像素数据编码为标准 RGBA8 PNG，返回字节数据"""
    buf = io.BytesIO()
    writer = png.Writer(width=width, height=height, alpha=True, bitdepth=8)
    writer.write(buf, pixel_rows)
    return buf.getvalue()


def read_chunks_from_bytes(data):
    """从 PNG 字节数据中解析所有 chunks"""
    chunks = []
    pos = 8  # skip PNG signature
    while pos < len(data):
        length = struct.unpack('>I', data[pos:pos + 4])[0]
        chunk_type = data[pos + 4:pos + 8]
        chunk_data = data[pos + 8:pos + 8 + length]
        crc = struct.unpack('>I', data[pos + 8 + length:pos + 12 + length])[0]
        expected = zlib.crc32(chunk_type + chunk_data) & 0xffffffff
        if crc != expected:
            print(f"Warning: CRC mismatch for chunk {chunk_type!r}", file=sys.stderr)
        chunks.append((chunk_type, chunk_data))
        pos += 12 + length
    return chunks


def get_idat_data(chunks):
    """从 chunks 中提取所有 IDAT 数据并拼接"""
    return b''.join(data for ctype, data in chunks if ctype == b'IDAT')


def extract_frames_from_zip(zip_path, extract_dir):
    """解压 zip 并提取所有 PNG 帧，按文件名排序后返回路径列表"""
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)

    frames = []
    for root, dirs, files in os.walk(extract_dir):
        for f in files:
            if f.lower().endswith('.png'):
                frames.append(os.path.join(root, f))
    frames.sort()
    return frames


def convert_to_rgba8(filepath):
    """将任意 PNG 转换为标准 RGBA8 格式，返回 (width, height, png_bytes)"""
    reader = png.Reader(filename=filepath)
    width, height, rows, info = reader.asDirect()
    pixel_rows = list(rows)

    # 重新编码为标准 RGBA8
    png_bytes = encode_frame_to_png(pixel_rows, width, height)
    return width, height, png_bytes


def create_apng(frame_paths, output_path, fps=15, loops=0, quality=100):
    """
    合成 APNG 动画

    支持两种模式：
    1. 所有帧都是标准 RGBA8 PNG → 直接搬运原始 IDAT 数据（最快）
    2. 帧格式不一致 → 通过 pypng 统一转换为 RGBA8 后合成
    """
    duration_ms = int(round(1000 / fps))
    delay_num = duration_ms
    delay_den = 1000

    # 第一步：读取所有帧的信息
    frame_chunks_list = []
    for path in frame_paths:
        try:
            chunks = read_png_chunks(path)
            frame_chunks_list.append(chunks)
        except Exception as e:
            raise ValueError(f"Failed to read {path}: {e}")

    # 检查是否所有帧都是 RGBA8
    all_rgba8 = all(is_rgba8(chunks) for chunks in frame_chunks_list)

    # 获取尺寸信息
    sizes = []
    for chunks in frame_chunks_list:
        info = get_ihdr_info(chunks)
        if info:
            sizes.append((info[0], info[1]))
        else:
            sizes.append((None, None))

    # 检查尺寸一致性
    first_size = sizes[0]
    size_mismatch = [s for s in sizes if s != first_size]
    if size_mismatch:
        print(f"Warning: Frame sizes are inconsistent. First frame: {first_size}, others: {set(size_mismatch)}", file=sys.stderr)
        print("Frames will be resized to match the first frame. This may affect quality.", file=sys.stderr)
        all_rgba8 = False  # 强制重新编码以统一尺寸

    # 准备帧数据：list of (width, height, idat_bytes)
    frame_idats = []

    if all_rgba8:
        # 快速路径：直接提取 IDAT
        for chunks in frame_chunks_list:
            idat_data = get_idat_data(chunks)
            frame_idats.append((first_size[0], first_size[1], idat_data))
    else:
        # 慢速路径：统一转换为 RGBA8
        max_width = max((s[0] for s in sizes if s[0] is not None), default=first_size[0])
        max_height = max((s[1] for s in sizes if s[1] is not None), default=first_size[1])

        for i, path in enumerate(frame_paths):
            width, height, png_bytes = convert_to_rgba8(path)

            # 如果尺寸不一致，需要处理
            if (width, height) != (max_width, max_height):
                # 重新读取并调整大小
                reader = png.Reader(bytes=png_bytes)
                w, h, rows, info = reader.asDirect()
                pixel_rows = list(rows)

                # 简单的居中裁剪/填充
                if width != max_width or height != max_height:
                    pixel_rows = resize_pixel_rows(pixel_rows, width, height, max_width, max_height)
                    # 重新编码
                    png_bytes = encode_frame_to_png(pixel_rows, max_width, max_height)

                chunks = read_chunks_from_bytes(png_bytes)
            else:
                chunks = read_chunks_from_bytes(png_bytes)

            idat_data = get_idat_data(chunks)
            frame_idats.append((max_width, max_height, idat_data))

        first_size = (max_width, max_height)

    # 写入 APNG 文件
    num_frames = len(frame_idats)
    out_width, out_height = first_size

    with open(output_path, 'wb') as f:
        # PNG 签名
        f.write(PNG_SIGNATURE)

        # IHDR
        ihdr_data = struct.pack('>IIBBBBB',
            out_width, out_height,
            8,   # bit depth
            6,   # color type: RGBA
            0,   # compression
            0,   # filter
            0)   # interlace
        write_chunk(f, b'IHDR', ihdr_data)

        # acTL（动画控制）
        actl_data = struct.pack('>II', num_frames, loops)
        write_chunk(f, b'acTL', actl_data)

        # 第一帧
        seq = 0
        fctl_data = struct.pack('>IIIIIHHBB',
            seq,           # sequence_number
            out_width,     # width
            out_height,    # height
            0,             # x_offset
            0,             # y_offset
            delay_num,     # delay_num
            delay_den,     # delay_den
            0,             # dispose_op: APNG_DISPOSE_OP_NONE
            0)             # blend_op: APNG_BLEND_OP_SOURCE
        write_chunk(f, b'fcTL', fctl_data)
        seq += 1

        # 第一帧数据（IDAT）
        # 需要分块（每块最大 65535 字节）
        idat = frame_idats[0][2]
        for i in range(0, len(idat), 65535):
            write_chunk(f, b'IDAT', idat[i:i + 65535])

        # 后续帧
        for frame_idx in range(1, num_frames):
            # fcTL
            fctl_data = struct.pack('>IIIIIHHBB',
                seq, out_width, out_height, 0, 0,
                delay_num, delay_den, 0, 0)
            write_chunk(f, b'fcTL', fctl_data)
            seq += 1

            # fdAT（帧数据）
            idat = frame_idats[frame_idx][2]
            for i in range(0, len(idat), 65535):
                chunk_data = struct.pack('>I', seq) + idat[i:i + 65535]
                write_chunk(f, b'fdAT', chunk_data)
                seq += 1

        # IEND
        write_chunk(f, b'IEND', b'')

    return {
        'frame_count': num_frames,
        'fps': fps,
        'duration_ms': duration_ms,
        'total_duration_s': round(num_frames * duration_ms / 1000, 2),
        'loops': 'infinite' if loops == 0 else loops,
        'quality': quality,
        'output_size': os.path.getsize(output_path),
    }


def resize_pixel_rows(pixel_rows, old_width, old_height, new_width, new_height):
    """
    调整像素行数据大小。
    使用简单居中策略：小图居中放置，大图居中裁剪。
    返回新的像素行列表（每行是整数列表，RGBA 格式）。
    """
    # 先构建完整的二维像素数组
    pixels = []
    for row in pixel_rows:
        row_pixels = [tuple(row[i:i + 4]) for i in range(0, len(row), 4)]
        pixels.append(row_pixels)

    # 计算缩放后的尺寸（保持宽高比）
    scale_w = new_width / old_width
    scale_h = new_height / old_height
    scale = min(scale_w, scale_h)

    scaled_w = int(old_width * scale)
    scaled_h = int(old_height * scale)

    # 如果不需要缩放（目标更大），直接居中放置
    # 如果需要缩放，先缩放再居中
    if scale < 1.0:
        # 下采样
        scaled_pixels = []
        for y in range(scaled_h):
            src_y = int(y / scale)
            src_y = min(src_y, old_height - 1)
            new_row = []
            for x in range(scaled_w):
                src_x = int(x / scale)
                src_x = min(src_x, old_width - 1)
                new_row.append(pixels[src_y][src_x])
            scaled_pixels.append(new_row)
    else:
        scaled_pixels = pixels
        scaled_w = old_width
        scaled_h = old_height

    # 居中放置到目标画布
    offset_x = (new_width - scaled_w) // 2
    offset_y = (new_height - scaled_h) // 2

    # 创建新画布（透明背景）
    transparent = (0, 0, 0, 0)
    new_pixels = []
    for y in range(new_height):
        row = []
        for x in range(new_width):
            sy = y - offset_y
            sx = x - offset_x
            if 0 <= sy < scaled_h and 0 <= sx < scaled_w:
                row.extend(scaled_pixels[sy][sx])
            else:
                row.extend(transparent)
        new_pixels.append(row)

    return new_pixels


def quality_to_compress_level(quality):
    """
    将质量百分比映射到 zlib 压缩级别。
    对于 PNG，压缩是无损的，此参数只影响文件大小和压缩速度。
    """
    quality = max(1, min(100, quality))
    # 质量越高 → 压缩级别越低 → 文件越大
    if quality >= 95:
        return 1
    elif quality >= 90:
        return 3
    elif quality >= 80:
        return 6
    else:
        return 9


def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def main():
    parser = argparse.ArgumentParser(
        description='Convert PNG sequence frames to APNG animation (Pure Python)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python png2apng.py frames.zip output.apng
  python png2apng.py frames.zip output.apng --fps 24 --loops 3 --quality 85
        """
    )
    parser.add_argument('input', help='Input zip file containing PNG frames')
    parser.add_argument('output', help='Output APNG file path')
    parser.add_argument('--fps', type=int, default=15,
                        help='Frames per second, default 15 (recommended: 10-30)')
    parser.add_argument('--loops', type=int, default=0,
                        help='Loop count, 0=infinite, default 0')
    parser.add_argument('--quality', type=int, default=100,
                        help='Compression quality 1-100, default 100 (recommended: 70-100)')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if not args.input.lower().endswith('.zip'):
        print("Error: Input must be a zip file", file=sys.stderr)
        sys.exit(1)

    tmpdir = tempfile.mkdtemp(prefix='png2apng_')
    try:
        print(f"Extracting {args.input}...")
        frames = extract_frames_from_zip(args.input, tmpdir)

        if not frames:
            print("Error: No PNG files found in the zip archive", file=sys.stderr)
            sys.exit(1)

        print(f"Found {len(frames)} PNG frames")
        for i, f in enumerate(frames[:5], 1):
            print(f"  [{i}] {os.path.basename(f)}")
        if len(frames) > 5:
            print(f"  ... and {len(frames) - 5} more")

        print(f"\nGenerating APNG...")
        print(f"  FPS: {args.fps}")
        print(f"  Loops: {'infinite' if args.loops == 0 else args.loops}")
        print(f"  Quality: {args.quality}%")

        result = create_apng(frames, args.output, args.fps, args.loops, args.quality)

        print(f"\nDone! APNG saved to: {args.output}")
        print(f"  Frames: {result['frame_count']}")
        print(f"  Frame duration: {result['duration_ms']} ms")
        print(f"  Total duration: {result['total_duration_s']} s")
        print(f"  File size: {format_size(result['output_size'])}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    main()
